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

## Platform integration boundary

QSign consumes versioned QazStack contracts in a hybrid-safe state. Canonical
`kk`, `ru`, and `en` routing aliases, source rights metadata, reviewed-activity
evidence, and asset provenance are projected through
`contracts/qsign-platform-integration-v1.json`. These projections contain only
approved identifiers and status metadata.

`QSIGN_QAZCOMPUTE_LANGUAGE_ROUTING_MODE=disabled` is the production-safe
default. `shadow` or `hybrid` may call an explicitly configured HTTPS QazCompute
profile using only aggregate script/count features; QSign still owns language
rules, sign planning, transliteration, dactyl fallback, review, and publication.
The profile is never an ASR, video, gesture, media, or shared-memory endpoint.

`QSIGN_IDENTITY_MODE=documented` leaves the local review token and signed
session controls authoritative. A production OIDC mode may be enabled only
after a provider accepts the exact issuer, audience, redirect/logout URIs,
PKCE/state/nonce flow, deny-by-default reviewer roles, and revoke/logout test.

## Security

- No live secrets should exist in the repository.
- `.env.example` contains placeholders only.
- Review endpoints must stay token-protected.
- High-risk domains should remain behind human review.
- Generated outputs should retain source and license provenance.
- Remote QazCompute routing must remain disabled unless the accepted provider
  endpoint is explicitly configured; remote failure never replaces a local plan.
