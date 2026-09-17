#!/bin/sh
# If AWS_SECRETS_MANAGER_SECRET_ID is set (production), fetch secrets from Secrets
# Manager and export them before running the real command — nothing sensitive ever
# needs to live in a file on the instance or in the repo (spec section 8). Local dev
# just uses .env via docker-compose's `env_file:` and never sets this variable, so
# this is a no-op there.
set -e

if [ -n "$AWS_SECRETS_MANAGER_SECRET_ID" ]; then
    echo "Fetching secrets from Secrets Manager: $AWS_SECRETS_MANAGER_SECRET_ID" >&2
    eval "$(python /app/scripts/fetch_secrets.py "$AWS_SECRETS_MANAGER_SECRET_ID")"
fi

exec "$@"
