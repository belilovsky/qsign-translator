# QSign Translator
![Status](https://img.shields.io/badge/status-production-green)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python)
[![CI](https://github.com/belilovsky/qsign-translator/actions/workflows/ci.yml/badge.svg)](https://github.com/belilovsky/qsign-translator/actions)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Прототип планировщика жестового языка (РК/РФ) — создание черновиков
жестовой записи, ревью-воркфлоу и подготовка к видео-рендеру.

Репозиторий намеренно узкий: ядро продукта, ASR и генерация аватаров — за
адаптерами:

```text
audio / video / text
  -> ASR adapter
  -> text normalization
  -> RU/KZ language routing
  -> text-to-gloss / sign plan
  -> reviewable sign plan
  -> video readiness / render manifest
  -> future mp4 / avatar output
```

## Requirements

- Python 3.11 or newer
- Docker Compose for the local Postgres/MinIO stack
- `ffmpeg` only when testing review-video generation

## Repository Policy

This repository is the canonical source of truth for QSign Translator.

- Active local checkout:
  `/Users/belilovsky/Documents/Codex/2026-04-28/qsign-translator`
- Public GitHub repository:
  `https://github.com/belilovsky/qsign-translator`
- Archived pre-public working copy:
  `/Users/belilovsky/Documents/Codex/2026-04-28/qsign-translator-archive`

Day-to-day development should happen only in the active checkout and be pushed
to the public GitHub repository. The archived working copy is kept only as a
historical fallback and should be treated as read-only.

## What This Repository Does

- Source registry for datasets, models, licenses, and readiness.
- Deterministic text-to-sign-plan prototype for Russian and Kazakh text.
- Bundled runtime lexicon now merges a small reviewed seed with an archived
  Slovo-derived Russian gloss list for broader draft coverage.
- Dactyl fallback for unknown words.
- Optional ASR adapter interface; no heavy weights are required for tests.
- Persisted translation jobs and review/feedback API scaffolding.
- Render-plan output that reports whether video fragments exist before any
  player controls are enabled.
- Review-video output that can render a downloadable mp4 of the current draft
  even before a true signer-avatar backend is connected.
- AI-video brief output that packages a provider-ready prompt, negative prompt,
  operator task, and QA checklist for external video generators.

The current public UI is a transparent draft-and-review tool. It does not claim
that an avatar video exists when only a sign plan or dactyl fallback is
available.

## Non-Goals

This repository does not currently promise:

- certified sign-language translation quality
- native-signer validation completion
- production-grade signer-avatar rendering
- safe autonomous use in medical, legal, emergency, or finance settings

## Quick Start

Choose the smallest path that fits what you want to do.

### 1. CLI only

Install the package in editable mode first:

```bash
python3 -m pip install -e ".[test]"
qsign "Привет, меня зовут Александр"
qsign "Сәлеметсіз бе, маған көмек керек"
./scripts/check.sh
```

The CLI prints a JSON sign plan. It does not claim to be a correct
professional interpretation yet; it is a technical spike foundation.

If you prefer not to install the package, the repository also works with
`PYTHONPATH=src`:

```bash
PYTHONPATH=src python3 -m qsign_translator --pretty "Привет, меня зовут Александр"
```

### 2. Browser UI and local API

For the browser UI and API endpoints:

```bash
python3 -m pip install -e ".[api,db,test]"
cp .env.example .env
docker compose up -d postgres minio
uvicorn qsign_translator.api:app --reload
```

Then open the app at `http://127.0.0.1:8000/`.

The public shell includes a separate reviewer route at `/#/review`. It stays
read-only until an operator provides `x-qsign-review-token`, and it should not
claim that saved records, review-video, or AI-video exports exist when a draft
only lives locally in the browser session.

Protected reviewer APIs now also support persisted review sessions, so native
signer or linguist checks can be saved with scores, notes, blocking flags, and
an optional applied `review_status`.

Operators can also attach an externally rendered `mp4` back to a saved job
through the protected review API. This closes the loop between sign-plan
generation, human review, external video rendering, and final publish gating.

The same protected review surface now also exposes a small publication control
contract:

- `GET /v1/review/audit` returns the per-job audit trail;
- `PATCH /v1/review/jobs/{job_id}/publish-status` records the final reviewer
  decision (`draft`, `final_review_pending`, `publishable`,
  `needs_video_fix`, `rejected`).

This keeps the handoff honest: an uploaded final `mp4` does not become
"publishable" automatically. A reviewer still has to mark the saved job as
ready for publication.

API responses follow the same rule: `metadata.output_status=not_rendered`
means the result is a reviewable plan, not a generated video.

When Postgres and `ffmpeg` are available, `GET /v1/jobs/{job_id}/review-video`
returns an honest review mp4 for the saved draft. This is a verification aid,
not a professional sign-language interpretation and not a finished avatar
pipeline.

When a saved job exists, `GET /v1/jobs/{job_id}/ai-video-brief` returns the
handoff package for external AI-video systems. It is designed for operators and
generator prompts, not as proof that the generated result is linguistically
correct without native-signer review. The payload now includes four export
views out of the box: `Universal prompt`, `Operator handoff`, `JSON
payload`, and `Batch storyboard`.

`POST /v1/ai-video-batch-brief` accepts a list of saved `job_ids` and returns
a stricter batch package for multi-phrase rendering: ordered scenes, timeline
offsets, assembly rules, and exports for operator runbooks or downstream
automation.

Single-job AI-video briefs now also include a stricter `render contract`
export: target filename, publish blockers, exact unit order, and acceptance
checks that keep external video generation aligned with reviewer expectations.

Example:

```bash
curl -X POST http://127.0.0.1:8000/v1/ai-video-batch-brief \
  -H 'content-type: application/json' \
  -d '{"job_ids":["job-uuid-1","job-uuid-2"],"title":"Intro sequence"}'
```

### 3. Lightweight API-only smoke

```bash
python3 -m pip install -e ".[api,db]"
uvicorn qsign_translator.api:app --reload
curl -X POST http://127.0.0.1:8000/v1/translate/text \
  -H 'content-type: application/json' \
  -d '{"text":"Привет, меня зовут Александр"}'
```

## Validation

Fast sanity check:

```bash
./scripts/check.sh
```

Live deployment smoke:

```bash
python3 scripts/smoke_live.py --base-url https://qsign.qdev.run
```

The live smoke creates temporary test jobs and verifies health, readiness,
OpenAPI version, translation persistence, render-plan output, review-video
headers, AI-video handoff exports, batch handoff exports, protected review
access, optional audit/publish-state review flows, and invalid job-id handling.

Fresh-clone contributor path:

```bash
python3 -m pip install -e ".[test]"
pytest -q
```

The bundled check script stays dependency-light and covers:

- Python compile checks
- unit and API tests that can run without heavy backends
- scenario smoke for a curated set of user-facing RU phrase cases
- JSON fixture validation
- SQL validation
- RU/KZ CLI smoke

## Local Infrastructure

- Local API default: `http://127.0.0.1:8000/`
- Docker Compose ports are documented in [docs/infrastructure.md](docs/infrastructure.md)
- Initial schema: `infra/db/migrations/001_initial.sql`
- Seed helper: `scripts/seed_db.py`
- Runtime lexicon rebuild: `python3 scripts/build_runtime_lexicon.py`

The runtime lexicon is generated from two layers:

- `data/curated_overrides.json` for reviewed manual phrases, aliases, and KK entries;
- repo-local `data/import_sources/slovo/` assets for wider RU coverage.

This keeps product-approved overrides separate from the larger imported corpus.

## Common Commands

If you prefer shorter commands, the repository also ships with a small
`Makefile`:

```bash
make install
make check
make api
```

## Repository Guide

- [ROADMAP.md](ROADMAP.md): readiness score, phases, and exit criteria
- [CHANGELOG.md](CHANGELOG.md): release-level change summary
- [docs/current-status.md](docs/current-status.md): current prototype scope and known limits
- [docs/architecture.md](docs/architecture.md): system shape and data flow
- [docs/infrastructure.md](docs/infrastructure.md): storage and service layout
- [docs/production-runbook.md](docs/production-runbook.md): generic deploy and smoke flow
- [docs/open-source-readiness.md](docs/open-source-readiness.md): publication checklist
- [docs/repository-policy.md](docs/repository-policy.md): canonical repo and archive policy
- [docs/product-benchmark.md](docs/product-benchmark.md): service benchmark and competitive framing
- [docs/product-backlog.md](docs/product-backlog.md): prioritized next steps
- [docs/source-registry.md](docs/source-registry.md): provenance and licensing inventory

## Contributing

Small, focused pull requests are easiest to review here. Start with
[CONTRIBUTING.md](CONTRIBUTING.md)
for setup, testing, and scope guidance. Repository norms and sensitive-report
handling live in
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
and
[SECURITY.md](SECURITY.md).

## Project Rules

- Do not treat generated signing as authoritative without native signer review.
- Every dataset/model must have license and consent status before production use.
- High-risk domains such as medical, legal, emergency, and finance require human
  interpreter fallback until validated.
- Unknown words must degrade transparently to dactyl/subtitles, not hallucinated
  signs.

## Release Hygiene

Before publishing a public repository, review
[docs/open-source-readiness.md](docs/open-source-readiness.md).
