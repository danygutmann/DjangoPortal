# DjangoPortal

A modular multi-user application starter built with Django REST Framework and
NiceGUI. Django owns authentication, permissions, data, and business rules;
NiceGUI is a server-rendered client of the backend API.

## Quick start

1. Copy `.env.example` to `.env` and replace every example secret.
2. Start the stack with `docker compose up --build`.
3. Create the first administrator with
   `docker compose exec backend python manage.py createsuperuser`.
4. Visit <http://localhost:8080/>. phpMyAdmin is available only with
   `docker compose --profile tools up` at <http://localhost:8081/>.

The API schema is at `/api/schema/` and interactive API documentation is at
`/api/docs/` on the backend (port 8000). See `docs/` for setup, architecture,
security, module development, tests, operations, and backup/restore guidance.

This is an initial framework implementation. Review the operational and
security limitations documented in `docs/security.md` before production use.
