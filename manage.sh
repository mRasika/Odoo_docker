#!/bin/bash

# Functions
show_help() {
    echo "Odoo Docker Management Script"
    echo "Usage: ./manage.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start Odoo containers"
    echo "  stop        - Stop Odoo containers"
    echo "  restart     - Restart Odoo containers"
    echo "  logs        - Show Odoo logs"
    echo "  ps          - Show container status"
    echo "  backup      - Create database backup"
    echo "  restore     - Restore database from backup"
    echo "  build       - Rebuild containers"
    echo "  help        - Show this help message"
}

# Check if docker is running
docker_check() {
    if ! docker info >/dev/null 2>&1; then
        echo "Error: Docker is not running"
        exit 1
    fi
}

# Main script
docker_check

case "$1" in
    start)
        docker compose up -d
        ;;
    stop)
        docker compose down
        ;;
    restart)
        docker compose restart
        ;;
    logs)
        docker compose logs -f
        ;;
    ps)
        docker compose ps
        ;;
    backup)
        BACKUP_DIR="backups"
        mkdir -p "$BACKUP_DIR"
        BACKUP_FILE="$BACKUP_DIR/odoo_backup_$(date +%Y%m%d_%H%M%S).sql"
        echo "Creating backup: $BACKUP_FILE"
        docker exec odoo_db pg_dump -U odoo postgres > "$BACKUP_FILE"
        echo "Backup completed"
        ;;
    restore)
        if [ -z "$2" ]; then
            echo "Error: Please specify backup file"
            echo "Usage: ./manage.sh restore <backup_file>"
            exit 1
        fi
        echo "Restoring from backup: $2"
        docker exec -i odoo_db psql -U odoo postgres < "$2"
        echo "Restore completed"
        ;;
    build)
        docker compose down
        docker compose build --no-cache
        docker compose up -d
        ;;
    help|*)
        show_help
        ;;
esac
