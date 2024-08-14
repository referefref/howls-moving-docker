#!/usr/bin/env python3

"""
HowlsMovingDocker (HWD) - A Moving Target Defense Docker Orchestration Platform

Version: 1.0
GitHub: https://github.com/referefref/howls-moving-docker/

This script implements a moving target defense strategy for Docker containers,
including main service management, dummy container creation and recycling,
and log monitoring for potential security breaches.
"""

import yaml
import docker
import random
import time
import requests
import os
import logging
import re
import argparse
from typing import Dict, List, Tuple
import sys

__version__ = "1.0"

def load_config(config_file: str) -> Dict:
    """Load and parse the YAML configuration file."""
    try:
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logging.error(f"Configuration file '{config_file}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file: {e}")
        sys.exit(1)

def download_password_list(url: str, filename: str):
    """Download the password list from the specified URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(filename, 'wb') as file:
            file.write(response.content)
    except requests.RequestException as e:
        logging.error(f"Error downloading password list: {e}")
        sys.exit(1)

def get_random_credentials(password_file: str) -> Tuple[str, str]:
    """Generate random username and password from the password list."""
    try:
        with open(password_file, 'r', errors='ignore') as file:
            passwords = file.readlines()
        return (random.choice(['root', 'admin', 'user']), random.choice(passwords).strip())
    except FileNotFoundError:
        logging.error(f"Password file '{password_file}' not found.")
        sys.exit(1)

def get_random_port(start: int, end: int) -> int:
    """Generate a random port number within the specified range."""
    return random.randint(start, end)

def create_main_containers(client: docker.DockerClient, config: Dict) -> List[docker.models.containers.Container]:
    """Create the main service containers based on the configuration."""
    try:
        network = client.networks.create(config['network_name'], driver="bridge")
        containers = []

        for service in config['main_services']:
            environment = {k: v for k, v in service.get('environment', {}).items()}
            volumes = {
                f"{config['volumes'][volume]}": {'bind': mount_point, 'mode': 'rw'}
                for volume, mount_point in service.get('volumes', {}).items()
            }

            ports = {}
            for port in service.get('ports', []):
                random_port = get_random_port(config['production_port_range']['start'], config['production_port_range']['end'])
                ports[f"{port}/tcp"] = random_port

            container = client.containers.run(
                service['image'],
                name=service['name'],
                ports=ports,
                environment=environment,
                volumes=volumes,
                network=config['network_name'],
                detach=True
            )
            containers.append(container)

        return containers
    except docker.errors.DockerException as e:
        logging.error(f"Error creating main containers: {e}")
        sys.exit(1)

def create_dummy_containers(client: docker.DockerClient, config: Dict, password_file: str) -> List[Tuple[docker.models.containers.Container, Dict]]:
    """Create dummy containers based on the configuration."""
    try:
        dummy_containers = []
        for service in config['dummy_services']:
            for _ in range(random.randint(service['min_instances'], service['max_instances'])):
                port = get_random_port(service['port_range']['start'], service['port_range']['end'])
                username, password = get_random_credentials(password_file)
                
                environment = {k: v.format(username=username, password=password) for k, v in service.get('environment', {}).items()}
                volumes = {
                    f"{config['volumes'][volume]}": {'bind': mount_point, 'mode': 'rw'}
                    for volume, mount_point in service.get('volumes', {}).items()
                }

                container = client.containers.run(
                    service['image'],
                    name=f"{service['name']}_{port}",
                    ports={f"{port}/tcp": port},
                    environment=environment,
                    volumes=volumes,
                    detach=True
                )
                
                container_info = {
                    'username': username,
                    'password': password,
                    'port': port,
                    'log_monitoring': service.get('log_monitoring', {}),
                    'last_check': time.time(),
                    'service_name': service['name']
                }
                
                dummy_containers.append((container, container_info))
        
        return dummy_containers
    except docker.errors.DockerException as e:
        logging.error(f"Error creating dummy containers: {e}")
        sys.exit(1)

def recycle_dummy_containers(client: docker.DockerClient, dummy_containers: List[Tuple[docker.models.containers.Container, Dict]], config: Dict, password_file: str):
    """Stop and remove existing dummy containers, then create new ones."""
    try:
        for container, _ in dummy_containers:
            container.stop()
            container.remove()
        
        return create_dummy_containers(client, config, password_file)
    except docker.errors.DockerException as e:
        logging.error(f"Error recycling dummy containers: {e}")
        return dummy_containers

def update_main_container_ports(client: docker.DockerClient, containers: List[docker.models.containers.Container], config: Dict):
    """Update the ports of main containers to implement moving target defense."""
    try:
        for container in containers:
            service = next(s for s in config['main_services'] if s['name'] == container.name)
            new_ports = {}
            for port in service.get('ports', []):
                random_port = get_random_port(config['production_port_range']['start'], config['production_port_range']['end'])
                new_ports[f"{port}/tcp"] = random_port

            new_container = client.containers.run(
                container.image.tags[0],
                name=f"{container.name}_new",
                ports=new_ports,
                environment=container.attrs['Config']['Env'],
                volumes=container.attrs['Mounts'],
                network=config['network_name'],
                detach=True
            )

            time.sleep(10)  # Wait for the new container to be ready

            container.stop()
            container.remove()

            new_container.rename(container.name)
    except docker.errors.DockerException as e:
        logging.error(f"Error updating main container ports: {e}")

def monitor_log_file(container: docker.models.containers.Container, container_info: Dict, logger: logging.Logger):
    """Monitor the log file of a dummy container for successful login attempts."""
    log_file = container_info['log_monitoring'].get('log_file')
    success_pattern = container_info['log_monitoring'].get('success_pattern')
    
    if not log_file or not success_pattern:
        return  # Skip monitoring if log file or success pattern is not specified

    try:
        exec_result = container.exec_run(f"tail -n +1 {log_file}")
        log_content = exec_result.output.decode('utf-8')
        
        matches = re.finditer(success_pattern, log_content)
        for match in matches:
            logger.warning(f"Successful login detected on dummy container {container.name}")
            logger.warning(f"Service: {container_info['service_name']}, Port: {container_info['port']}, " 
                           f"Username: {match.group(1)}, Source: {match.group(2)}")
        
        container_info['last_check'] = time.time()
    
    except Exception as e:
        logger.error(f"Error monitoring log file for container {container.name}: {str(e)}")

def monitor_dummy_containers(dummy_containers: List[Tuple[docker.models.containers.Container, Dict]], logger: logging.Logger):
    """Periodically check the logs of all dummy containers."""
    current_time = time.time()
    for container, container_info in dummy_containers:
        check_interval = container_info['log_monitoring'].get('check_interval')
        if check_interval and current_time - container_info['last_check'] >= check_interval:
            monitor_log_file(container, container_info, logger)

def main_loop(client: docker.DockerClient, config: Dict, password_file: str, logger: logging.Logger):
    """Main execution loop for the HowlsMovingDocker system."""
    main_containers = create_main_containers(client, config)
    dummy_containers = create_dummy_containers(client, config, password_file)

    production_update_interval = config['production_update_interval'] * 60
    dummy_recycle_interval = config['dummy_recycle_interval'] * 60

    last_production_update = time.time()
    last_dummy_recycle = time.time()

    try:
        while True:
            current_time = time.time()

            if current_time - last_production_update >= production_update_interval:
                update_main_container_ports(client, main_containers, config)
                last_production_update = current_time

            if current_time - last_dummy_recycle >= dummy_recycle_interval:
                dummy_containers = recycle_dummy_containers(client, dummy_containers, config, password_file)
                last_dummy_recycle = current_time

            monitor_dummy_containers(dummy_containers, logger)

            time.sleep(10)  # Check every 10 seconds
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        for container in client.containers.list():
            container.stop()

def setup_logging():
    """Set up logging configuration."""
    logger = logging.getLogger('HowlsMovingDocker')
    logger.setLevel(logging.INFO)
    
    file_handler = logging.FileHandler('howls_moving_docker.log')
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def print_help():
    """Print help information including configuration options."""
    print(f"HowlsMovingDocker (HWD) v{__version__}")
    print("A Moving Target Defense Docker Orchestration Platform")
    print("\nUsage: python hwd.py [config_file]")
    print("\nConfiguration Options:")
    print("  password_list_url: URL to download the password list")
    print("  network_name: Name of the Docker network to create")
    print("  production_port_range: Range of ports for main services")
    print("  production_update_interval: Interval (in minutes) to update main service ports")
    print("  dummy_recycle_interval: Interval (in minutes) to recycle dummy containers")
    print("  main_services: List of main services to deploy")
    print("  dummy_services: List of dummy services to deploy")
    print("    - name: Name of the dummy service")
    print("    - image: Docker image to use")
    print("    - min_instances: Minimum number of instances to create")
    print("    - max_instances: Maximum number of instances to create")
    print("    - port_range: Range of ports for dummy services")
    print("    - environment: Environment variables for the container")
    print("    - volumes: Volume mappings for the container")
    print("    - log_monitoring: Log monitoring configuration")
    print("      - log_file: Path to the log file in the container")
    print("      - success_pattern: Regex pattern to match successful logins")
    print("      - check_interval: Interval (in seconds) to check logs")
    print("  volumes: Volume mappings for all services")

def main():
    """Main entry point for the HowlsMovingDocker system."""
    parser = argparse.ArgumentParser(description="HowlsMovingDocker (HWD) - A Moving Target Defense Docker Orchestration Platform")
    parser.add_argument("config", nargs="?", default="config.yaml", help="Path to the configuration file")
    parser.add_argument("--version", action="version", version=f"HowlsMovingDocker v{__version__}")
    parser.add_argument("--help", action="store_true", help="Show detailed help information")
    args = parser.parse_args()

    if args.help:
        print_help()
        sys.exit(0)

    config = load_config(args.config)
    client = docker.from_env()
    logger = setup_logging()

    # Download password list
    download_password_list(config['password_list_url'], 'password_list.txt')

    try:
        main_loop(client, config, 'password_list.txt', logger)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
