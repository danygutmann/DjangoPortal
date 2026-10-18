#!/bin/bash
set -eu
umask 077

mkdir -p /backups
interval="${BACKUP_INTERVAL_SECONDS:-86400}"
daily_retention="${BACKUP_RETENTION_DAILY:-14}"
weekly_retention="${BACKUP_RETENTION_WEEKLY:-8}"

while true; do
    stamp="$(date -u +%Y%m%d_%H%M%S)"
    target="/backups/djangoportal_${stamp}.sql.gz"
    if mariadb-dump --host="$DB_HOST" --user="$DB_USER" --single-transaction --routines --triggers "$DB_NAME" | gzip -9 > "$target"; then
        echo "Created backup $target"
    else
        rm -f "$target"
        echo "Backup failed at $stamp" >&2
    fi

    cutoff="$(date -u -d "${daily_retention} days ago" +%Y%m%d)"
    weekly_count=0
    declare -A seen_weeks=()
    while IFS= read -r file; do
        name="${file##*/}"
        file_date="${name#djangoportal_}"
        file_date="${file_date%%_*}"
        if [[ "$file_date" < "$cutoff" ]]; then
            week="$(date -u -d "$file_date" +%G-%V)"
            if [[ -z "${seen_weeks[$week]:-}" && "$weekly_count" -lt "$weekly_retention" ]]; then
                seen_weeks[$week]=1
                weekly_count=$((weekly_count + 1))
            else
                rm -f "$file"
            fi
        fi
    done < <(find /backups -maxdepth 1 -type f -name 'djangoportal_*.sql.gz' -print | sort -r)
    sleep "$interval"
done
