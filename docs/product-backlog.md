# Product Backlog

This backlog converts the benchmark into concrete product improvements.

## P0: Production Guardrails

- Add a persistent banner: “AI translation draft, native signer validation
  required.”
- Add high-risk domain detection:
  - medical;
  - legal;
  - emergency;
  - finance.
- For high-risk inputs, return `needs_human_interpreter: true`.
- Store every generated sign plan as a `translation_job`. **Implemented for
  text input when Postgres is configured.**
- Add API response metadata. **Implemented for text input:**
  - source ids;
  - fallback count;
  - unknown token count;
  - review status;
  - output kind/status.
- Keep the video player honest. **Implemented for the public UI:**
  - no playback when no rendered or clip-backed video fragments exist;
  - clear "video cannot be assembled yet" state for dactyl-only plans;
  - render readiness shown separately from the sign plan.

## P1: Core User Workflow

- Audio upload:
  - upload file;
  - run ASR adapter;
  - show editable transcript before sign generation.
- Step-by-step result:
  - transcript;
  - normalized text;
  - gloss plan;
  - video readiness.
- Gloss inspector:
  - click a unit;
  - show source;
  - show confidence;
  - show fallback reason;
  - show “suggest correction”.
- Feedback. **Initial saved-job feedback endpoint and UI implemented:**
  - wrong sign;
  - unclear sign;
  - offensive/inappropriate;
  - missing sign;
  - good translation.
- Review queue. **Initial token-protected API implemented:**
  - reviewer sees input, transcript, gloss, video;
  - scores dimensions from `docs/native-signer-validation.md`;
  - can approve/reject/edit gloss.

## P1: Visual/UI Improvements

- Add editable transcript block between input and gloss plan.
- Add “fallback summary” card:
  - `N слов покрыто`;
  - `N дактиль`;
  - `N неизвестно`.
- Add playback controls:
  - speed 0.5x / 0.75x / 1x;
  - replay current sign;
  - subtitles on/off;
  - disabled until video fragments are available.
- Add source trust panel:
  - `verified`;
  - `license needed`;
  - `access needed`;
  - `reviewed by signer`.
- Add empty states:
  - no audio selected;
  - no video backend;
  - no dictionary match.

## P2: Service Modes

- Public web app mode.
- Website widget/plugin mode.
- API mode for public-service systems.
- Kiosk mode for PSC/hospitals/transport desks.
- Learning mode:
  - sign-by-sign playback;
  - dictionary;
  - saved phrases.

## P2: Data And Model Quality

- Build 100 validated public-service phrases for RU.
- Build 100 validated public-service phrases for KZ/KRSL.
- Add bilingual/code-switch test set.
- Add ASR benchmark set:
  - clean speech;
  - noisy room;
  - phone audio;
  - code-switching.
- Add native signer review pack generation.
- Add corpus coverage dashboard.

## P3: Advanced Output

- Clip retrieval assembly.
- RuSignBot/MimicMotion RSL video spike.
- Avatar backend adapter.
- Generated video cache.
- Per-sign timing alignment.
- Non-manual marker representation.

## Metrics

- ASR WER by language and environment.
- Gloss coverage.
- Fallback rate.
- Native signer understandability score.
- High-risk refusal/gating rate.
- Time to first result.
- User correction rate.
- Repeat/replay rate.
