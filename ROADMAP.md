# QSign Translator Roadmap

This roadmap describes how QSign should move from a transparent prototype to a
useful, reviewed sign-planning and video-handoff platform.

QSign should remain honest about scope: it can generate reviewable drafts today,
but it must not present itself as a certified sign-language interpreter until
native-signer validation and a production video backend are in place.

## Current Readiness

- Engineering/operator prototype: 99/100.
- Standalone sign-language translation product: not production-ready.

The high engineering score reflects the current API, UI, review route, live
smokeability, and open-source hygiene. The lower real-world translation
readiness reflects missing native-signer validation, limited lexicon coverage,
and no production avatar pipeline.

## Phase 1: Operational Prototype Hardening

Goal: keep the live prototype reliable, measurable, and easy to maintain.

- Maintain green local checks through `./scripts/check.sh`.
- Maintain green live checks through `python3 scripts/smoke_live.py`.
- Keep package, API, UI, and docs versions aligned.
- Keep invalid external identifiers from surfacing database tracebacks.
- Keep review routes token-gated and non-public by default.
- Restore GitHub Actions when maintainer auth is ready.

Exit criteria:

- Local and live smoke checks are green.
- Public docs describe current limits clearly.
- Live API health and readiness are monitored.

## Phase 2: Reviewable Language Quality

Goal: improve the sign-plan itself before investing heavily in final video.

- Expand RU/KZ normalization for names, dates, numbers, addresses, and entities.
- Add phrase-level templates for high-frequency public-service scenarios.
- Track unknown terms and dactyl fallback frequency.
- Build a lexicon coverage report.
- Add native-signer review protocol into the reviewer workflow.
- Persist reviewer corrections as candidate lexicon updates.

Exit criteria:

- Unknown/fallback terms are measurable.
- Reviewed phrases can be separated from unreviewed drafts.
- Native-signer feedback has a durable data shape.

## Phase 3: Reviewer And Admin Operations

Goal: turn the protected reviewer route into a practical operating surface.

- Replace manual token entry with session-based operator login.
- Add roles for admin, reviewer, linguist, and operator.
- Add audit events for review status changes and feedback.
- Add queue filters, search, and saved views.
- Add system status for DB, source registry, lexicon, ASR, and video readiness.

Exit criteria:

- Operators can process review queues without direct API knowledge.
- Admin actions are auditable.
- Secrets are not exposed to browser storage.

## Phase 4: Video Output Pipeline

Goal: make output video generation controlled and reviewable.

- Keep review-video as a transparent storyboard artifact.
- Add clip-based renderer when licensed clips exist.
- Keep AI-video brief exports provider-neutral and batch-safe.
- Add provider-specific adapters only after the generic contract is stable.
- Block public/publish-ready output until human review is complete.

Exit criteria:

- Render readiness is computed from real available assets.
- Batch exports are reproducible.
- Generated video is labeled as draft unless approved by review.

## Phase 5: Evaluation And Public Trust

Goal: measure usefulness instead of relying on demo impressions.

- Build a small public benchmark for RU, KZ, and code-switching.
- Track ASR word error rate separately from sign-planning quality.
- Track meaning preservation, sign choice, grammar, and understandability.
- Publish known limits and domain restrictions.
- Keep high-risk domains behind human interpreter fallback.

Exit criteria:

- Evaluation reports are repeatable.
- Product claims match measured behavior.
- Real-world use cases are scoped by evidence.
