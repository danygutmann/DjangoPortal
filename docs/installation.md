# Installation and deployment

## Docker

1. Install Docker Engine with the Compose plugin.
2. Copy `.env.example` to `.env`. Set unique, randomly generated
   `DJANGO_SECRET_KEY`, `FRONTEND_STORAGE_SECRET`, `DB_PASSWORD`, and
   `DB_ROOT_PASSWORD` values. Never commit `.env`.
3. Start the stack with `docker compose up --build -d`.
4. Create an administrator: `docker compose exec backend python manage.py createsuperuser`.
5. Open <http://localhost:8080/>. Django admin/API are on port 8000.

Check `docker compose ps` and service logs with
`docker compose logs --follow backend frontend mariadb backup`. Persistent named
volumes hold MariaDB data and compressed backups.

phpMyAdmin is disabled by default; enable only when needed using
`docker compose --profile tools up -d phpmyadmin`. It binds to loopback.

## Updates

Back up the database first. Pull/build the intended version and run
`docker compose up --build -d`. The backend applies checked-in migrations
before serving requests and synchronizes the validated module metadata.
Review release notes and take a verified backup before upgrading production.

## Deployment considerations

The sample Compose stack publishes the API and frontend ports for local use.
For internet-facing deployments, terminate TLS at a trusted reverse proxy,
restrict API/admin ingress, set `DJANGO_ALLOWED_HOSTS` and
`DJANGO_CSRF_TRUSTED_ORIGINS`, and set `DJANGO_SECURE_COOKIES=1` before
production. The port mappings bind to host loopback by default so a host proxy
can reach them without exposing plain HTTP ports on every interface.
