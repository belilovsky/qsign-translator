# Changelog

All notable QSign Translator changes are summarized here.

## 0.2.0 - 2026-06-27

- Added a responsive public UI for transparent draft sign-plan generation.
- Added a protected reviewer route for saved-job review queues.
- Added honest unsaved-draft states for review-video, render-plan, and
  AI-video exports.
- Added render-plan, review-video, single-job AI-video brief, and batch
  AI-video brief endpoints.
- Added token-protected review jobs and review feedback endpoints.
- Added persisted review-session endpoints with scores, notes, blocking flags,
  and optional status application back to saved jobs.
- Added explicit video pipeline blockers and next-step hints to render-plan and
  AI-video handoff payloads.
- Added protected `mp4` upload flow for attaching externally rendered final
  videos back to saved jobs, plus a dedicated served route for uploaded output.
- Added live footer attribution to `qdev.run`.
- Aligned package, FastAPI OpenAPI, and visible UI version metadata.
- Hid `HEAD` monitor routes from OpenAPI to avoid duplicate operation IDs.
- Hardened job endpoints so invalid external IDs return missing-record
  responses instead of database tracebacks.
- Added `scripts/smoke_live.py` for live deployment verification.

## 0.1.0 - Initial public prototype

- Added deterministic RU/KZ text-to-sign-plan core.
- Added dactyl fallback for unknown words.
- Added source registry and sample lexicon fixtures.
- Added optional ASR adapter interface.
- Added Postgres schema for sources, lexicon entries, jobs, plan units, and
  review metadata.
- Added baseline tests and local validation script.
