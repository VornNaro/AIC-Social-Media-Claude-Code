#!/bin/sh
# Apply any pending migrations, then run the given command (uvicorn by default).
set -e
alembic upgrade head
exec "$@"
