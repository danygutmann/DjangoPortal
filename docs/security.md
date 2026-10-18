# Security

- Django's default password validators and authentication backend are used;
  guest access is not provided.
- REST endpoints require an authenticated, signed API session unless explicitly
  marked public. Login is throttled. Tokens expire and logout revokes the
  server-side session.
- Task visibility is scoped to the creator and assignee unless the user has the
  explicit all-task or module-administration permission. API writes call the
  same domain services used by other backend callers.
- User/group permissions are administered by trusted Django administrators;
  ordinary users have no endpoint to grant themselves permissions.
- Frontend bearer tokens remain in NiceGUI server-side user storage. Passwords
  are sent to the backend over the internal service network and are not logged.
- Module discovery only reads deployed, configured YAML manifests with
  `safe_load`; it does not install or import arbitrary module code.
- Database data and backup files use persistent Docker volumes. Secrets must
  be supplied out-of-band, not committed to source.

## Production hardening required

The Compose example is a development-oriented deployment baseline, not a
complete hardened perimeter. Put it behind TLS, do not expose the Django port
or phpMyAdmin publicly, restrict admin access, set secure cookie and proxy
settings (`DJANGO_SECURE_COOKIES=1`) for the actual topology, rotate secrets with a planned process, and
monitor backup success. API tokens are bearer credentials: protect frontend
traffic with TLS and treat the NiceGUI storage secret as sensitive. OIDC,
external rate limiting, audit retention policies, and a production reverse
proxy are not implemented.
