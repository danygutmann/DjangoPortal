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
| `BACKEND_TLS_ENABLED` | Enable HTTPS on the internal Gunicorn API listener |
| `BACKEND_TLS_CERT_FILE`, `BACKEND_TLS_KEY_FILE` | Backend TLS certificate and private key paths |
| `BACKEND_TLS_CA_FILE` | CA certificate path trusted by the frontend and backend healthcheck |
| `API_SESSION_MAX_AGE` | Signed API token lifetime in seconds (default 3600) |
| `BACKUP_INTERVAL_SECONDS` | Interval between SQL backups (default 86400) |
| `BACKUP_RETENTION_DAILY` | Recent daily backup window (default 14 days) |
| `BACKUP_RETENTION_WEEKLY` | Older weekly snapshots to keep (default 8) |
| `TZ` | Container timezone; backup timestamps are UTC |
| `LOG_LEVEL` | Python root logging level |

Set `DB_ENGINE=sqlite` only for local development or isolated tests. It is not
the production database configuration.

For production internal API traffic, install a backend certificate/key under
the ignored `tls/` directory and the signing CA certificate under `tls-ca/`.
Set `BACKEND_TLS_ENABLED=1` and `BACKEND_URL=https://backend:8000`; the
certificate must be valid for the Docker service hostname `backend`. Keep
private keys out of source control.

The backend runs as the non-root `app` user. Make the private key readable by
that user/group only (for example mode `0640` with a matching container group),
and make the certificate and CA certificate readable by the service users.
Check the effective container identity with
`docker compose run --rm --no-deps --entrypoint id backend app`; do not make a
private key world-readable to work around mount permissions.
