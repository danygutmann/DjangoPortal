# Architecture

Django is the authority for user identity, permissions, persistent data, and
business rules. NiceGUI is a separate server-rendered client; its server calls
the versioned Django API over the Docker network. Browser-supplied usernames
are never treated as identity.

`core` contains API sessions, the deployed-module registry, user permission
inspection, and API authentication. Each installed module owns its models,
services, serializers, API routes, manifest, administration, and tests.
`task_manager` is the first reference module. Modules are explicitly listed in
`MODULE_MANIFESTS`; a YAML manifest cannot install or execute code.

The deployment consists of NiceGUI (`frontend`), Django/Gunicorn (`backend`),
MariaDB, scheduled SQL backups, and optional local-only phpMyAdmin. Only the
backend connects to the database. UUIDs are used for module and task object IDs.
Modules can be administratively disabled without deleting their records.

## Important implementation boundaries

- The task module uses shared services for API writes and permission checks.
- Django groups and model permissions are managed through Django admin.
- Authentication between frontend and backend uses short-lived, revocable
  signed bearer tokens held in NiceGUI server-side user storage.
- The initial frontend provides login, task list/search/status filtering, task
  creation, and sign-out. It is a starter UI rather than the full theme and
  preference system described in the roadmap.
- A future module needs a registered manifest and deployment-time inclusion in
  `MODULE_MANIFESTS` and `INSTALLED_APPS`; arbitrary runtime code installation
  is intentionally unsupported.
