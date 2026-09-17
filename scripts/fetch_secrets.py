#!/usr/bin/env python
"""Fetches a Secrets Manager secret (a flat JSON object) and prints shell `export`
statements for each key — for scripts/entrypoint.sh to `eval`.

Spec section 8: "Tajemství vyhradne ze Secrets Manageru nebo promennych prostredi.
Nic v repozitáři." This is the Secrets Manager half — nothing here is ever written
to disk or logged.
"""

from __future__ import annotations

import json
import os
import shlex
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: fetch_secrets.py <secret-id>", file=sys.stderr)
        raise SystemExit(2)

    import boto3

    secret_id = sys.argv[1]
    region = os.environ.get("AWS_REGION", "eu-central-1")
    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId=secret_id)
    secret = json.loads(response["SecretString"])

    for key, value in secret.items():
        print(f"export {key}={shlex.quote(str(value))}")


if __name__ == "__main__":
    main()
