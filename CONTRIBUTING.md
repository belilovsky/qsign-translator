# Contributing

## Before You Start

This repository is a transparent RU/KZ sign-planning prototype, not a finished
sign-language production system. The best contributions keep that honesty
intact.

Good contribution areas:

- text normalization and phrase planning
- API contract clarity
- review workflow improvements
- test coverage
- documentation cleanup
- public-safe infrastructure guidance

Please avoid opening PRs that market the project as a finished translator or
introduce unverifiable quality claims.

## Local Setup

Use Python 3.11+ for local development.

```bash
python3 -m pip install -e ".[api,db,test]"
cp .env.example .env
docker compose up -d postgres minio
./scripts/check.sh
```

Shortcuts are also available:

```bash
make install-api
make check
make bootstrap-local
```

If you do not need the API stack, the CLI-only path also works:

```bash
python3 -m pip install -e .
qsign "Привет, меня зовут Александр"
```

## Testing

Use the project check script before sending a change:

```bash
./scripts/check.sh
```

That script covers:

- Python compile checks
- unit and API tests
- JSON validation for data fixtures
- SQL validation
- CLI smoke for RU and KZ examples

## Change Style

- Prefer small pull requests with one clear purpose.
- Keep public copy honest about draft status, fallback behavior, and review
  requirements.
- Add tests when changing API behavior, persistence, or output contracts.
- Preserve transparent fallback behavior for unknown words.
- Do not commit live secrets, host-specific config, or private operational
  notes.

## Review Expectations

Please include:

- what changed
- how you tested it
- any remaining risk or limitation

For behavior changes in public API or docs, a short example request/response is
helpful.
