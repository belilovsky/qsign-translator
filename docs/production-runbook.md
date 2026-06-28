# Production Runbook

This document is intentionally public-safe. It describes the deployment shape
and smoke expectations without exposing a specific host, internal paths, or
private operational topology.

## Recommended Shape

- FastAPI application process or container
- PostgreSQL for jobs, plans, feedback, and source registry
- S3-compatible object storage for clips, generated drafts, and future video
  assets
- Reverse proxy or ingress for HTTPS
- Optional background worker for heavier render or ASR tasks

## Required Configuration

Runtime secrets should be injected outside the repository:

- `DATABASE_URL`
- `QSIGN_REVIEW_TOKEN`
- storage credentials if object storage is enabled

Do not commit environment files with live values. Keep secrets in your process
manager, secret store, or host-level environment config.

## Generic Deploy Flow

```bash
./scripts/check.sh
make benchmark
rsync -az --delete \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude 'experiments/mimic_text2video/' \
  --exclude '.env' \
  ./ your-host:/srv/qsign-translator/
ssh your-host 'cd /srv/qsign-translator && docker compose config --quiet'
ssh your-host 'cd /srv/qsign-translator && docker compose up -d postgres minio'
ssh your-host 'cd /srv/qsign-translator && .venv/bin/python -m pip install -e ".[api,db,test]"'
ssh your-host 'cd /srv/qsign-translator && .venv/bin/python scripts/apply_migrations.py'
ssh your-host 'systemctl restart qsign-translator.service'
ssh your-host 'systemctl is-active qsign-translator.service'
```

If you do not use `systemd`, replace the service-management lines with your own
supervisor or container restart flow.

## Smoke

Preferred automated live smoke:

```bash
python3 scripts/smoke_live.py --base-url https://your-public-host.example
```

Convenience wrapper:

```bash
make smoke-live
BASE_URL=https://your-public-host.example make smoke-live
REVIEW_TOKEN='set-from-secure-env' make smoke-live
```

This creates temporary test jobs and checks the public API path from outside
the deploy host. Use the optional `--review-token` flag only from a secure
operator machine.

Verify readiness first:

```bash
BASE=https://your-public-host.example
curl -fsS "$BASE/health"
curl -fsS "$BASE/health/ready"
curl -fsS "$BASE/v1/sources"
curl -fsS "$BASE/v1/lexicon?language=ru"
```

Verify a saved job end to end:

```bash
BASE=https://your-public-host.example
JOB1="$(curl -fsS -X POST "$BASE/v1/translate/text" -H 'content-type: application/json' -d '{"text":"Привет Александр"}' | jq -r '.metadata.job_id')"
JOB2="$(curl -fsS -X POST "$BASE/v1/translate/text" -H 'content-type: application/json' -d '{"text":"Мне нужна помощь"}' | jq -r '.metadata.job_id')"
curl -fsS "$BASE/v1/jobs/$JOB1/render-plan" | jq '.summary, .adapter.adapter_status'
curl -fsSI "$BASE/v1/jobs/$JOB1/review-video" | grep -Ei 'content-type|x-qsign-preview'
curl -fsS "$BASE/v1/jobs/$JOB1/review-video" -o /tmp/qsign-review.mp4 && file /tmp/qsign-review.mp4
curl -fsS "$BASE/v1/jobs/$JOB1/ai-video-brief" | jq '.exports | keys'
curl -fsS -X POST "$BASE/v1/ai-video-batch-brief" -H 'content-type: application/json' \
  -d "{\"job_ids\":[\"$JOB1\",\"$JOB2\"],\"title\":\"Smoke batch\"}" | jq '.format_version, .summary.scene_count, (.exports | keys)'
```

For operator handoff, prefer the explicit `render_contract` or
`operator_runbook` exports over improvising your own scene order or acceptance
criteria.

If `summary.generic_avatar_allowed` is `false`, do not forward the package into
free-form text-to-video sign synthesis. Treat it as a review/operator package
only and resolve signer approval, lexical gaps, or missing assets first.

Verify the review API only with an explicit operator token:

```bash
BASE=https://your-public-host.example
TOKEN='set-me-from-secure-env'
curl -fsS "$BASE/v1/review/jobs" -H "x-qsign-review-token: $TOKEN"
curl -fsS "$BASE/v1/review/audit?job_id=$JOB1" -H "x-qsign-review-token: $TOKEN" | jq '.items | length'
```

Attach a rendered `mp4` back to a saved job:

```bash
BASE=https://your-public-host.example
TOKEN='set-me-from-secure-env'
JOB='job-uuid'
curl -fsS -X POST "$BASE/v1/review/jobs/$JOB/rendered-video" \
  -H "x-qsign-review-token: $TOKEN" \
  -H 'content-type: video/mp4' \
  --data-binary @final-reviewable.mp4
curl -fsSI "$BASE/v1/jobs/$JOB/rendered-video" | grep -Ei 'content-type|x-qsign-render'
curl -fsS -X PATCH "$BASE/v1/review/jobs/$JOB/publish-status" \
  -H "x-qsign-review-token: $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"publish_status":"publishable","note":"final video approved"}' | jq '.publish_status'
```

The recommended reviewer state flow is:

1. translation job is created as `publish_status=draft`;
2. reviewer uploads a final rendered `mp4`;
3. system moves the job to `final_review_pending`;
4. reviewer explicitly marks it as `publishable`, `needs_video_fix`, or
   `rejected`;
5. downstream publishing should only happen from `publishable`.

## Rollback

- Keep your last known-good deploy artifact or git revision outside the app
  tree.
- Restart only the app process first before touching storage services.
- If the app is healthy but video preview is failing, verify `ffmpeg` and the
  preview asset separately before rolling back the full stack.

## Safety Notes

- Do not store raw signer footage or large model weights in git.
- Prefer object storage or mounted volumes for clip libraries and generated
  mp4 files.
- Treat review-video as a draft artifact, not a certified output.
- Keep medical, legal, emergency, and finance scenarios behind human review.
