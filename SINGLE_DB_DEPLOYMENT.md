# Odoo Single Database Deployment: Problem & Solution Documentation

## Problem Summary

When deploying Odoo with Docker and Cloudflare Tunnel, the platform always redirected to the database selector page, even though the configuration was set to use a single database (`erp`). This prevented direct access to the intended Odoo instance and caused issues with document sharing and portal links.

### Key Issues
- Odoo always showed the database selector instead of loading the `erp` database directly.
- Document links (e.g., quotations, invoices) did not work as expected.
- The login page sometimes loaded without styles (CSS) due to misconfiguration.

## Root Causes
1. **Odoo Configuration Not Mounted:**
   - The custom `odoo.conf` file (with correct `dbfilter` and database credentials) was not mounted into the container, so Odoo used its default config.
2. **Incorrect dbfilter Setting:**
   - The `dbfilter` was not set to an exact match (`^erp$`), so Odoo could not auto-select the correct database.
3. **Cloudflare/Proxy Host Header:**
   - (Not the root cause in this case, but often a problem) If the Host header is not forwarded correctly, dbfilter will not match.

## Solution Steps
1. **Mount the Correct odoo.conf:**
   - Updated `docker-compose.yml` to mount `./config/odoo.conf` into `/etc/odoo/odoo.conf` in the Odoo container.
2. **Set dbfilter for Exact Match:**
   - Set `dbfilter = ^erp$` in `odoo.conf` to match only the `erp` database.
3. **Set list_db = False:**
   - Added `list_db = False` to hide the database selector page.
4. **Restarted Odoo Container:**
   - Fully recreated the Odoo container to ensure the new config was used.
5. **Verified Database Name:**
   - Confirmed the database is named exactly `erp` (all lowercase).
6. **Checked Static Files & Base URL:**
   - Ensured `web.base.url` matches the public domain and static files load correctly.

## Result
- Odoo now loads the `erp` database directly at `https://erp.theremarked.com` without showing the database selector.
- Document and portal links work as expected.
- The login page and static files load correctly in all browsers.

## Next Steps
- To enable multi-database support with subdomains, update `dbfilter` to `^%d$` and ensure each subdomain matches a database name.

---

# Commit Message Suggestion

```
fix: ensure single-db Odoo deployment auto-selects 'erp' database

- Mount custom odoo.conf into container
- Set dbfilter to ^erp$ for exact match
- Hide database selector with list_db = False
- Add debug logging for troubleshooting
- Documented problem and solution
```
