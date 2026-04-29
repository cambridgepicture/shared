# Cambridge Picture Shared

Shared Flask authentication helpers used by the Cambridge Picture portal and apps.

The package provides session-based user lookup, decorators for portal login and
per-app access checks, and a SQLite-backed user store.

## Local Install

```bash
python -m pip install -e .
```

The default user database path is `/var/www/apps/portal/data/.user_store.sqlite3`.
Set `USER_DB_PATH` to override it in other deployments.
