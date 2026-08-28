# QSign Translator: working contract

QSign is a Python/FastAPI prototype for transparent RU/KZ/EN sign-language
draft plans. It is not a certified interpreter. High-risk content requires
human review.

## Start here

- Read `README.md`, `docs/architecture.md`, `docs/infrastructure.md`, and
  `SECURITY.md` before changing behavior or deployment material.
- Install the API/test environment with `make install-api`.
- Run the project gate with `make check`. It compiles the source, runs the
  native tests and smoke checks, validates data files and SQL, and exercises
  the CLI.

## Boundaries

- Keep review tokens, session cookies, media credentials, private jobs, and
  raw signer media out of logs, fixtures, and public files.
- Preserve the distinction between draft plans and reviewed sign-language
  material. Do not weaken the human-review or high-risk-domain safeguards.
- `qdev-project.json` is this repository's QDev/Platform integration input.
  Its QazStack and AVDS entries are deliberately `planned` until a bilateral
  Platform record and an AVDS adapter contract are accepted.
- `config/public-data-agent.profile.json` describes only public read surfaces.
  Do not expose mutation, review, job, upload, token, or session endpoints to
  an AI/data index.

## Delivery

- The local Compose stack uses `.env` values copied from `.env.example`; that
  file sets the API port to 18080.
- Do not commit, push, deploy, or restart remote services unless the owner
  explicitly requests it.
