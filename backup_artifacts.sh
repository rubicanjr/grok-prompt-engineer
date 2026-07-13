#!/bin/bash
# Automatic backup script for artifacts/ folder - Kural 0 compliant
BACKUP_DIR="/home/workdir/artifacts/backups"
SOURCE_DIR="/home/workdir/artifacts"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/artifacts_backup_$DATE.tar.gz" "$SOURCE_DIR"/*.md "$SOURCE_DIR"/*.sh 2>/dev/null || true
echo "[$(date)] Backup created: artifacts_backup_$DATE.tar.gz" >> /tmp/artifacts_backup.log
ls -t "$BACKUP_DIR"/artifacts_backup_*.tar.gz | tail -n +11 | xargs -r rm -f
echo "[$(date)] Old backups cleaned. Current count: $(ls "$BACKUP_DIR"/artifacts_backup_*.tar.gz 2>/dev/null | wc -l)"
