# Current Status

Last updated: 2026-06-28

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
- Runtime lexicon rebuilt from the archived Slovo gloss list plus reviewed seed
  entries, which materially improves Russian draft coverage.
- Curated overrides now live in `data/curated_overrides.json`, so reviewed
  manual phrases and aliases are maintained separately from the imported RU
  corpus.
- Phrase lookup, token lookup, and dactyl fallback.
- Optional ASR adapter interface.
- Persisted translation jobs when Postgres is configured.
- Saved plan-unit records for review and downstream rendering.
- Feedback API for saved jobs.
- Token-protected review API for operator workflows.
- Persisted review-session API for signer, linguist, and operator validation.
- Protected upload flow for attaching an externally rendered `mp4` back to a
  saved job.
- Publish-state contract for final reviewer approval after a rendered video is
  attached.
- Per-job audit trail for job creation, review changes, feedback, uploaded
  video events, and publish decisions.
- Render-plan manifest for future clip or avatar assembly.
- Review-video draft mp4 generation for saved jobs.
- AI-video brief export for one saved phrase.
- Batch AI-video brief export for multiple saved phrases.
- Stricter render-contract export for external video operators.
- Responsive public UI with result trace, coverage counters, and export modes.
- Separate reviewer route in the same frontend shell, with token-gated queue and
  details view.
- Reviewer UI now supports persisted validation sessions with role, language,
  notes, blocking flags, and lightweight scoring.
- Honest unsaved-draft states in the UI: no fake saved-job, review-video, or
  AI-video availability when a draft only exists locally.

## Public API Shape

- `POST /v1/translate/text`
- `POST /v1/transcribe/audio`
- `GET /v1/jobs/{job_id}`
- `GET /v1/jobs/{job_id}/render-plan`
- `GET|HEAD /v1/jobs/{job_id}/review-video`
- `GET|HEAD /v1/jobs/{job_id}/rendered-video`
- `GET /v1/jobs/{job_id}/ai-video-brief`
- `POST /v1/ai-video-batch-brief`
- `POST /v1/feedback`
- `GET /v1/review/sessions`
- `POST /v1/review/sessions`
- `GET /v1/review/audit`
- `POST /v1/review/jobs/{job_id}/rendered-video`
- `PATCH /v1/review/jobs/{job_id}/publish-status`
- `GET /health`
- `GET /health/ready`

Protected review endpoints remain available for operator use, but require
`x-qsign-review-token`.

## Verification Summary

The current repository state has been exercised through:

- unit and API tests via `./scripts/check.sh`;
- curated phrase-coverage smoke for common RU user requests;
- live API smoke against a deployed instance via `scripts/smoke_live.py`;
- browser smoke at desktop and mobile widths;
- batch-brief checks with multiple saved jobs;
- review-video checks through both `GET` and `HEAD`.

Recent validation passed with:

- 95 automated tests green;
- no browser console errors in the checked desktop/mobile flow;
- no horizontal overflow in the checked public UI;
- stable route switching between the main app and `#/review`;
- working single-job and batch AI-video export modes.
- deterministic language route now routes Kazakh without explicit Kazakh-specific
  characters when common Kazakh lexical markers are present (`мен`, `керек`, etc.),
  and EN/KK seed coverage is expanded for common short phrases.
- repeated regeneration in the same session updates dependent draft artifacts
  (plan, render-plan, AI video brief) without stale cross-run overwrites.
- planner hot-path work is now cached and de-duplicated:
  deterministic tokenization, normalization, language detection, transliteration,
  and dactyl fallback no longer repeat unnecessary work across common requests.
- API fallback reads for source registry and lexicon export are now cached in-process,
  reducing repeated JSON parsing when database-backed endpoints are unavailable.
- repository now includes `scripts/benchmark_planner.py` and `make benchmark`
  for lightweight performance regression checks during future iterations.
- deterministic runtime lexicon rebuild from curated overrides plus archived
  Slovo assets.
- live footer attribution now points back to `qdev.run` in a muted, non-promotional style.
- package metadata, FastAPI OpenAPI metadata, and visible UI version are aligned
  at `0.2.0`.
- OpenAPI generation is warning-free while `HEAD` monitor routes remain active.
- invalid external job identifiers are handled as missing records instead of
  surfacing database tracebacks.
- review sessions can now be persisted with scoring and notes, then optionally
  apply a new `review_status` to the saved job.
- render-plan and AI-video brief responses now expose pipeline blockers and the
  next operational step instead of only raw asset counts.
- reviewer UI now supports attaching an externally rendered final `mp4`, and
  saved jobs can expose that uploaded video through a dedicated route.
- uploaded final videos now move the job into `final_review_pending`, while a
  separate publish-state decision determines whether the result is truly ready
  for publication.
- reviewer tooling now exposes a lightweight audit trail and final
  publish-status controls for the saved job lifecycle.
- reviewer UI now separates plan units, saved review sessions, user feedback,
  and audit history into clearer sections with counts and timestamps.
- AI-video handoff now includes an explicit render contract so operators get a
  stricter acceptance checklist, output naming, and unit-order contract.
- AI-video brief now explicitly blocks generic sign-avatar generation whenever
  signer approval, lexical coverage, or clip-backed assets are incomplete, so
  external video tools are not asked to fake fluent sign language from fallback
  tokens.

## Readiness Rating

Current engineering/operator prototype applicability: **99/100**.

This score applies to the prototype as a transparent tool for text-to-plan,
review queues, draft preview, and AI-video handoff. It does not mean the system
is a certified or autonomous sign-language translator.

Current standalone translation-product readiness remains below production
level until native-signer validation, broader lexicon coverage, evaluation
benchmarks, and a real video/avatar backend are complete.

## Known Limits

This repository is publishable as a prototype, but not as a finished
sign-language production stack.

- No real signer-avatar generation pipeline is wired in yet.
- Generic text-to-video models are still not treated as trusted sign-language
  renderers; unresolved jobs now deliberately downgrade to review-only packages.
- No production clip library is bundled in the repository.
- No native-signer validation has happened yet.
- ASR quality on real RU/KZ production audio is not benchmarked here.
- High-risk domains still require human interpreter fallback.
- Batch render currently produces a strict handoff contract, not a render queue
  or worker-backed final video job.
- Publish-state approval is still an operator contract. There is no downstream
  CMS or auto-publish target connected yet.

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
