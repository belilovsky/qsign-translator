#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "bootstrap_local: created .env from .env.example"
fi

docker compose up -d postgres minio
echo "bootstrap_local: postgres and minio requested"
echo "bootstrap_local: run './scripts/check.sh' and then seed with DATABASE_URL from .env"

