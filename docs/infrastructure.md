# Infrastructure

## Services

The baseline stack is intentionally modest:

- FastAPI app for text/audio translation endpoints
- PostgreSQL 16 for source registry, lexicon, jobs, plans, and feedback
- S3-compatible storage for clips, generated drafts, and future video assets
- optional worker or GPU service in a later phase

## Database

Primary migration entrypoint:

```text
infra/db/migrations/001_initial.sql
```

Core tables:

- `source_registry` for datasets, models, frameworks, and license state
- `lexicon_entries` for token/gloss mapping
- `translation_jobs` for input/output job envelopes
- `sign_plan_units` for transparent per-token or per-phrase plans
- `feedback_events` for user/operator evaluation history

## Local Bootstrap

```bash
cp .env.example .env
docker compose up -d postgres minio
python3 -m pip install -e ".[db]"
DATABASE_URL=postgresql://qsign:change-me-local@127.0.0.1:54329/qsign python3 scripts/seed_db.py
```

Default local ports:

- API: `18080`
- Postgres: `54329`
- MinIO API: `19000`
- MinIO console: `19001`

These ports are only defaults. Public deployments can choose different host
ports or service-discovery wiring.

## Production Shape

Recommended deployment shape:

```text
/opt/qsign-translator
  app process or container
  postgres managed volume or external DB
  object storage bucket for clips and generated media
  reverse proxy or ingress for HTTPS
```

Do not put model weights, raw signer videos, or generated media in git. Store
only manifests, metadata, and checksums in the database when possible.

## Security

- No live secrets should exist in the repository.
- `.env.example` contains placeholders only.
- Review endpoints must stay token-protected.
- High-risk domains should remain behind human review.
- Generated outputs should retain source and license provenance.
