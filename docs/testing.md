# Testing

Install dependencies from `requirements.txt`, then run:

```sh
DB_ENGINE=sqlite python manage.py test
DB_ENGINE=sqlite python manage.py check
docker compose config
```

Tests cover the module registry, bearer login/logout, disabled-module denial,
task creation, object-level UUID isolation, and task change history. SQLite is
only a convenient unit-test database; deployment uses MariaDB. Docker service
healthchecks and persistent volumes should additionally be checked in the
intended deployment environment.
