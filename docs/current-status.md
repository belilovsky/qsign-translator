# Current Status

Last updated: 2026-06-27

## Scope

Repository source of truth:

- active repo: `/Users/belilovsky/Documents/Codex/2026-04-28/qsign-translator`
- public GitHub: `https://github.com/belilovsky/qsign-translator`
- archived fallback copy:
  `/Users/belilovsky/Documents/Codex/2026-04-28/qsign-translator-archive`

QSign Translator is currently a transparent RU/KZ sign-planning prototype. It
accepts short text, optionally accepts audio for ASR when the dependency is
installed, produces a reviewable sign plan, and exposes a public-safe API
contract for later video generation.

The project is intentionally honest about what exists today:

- text and phrase planning work;
- unknown words degrade to dactyl or visible fallback states;
- review-video is a lightweight draft preview, not a finished signer-avatar
  backend;
- AI-video export endpoints produce structured handoff packages, not verified
  linguistic output.

## Implemented

- Deterministic RU/KZ text-to-sign-plan prototype.
- Phrase lookup, token lookup, and dactyl fallback.
- Optional ASR adapter interface.
- Persisted translation jobs when Postgres is configured.
- Saved plan-unit records for review and downstream rendering.
- Feedback API for saved jobs.
- Token-protected review API for operator workflows.
- Render-plan manifest for future clip or avatar assembly.
- Review-video draft mp4 generation for saved jobs.
- AI-video brief export for one saved phrase.
- Batch AI-video brief export for multiple saved phrases.
- Responsive public UI with result trace, coverage counters, and export modes.
- Separate reviewer route in the same frontend shell, with token-gated queue and
  details view.
- Honest unsaved-draft states in the UI: no fake saved-job, review-video, or
  AI-video availability when a draft only exists locally.

## Public API Shape

- `POST /v1/translate/text`
- `POST /v1/transcribe/audio`
- `GET /v1/jobs/{job_id}`
- `GET /v1/jobs/{job_id}/render-plan`
- `GET|HEAD /v1/jobs/{job_id}/review-video`
- `GET /v1/jobs/{job_id}/ai-video-brief`
- `POST /v1/ai-video-batch-brief`
- `POST /v1/feedback`
- `GET /health`
- `GET /health/ready`

Protected review endpoints remain available for operator use, but require
`x-qsign-review-token`.

## Verification Summary

The current repository state has been exercised through:

- unit and API tests via `./scripts/check.sh`;
- live API smoke against a deployed instance;
- browser smoke at desktop and mobile widths;
- batch-brief checks with multiple saved jobs;
- review-video checks through both `GET` and `HEAD`.

Recent validation passed with:

- 47 automated tests green;
- no browser console errors in the checked desktop/mobile flow;
- no horizontal overflow in the checked public UI;
- stable route switching between the main app and `#/review`;
- working single-job and batch AI-video export modes.
- live footer attribution now points back to `qdev.run` in a muted, non-promotional style.

## Known Limits

This repository is publishable as a prototype, but not as a finished
sign-language production stack.

- No real signer-avatar generation pipeline is wired in yet.
- No production clip library is bundled in the repository.
- No native-signer validation has happened yet.
- ASR quality on real RU/KZ production audio is not benchmarked here.
- High-risk domains still require human interpreter fallback.
- Batch render currently produces a strict handoff contract, not a render queue
  or worker-backed final video job.

## Open-Source Notes

The repository is structured so that secrets stay out of git:

- `.env.example` contains placeholders only;
- local MCP config is ignored;
- deployment-specific details should live outside the public repository;
- object storage, review tokens, and database credentials are expected to be
  injected at deploy time.

The main remaining open-source tasks are maintainer decisions outside the code:
final public contact points, asset redistribution checks, and the eventual
restoration of the GitHub Actions workflow with proper maintainer auth.
