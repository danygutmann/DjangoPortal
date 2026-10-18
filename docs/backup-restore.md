# Backup and restore

The `backup` service creates compressed MariaDB dumps under the persistent
`backup_data` volume at `BACKUP_INTERVAL_SECONDS` intervals. The first dump is
created at service start. It keeps the configured recent daily window and, for
older files, at most one newest snapshot per ISO week up to the weekly limit.
Defaults are 14 days and 8 older weekly snapshots. Check `docker compose logs
backup` and monitor free space and job success.

## Restore

Stop writers first. Copy a chosen backup out of the volume, then restore it to
the target database with a trusted MariaDB client:

```sh
docker compose stop backend frontend
docker compose cp backup:/backups/djangoportal_YYYYMMDD_HHMMSS.sql.gz /tmp/portal.sql.gz
gzip -dc /tmp/portal.sql.gz | docker compose exec -T mariadb sh -c \
  'export MYSQL_PWD="$MARIADB_PASSWORD"; exec mariadb --skip-ssl --user="$MARIADB_USER" "$MARIADB_DATABASE"'
docker compose up -d backend frontend
```

Substitute an existing filename and supply credentials securely; avoid placing
passwords directly in shell history for real systems. Test restoration on an
isolated database before relying on a backup. No automated restore test or
off-host backup replication is included yet.
