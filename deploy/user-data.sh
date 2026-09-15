#!/bin/bash
# EC2 user-data: installs Docker, checks out the app, writes non-secret config, and
# starts the UI. Real secrets are never written here — see scripts/entrypoint.sh,
# which fetches them from Secrets Manager into the container's process env at
# startup (spec section 8: "Tajemství vyhradne ze Secrets Manageru nebo promennych
# prostredi. Nic v repozitáři.").
#
# TODO(mvp): this is a hand-run bootstrap script (MVP philosophy: "rychle a rucne"),
# not Terraform/CDK. Fine for a single pilot instance; revisit for repeatability if
# this grows beyond one steward group.
set -euxo pipefail

REPO_URL="${REPO_URL:-https://github.com/tomasjanosek/DataStewardSuite.git}"
APP_DIR=/opt/steward-session
AWS_REGION="${AWS_REGION:-eu-central-1}"
BEDROCK_MODEL_ID="${BEDROCK_MODEL_ID:-REPLACE_ME}"
SECRETS_ID="${SECRETS_ID:-steward-session/prod}"

if command -v dnf >/dev/null 2>&1; then
    dnf install -y docker git
elif command -v apt-get >/dev/null 2>&1; then
    apt-get update -y
    apt-get install -y docker.io git
else
    echo "Unsupported distro — install Docker and git manually." >&2
    exit 1
fi

systemctl enable docker
systemctl start docker

DOCKER_CONFIG_DIR=/usr/local/lib/docker/cli-plugins
mkdir -p "$DOCKER_CONFIG_DIR"
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
    -o "$DOCKER_CONFIG_DIR/docker-compose"
chmod +x "$DOCKER_CONFIG_DIR/docker-compose"

if [ ! -d "$APP_DIR/.git" ]; then
    git clone "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"
git pull

mkdir -p vault sessions data/profiles data/docs

# Non-secret config only. AWS_SECRETS_MANAGER_SECRET_ID tells the entrypoint where
# to fetch REDSHIFT_* from at container start — see scripts/entrypoint.sh.
cat > .env <<EOF
LLM_PROVIDER=bedrock
AWS_REGION=${AWS_REGION}
BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID}
VAULT_PATH=./vault
DATA_SOURCE_PROVIDER=redshift
AWS_SECRETS_MANAGER_SECRET_ID=${SECRETS_ID}
CREWAI_TESTING=true
CREWAI_TRACING_ENABLED=false
EOF

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build ui
