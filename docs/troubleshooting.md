# Troubleshooting

- **Backend cannot connect to MariaDB:** wait for the database healthcheck;
  verify `DB_NAME`, `DB_USER`, `DB_PASSWORD` and inspect
  `docker compose logs mariadb backend`.
- **Frontend cannot reach API:** verify backend health and `BACKEND_URL` is the
  internal service address `http://backend:8000`.
- **Login rejected:** confirm the account is active and its password is correct.
  Login attempts are rate limited.
- **Module or task API returns 403:** verify module enabled state in Django
  admin and grant the appropriate module/task permission through a group.
- **No task rows visible:** users see tasks they created or are assigned unless
  granted `view_all_tasks`; ensure `view_task` and `access_task_manager` are
  also granted.
- **Frontend refuses to start:** set a non-placeholder
  `FRONTEND_STORAGE_SECRET`; set a long random `DJANGO_SECRET_KEY` as well.
- **Backups absent:** inspect the backup service logs, MariaDB connectivity,
  credentials, interval, and persistent volume permissions/capacity.
