# Configuration

All configuration is provided through environment variables. `.env.example`
documents the required local values; replace all placeholders before starting.

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Django signing key; keep private and stable across replicas |
| `DJANGO_DEBUG` | Debug mode; keep disabled outside local development |
| `DJANGO_SECURE_COOKIES` | Use secure Django session/CSRF cookies; enable behind HTTPS |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated accepted Host names |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated trusted browser origins |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_ROOT_PASSWORD` | MariaDB database credentials |
| `DB_HOST`, `DB_PORT` | Backend database address |
| `FRONTEND_STORAGE_SECRET` | Independent NiceGUI storage signing secret |
| `BACKEND_URL` | Backend API URL as visible from the frontend container |
| `API_SESSION_MAX_AGE` | Signed API token lifetime in seconds (default 3600) |
| `BACKUP_INTERVAL_SECONDS` | Interval between SQL backups (default 86400) |
| `BACKUP_RETENTION_DAILY` | Recent daily backup window (default 14 days) |
| `BACKUP_RETENTION_WEEKLY` | Older weekly snapshots to keep (default 8) |
| `TZ` | Container timezone; backup timestamps are UTC |
| `LOG_LEVEL` | Python root logging level |

Set `DB_ENGINE=sqlite` only for local development or isolated tests. It is not
the production database configuration.
