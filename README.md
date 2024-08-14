# HowlsMovingDocker (HMD)

Version: 1.0

HowlsMovingDocker is a moving target defense Docker orchestration platform that creates a dynamic environment for your main application and dummy services. It continuously changes the network topology to enhance security and resilience against potential attacks.

## Features

- Deploys main application services with dynamically changing ports
- Creates multiple dummy instances with weak credentials
- Periodically recycles dummy instances, changing their ports and credentials
- Monitors authentication logs in dummy containers to detect successful login attempts
- Highly configurable through YAML files
- Uses volume mapping for data persistence

## Requirements

- Python 3.7+
- Docker

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/referefref/howls-moving-docker.git
   cd howls-moving-docker
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Ensure Docker is installed and running on your system.

## Usage

Run the main script with your chosen configuration file:

```
python hmd.py config_wordpress.yaml
```

For help and to see all available options:

```
python hmd.py --help
```

To check the version:

```
python hmd.py --version
```

## Configuration

Edit the YAML configuration file to customize the behavior of HowlsMovingDocker. Key configuration options include:

- `password_list_url`: URL to download the password list for dummy services
- `network_name`: Name of the Docker network to create
- `production_port_range`: Range of ports for main services
- `production_update_interval`: Interval (in minutes) to update main service ports
- `dummy_recycle_interval`: Interval (in minutes) to recycle dummy containers
- `main_services`: List of main services to deploy
- `dummy_services`: List of dummy services to deploy, including log monitoring settings
- `volumes`: Volume mappings for all services

See the example configuration files in the `config_examples` directory for more details.

## Log Monitoring

HMD can monitor logs of dummy services for successful login attempts. Configure the `log_monitoring` section for each dummy service in the configuration file:

```yaml
log_monitoring:
  log_file: /path/to/log/file
  success_pattern: "regex pattern to match successful logins"
  check_interval: 30  # seconds
```

If log monitoring is not applicable for a service, set these fields to `null`.

## Warning

While this project implements moving target defense strategies, it is primarily for educational and development purposes. Ensure proper security measures are in place before considering any production use.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
