# Odoo Multi-Database Deployment: Problem & Solution Documentation

## Feature Overview

This setup enables Odoo to serve multiple databases, each mapped to a different subdomain. For example:
- `erp.theremarked.com` → database: `erp`
- `saloon.theremarked.com` → database: `saloon`

## How It Works
- The `dbfilter = ^%d$` setting in `odoo.conf` ensures that the subdomain part of the URL is matched exactly to a database name.
- When a user visits `https://saloon.theremarked.com`, Odoo will automatically use the `saloon` database.
- The database selector (`list_db = false`) is hidden for security, so users cannot see or select other databases.

## Configuration Steps
1. **Database Naming:**
   - Create a database for each subdomain you want to use. The database name must match the subdomain (e.g., `saloon`).
2. **DNS/Subdomain Setup:**
   - Point each subdomain (e.g., `saloon.theremarked.com`) to your Odoo server or Cloudflare Tunnel.
3. **Odoo Configuration:**
   - In `config/odoo.conf`:
     ```ini
     dbfilter = ^%d$
     list_db = false
     ```
   - Restart the Odoo container after making changes.
4. **Security:**
   - With `list_db = false`, only the database matching the subdomain is accessible.
   - Users cannot see or access other databases via the web interface.

## Example odoo.conf
```ini
[options]
db_host = db
db_port = 5432
db_user = odoo
db_password = myodoopass
addons_path = /mnt/extra-addons
dbfilter = ^%d$
list_db = false
log_level = debug
```

## Troubleshooting
- If you only see one database or the selector, check your subdomain and database name match exactly.
- For admin/maintenance, set `dbfilter = .*` and `list_db = true` to see all databases.
- Ensure your DNS and proxy/tunnel forward the correct Host header.

## Commit Message Suggestion
```
feat: enable Odoo multi-database deployment with subdomain-based dbfilter

- Set dbfilter to ^%d$ for subdomain-to-database mapping
- Hide database selector for security
- Documented multi-database setup and troubleshooting
```
