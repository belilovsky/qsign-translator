# Architecture

## Layers

```text
Input adapters
  - text
  - audio
  - video with speech

ASR adapters
  - faster-whisper for general RU/KZ/EN
  - Kazakh-specialized model after benchmark
  - Vosk/NeMo only when streaming constraints require it

Language and normalization
  - route RU/KZ/EN/mixed
  - simplify text
  - preserve named entities

Sign planning
  - phrase lookup
  - token lookup
  - LLM/rule glossifier later
  - dactyl/subtitle fallback
  - confidence and warnings

Reviewable output
  - persisted translation job
  - ordered sign units
  - trace and decision reasons
  - human review status

Video backends
  - render-plan manifest
  - clip retrieval and ffmpeg concat
  - RuSignBot/MimicMotion experiment for RSL
  - KRSL retrieval/pose experiment after source access
  - future avatar/video model adapter

Delivery
  - REST API
  - web widget
  - batch mp4 generation
```

## Why This Shape

ASR and video generation are fast-moving model layers. The durable product asset
is the validated sign-planning layer: gloss vocabulary, fallback policy,
confidence, review workflow, and domain-specific phrase coverage.

## Adapter Contract

Every backend should return transparent intermediate data:

- transcript;
- detected language;
- normalized text;
- gloss/sign units;
- fallback units;
- confidence;
- source/license metadata;
- warnings.
- output kind/status.
- render readiness.

No generated video should be served without the corresponding sign plan.

The web player must stay disabled while `output_status=not_rendered` and the
render plan has no resolved video fragments. A dactyl-only plan is useful for
review, but it is not a video preview.
