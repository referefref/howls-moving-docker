# HowlsMovingDocker

HowlsMovingDocker is a moving target defense Docker orchestration platform that creates a dynamic environment for your main application and dummy services. It continuously changes the network topology to enhance security and resilience against potential attacks.

## Features

- Deploys a main application with its required services (e.g., WordPress with MariaDB, GitLab)
- Creates multiple dummy instances with weak credentials
- Periodically recycles dummy instances, changing their ports and credentials
- Dynamically updates ports for production services to create a moving target
- Implements load balancing to ensure no downtime during port changes
- Highly configurable through YAML files
- Uses volume mapping for data persistence

## Requirements

- Python 3.7+
- Docker

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/HowlsMovingDocker.git
   cd HowlsMovingDocker
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Ensure Docker is installed and running on your system.

## Configuration

Edit the YAML configuration file to customize the behavior of HowlsMovingDocker. You can configure:

- Password list URL
- Main services (e.g., WordPress, GitLab)
- Dummy services (e.g., MariaDB, PostgreSQL)
- Production port range and update interval
- Number of dummy instances, port ranges, and recycle intervals
- Volume mappings

Example configurations are provided for WordPress (`config_wordpress.yaml`) and GitLab (`config_gitlab.yaml`).

## Usage

Run the main script with your chosen configuration file:

```
python howls_moving_docker.py config_wordpress.yaml
```

or

```
python howls_moving_docker.py config_gitlab.yaml
```

This will:
1. Download the specified password list
2. Create the main application containers with random ports
3. Create the specified number of dummy instances
4. Periodically recycle the dummy instances
5. Regularly update the ports of the main application containers

To stop the script, use Ctrl+C. This will gracefully shut down all containers.

## Moving Target Defense

HowlsMovingDocker implements a moving target defense strategy by:

1. Randomly assigning ports to the main application containers within a specified range
2. Periodically updating these ports to new random values
3. Implementing a hot-swap mechanism to ensure no downtime during port changes
4. Creating and recycling dummy instances to add noise and confusion for potential attackers

This approach makes it more difficult for attackers to maintain a consistent understanding of the network topology and target specific services.

## Extending for Other Applications

To use HowlsMovingDocker with other applications:

1. Create a new YAML configuration file based on the provided examples.
2. Define the main services for your application, including image, ports, environment variables, and volumes.
3. Define the dummy services you want to create, such as databases or caching services.
4. Adjust the volume mappings as needed for your application.
5. Configure the production port range and update interval to suit your needs.

Examples of other applications you could implement:

- Joomla with MySQL
- Drupal with PostgreSQL
- Node.js application with MongoDB
- Ruby on Rails application with Redis and PostgreSQL

## Warning

While this project implements moving target defense strategies, it is primarily for educational and development purposes. Ensure proper security measures are in place before considering any production use.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
