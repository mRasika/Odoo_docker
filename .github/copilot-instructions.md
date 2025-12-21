# Odoo Docker Setup – Copilot Instructions

These notes highlight the concrete structure and workflows that an AI agent should follow to stay productive in this repository.

## 1. Big Picture Architecture
- The entire stack is defined in [docker-compose.yml](docker-compose.yml#L1-L84): the `odoo` app server, the `db` Postgres backend, and the `odoo_backup` dumper sidecar live on the `odoo-net` bridge network with the `odoo-data`/`db-data` volumes.
- The Odoo image is a lightweight extension of `odoo:18.0` (see [Dockerfile](Dockerfile#L1-L17)) that installs `python3-pip` before pulling every dependency from [requirements.txt](requirements.txt#L1-L12).
- Custom code is surfaced via the bind mount defined at [docker-compose.yml#L15-L18](docker-compose.yml#L15-L18) and the `addons_path` setting in [config/odoo.conf](config/odoo.conf#L1-L10); add new folders in [addons/](addons/) so they appear inside `/mnt/extra-addons`.

## 2. Critical Workflows
### 2.1 Bootstrapping the stack
- Follow the quick-start steps documented in [README.md#L22-L44](README.md#L22-L44): clone, write `secrets/postgresql_password.txt`, and run `docker compose up -d` so that every container joins `odoo-net` and the backup volume [backups/odoo-db](backups/odoo-db) is initialized.
### 2.2 Refreshing Python dependencies
- When a new Python requirement is needed (many modules such as the auto-database-backup plugin rely on `dropbox`, `boto3`, `paramiko`, etc. from [requirements.txt](requirements.txt#L1-L12)), add it there, then stop the stack, rebuild with `docker compose build --no-cache`, and bring the services up again as described in [README.md#L52-L62](README.md#L52-L62).
### 2.3 Adding or updating custom modules
- Populate [addons/](addons/) with module folders (existing entries include `salon_management`, `auto_database_backup`, etc.) and make sure their manifests, Python files, and data always align with the folders mounted via [docker-compose.yml#L15-L18](docker-compose.yml#L15-L18). After a deploy, install/upgrade through Odoo's UI or CLI as explained in [README.md#L97-L100](README.md#L97-L100).
### 2.4 Backups and observability
- The Postgres dumper (`odoo_sql_dumper`) runs `prodrigestivill/postgres-backup-local` and writes compressed SQL blobs to [backups/odoo-db](backups/odoo-db) every day; its env flags such as `SCHEDULE=@daily` and `BACKUP_KEEP_DAYS=7` are in [docker-compose.yml#L50-L70](docker-compose.yml#L50-L70). Keep that directory synced with any external backup client (Duplicati, Restic, etc.).
- Manual backups and log inspection are covered in [README.md#L77-L95](README.md#L77-L95); use `docker exec odoo_db pg_dump ...` before pushing data changes and `docker logs odoo_app`/`docker logs odoo_db` when investigating problems.
### 2.5 Secrets & runtime configuration
- Credentials flow through Docker secrets: [docker-compose.yml#L18-L26](docker-compose.yml#L18-L26) and the secret definition at [docker-compose.yml#L78-L81](docker-compose.yml#L78-L81) load `secrets/postgresql_password.txt` (current placeholder accessible at [secrets/postgresql_password.txt#L1-L1](secrets/postgresql_password.txt#L1-L1)).
- `config/odoo.conf` defines `db_host`, `db_port`, `db_user`, the default `addons_path`, `dbfilter`, `list_db`, and `log_level`. Adjust `dbfilter` there or by un-commenting the `ODOO_DBFILTER` env in `docker-compose.yml` when you need to hide unused databases ([config/odoo.conf#L1-L10](config/odoo.conf#L1-L10), [docker-compose.yml#L7-L24](docker-compose.yml#L7-L24)).

## 3. Conventions & Integration Points
- The stack always runs `odoo --proxy-mode` (see [docker-compose.yml#L7-L18](docker-compose.yml#L7-L18)). If you need to prevent the database chooser from appearing, re-enable `--no-database-list` and the escaped `ODOO_DBFILTER=^%d$$` line right above it.
- Custom automation modules (e.g., [addons/auto_database_backup](addons/auto_database_backup)) rely on extra dependencies listed under the TODO comment in [requirements.txt#L7-L12](requirements.txt#L7-L12); keep those in sync when editing manifests.
- The Postgres healthcheck in [docker-compose.yml#L43-L48](docker-compose.yml#L43-L48) gates the `odoo` service and the dumper, so fix any `pg_isready` failures with `docker compose ps` as outlined in [README.md#L101-L109](README.md#L101-L109).
- Use the documented volumes odoo-data, db-data, [addons/](addons/), and [backups/odoo-db](backups/odoo-db) from [README.md#L63-L74](README.md#L63-L74) to understand where state lives and what needs to be preserved when containers are replaced.

If any part of these instructions seems unclear or misses an important workflow, let me know so we can iterate on the guidance.
