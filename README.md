# Odoo Docker Setup with Custom Dependencies

This repository contains a dockerized setup for Odoo 18.0 with PostgreSQL, including custom Python dependencies management.

## Directory Structure
```
odoo/
├── addons/              # Custom Odoo modules
├── config/              # Odoo configuration files
├── secrets/             # Secret files (passwords)
│   └── postgresql_password.txt
├── docker-compose.yml   # Docker compose configuration
├── Dockerfile          # Custom Odoo image definition
└── requirements.txt    # Python dependencies
```

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. Clone this repository:
```bash
git clone <repository-url>
cd odoo
```

2. Create a password file:
```bash
mkdir -p secrets
echo "your_secure_password" > secrets/postgresql_password.txt
```

3. Start the containers:
```bash
docker compose up -d
```

4. Access Odoo:
- Web Interface: http://localhost:8069
- Default login credentials will be created on first startup

## Configuration

### Docker Compose
The setup includes two main services:
- `odoo`: Odoo application server
- `db`: PostgreSQL database

### Custom Dependencies
Python dependencies are managed through `requirements.txt`. To add new dependencies:

1. Add them to `requirements.txt`
2. Rebuild the containers:
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Volumes
- `odoo-data`: Odoo data files
- `db-data`: PostgreSQL data
- `./addons`: Custom Odoo modules

### Networks
- `odoo-net`: Internal network for Odoo and PostgreSQL communication

### Security
- Database passwords are managed through Docker secrets
- Passwords are stored in `secrets/postgresql_password.txt`

## Maintenance

### Backup
To backup your data:
```bash
# Backup PostgreSQL database
docker exec odoo_db pg_dump -U odoo postgres > backup.sql

# Backup Odoo filestore
docker cp odoo_app:/var/lib/odoo ./odoo_backup
```

### Logs
View logs:
```bash
# Odoo logs
docker logs odoo_app

# PostgreSQL logs
docker logs odoo_db
```

### Adding Custom Modules
1. Place your custom modules in the `addons/` directory
2. Install them through Odoo's web interface or update the configuration

### Automation helpers
- `addons/sl_salon_management/scripts/booking_ui_automation.py` mimics the backend booking form, approves the draft, and asserts an order links back to the booking so you can exercise the overlap/approval path without manual clicks.
- Run it from inside the Odoo container to execute the flow: `docker compose exec -T odoo python3 /mnt/extra-addons/sl_salon_management/scripts/booking_ui_automation.py`.

## Common Issues and Solutions

### Database Connection Issues
If you experience database connection issues:
1. Verify the password in `secrets/postgresql_password.txt`
2. Check if both containers are running:
```bash
docker compose ps
```

### Python Dependencies
If you need to install additional Python packages:
1. Add them to `requirements.txt`
2. Rebuild the container as described above

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
