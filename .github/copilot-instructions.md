# Odoo Docker Setup - Copilot Instructions

This document provides essential guidelines for AI coding agents to effectively navigate and contribute to this Odoo 18.0 Dockerized project.

## 1. Big Picture Architecture

The project utilizes a Docker-based architecture with two primary services:
- **`odoo`**: The Odoo application server, built from a custom `Dockerfile` that includes Python dependencies defined in `requirements.txt`.
- **`db`**: A PostgreSQL database server, linked to Odoo.

These services communicate over an internal Docker network (`odoo-net`). Data persistence is achieved through Docker volumes (`odoo-data` for Odoo and `db-data` for PostgreSQL).

**Key Files:**
- `docker-compose.yml`: Defines the Odoo and PostgreSQL services, their networks, and volumes.
- `Dockerfile`: Specifies how the Odoo application image is built, including custom Python dependencies.
- `requirements.txt`: Lists Python packages required by the Odoo application.

## 2. Critical Developer Workflows

### 2.1. Initial Setup
To get the project running locally:
1.  **Clone the repository.**
2.  **Create a PostgreSQL password file**: `echo "your_secure_password" > secrets/postgresql_password.txt`
3.  **Start containers**: `docker compose up -d`

### 2.2. Adding/Updating Python Dependencies
When new Python libraries are required:
1.  Add the dependency to `requirements.txt`.
2.  Rebuild the Odoo service to include the new dependency:
    ```bash
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    ```

### 2.3. Managing Custom Odoo Modules
Custom Odoo modules should be placed in the `addons/` directory. These are automatically mounted into the Odoo container.
To install or update modules, use the Odoo web interface or update the Odoo configuration.

### 2.4. Database Operations
-   **Backup PostgreSQL**: `docker exec odoo_db pg_dump -U odoo postgres > backup.sql`
-   **Backup Odoo Filestore**: `docker cp odoo_app:/var/lib/odoo ./odoo_backup`

### 2.5. Viewing Logs
-   **Odoo Application Logs**: `docker logs odoo_app`
-   **PostgreSQL Database Logs**: `docker logs odoo_db`

## 3. Project-Specific Conventions

-   **Secrets Management**: Database passwords are handled via Docker secrets, specifically using `secrets/postgresql_password.txt`. Avoid hardcoding credentials directly in configuration files.
-   **Module Placement**: All custom Odoo modules reside in the `addons/` directory, which is a bind mount.
-   **Odoo Version**: The project is set up for Odoo 18.0. Ensure compatibility when adding modules or making changes.

## 4. Integration Points & External Dependencies

-   **PostgreSQL**: The primary database, accessed by Odoo via the `db` service.
-   **Docker Hub**: Odoo base images and other dependencies are pulled from Docker Hub during the build process.

By adhering to these instructions, AI coding agents can efficiently understand, modify, and extend the functionality of this Odoo Docker setup.
