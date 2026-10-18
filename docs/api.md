# API

All application endpoints use `/api/v1/`. The OpenAPI schema is at
`/api/schema/`; Swagger UI is at `/api/docs/`. API endpoints require a bearer
token except for login and health.

1. `POST /api/v1/auth/login/` with `username` and `password` returns a
   time-limited signed token.
2. Send it as a bearer token in the authorization header.
3. `POST /api/v1/auth/logout/` revokes that token.

Available endpoints include `GET /api/v1/me/permissions/`,
`GET /api/v1/modules/`, and standard list/create/retrieve/update/delete
operations on `/api/v1/tasks/`. List filters include `search`, `status`,
`priority`, `due_before`, `due_after`, `assigned_to_me=true`, and
`scope=mine|all`. A task also has `/comments/` and `/history/` subresources.
Disabled modules reject their API calls. Permission and
object-visibility checks are enforced by the backend, not the frontend.

The schema and documentation are informational; the API's authentication
requirements remain in force.
