# Research Synthesis

## Decision

Do not build the full chain from scratch. Treat ASR and video/avatar generation
as replaceable adapters. Build and own the middle layer:

```text
spoken/written RU/KZ
  -> normalized text
  -> gloss/sign plan
  -> confidence and fallback policy
  -> video backend adapter
```

## Practical Starting Point

Russian Sign Language should be the first technical spike because the available
components are denser:

- Slovo for isolated signs and pretrained baselines.
- Bukva for dactyl fallback.
- Easy Sign for practical recognition reference.
- RuSignBot/mimic_text2video for text-to-video generation experiments.
- Logos as a possible newer encoder/pretraining base.

Kazakh/KRSL should run in parallel as a research and partnership track:

- Verify KRSL-OnlineSchool access and license.
- Verify FluentSigners-50 and KRSL20 data terms.
- Find actual code/data for Kazakh text-to-KSL gloss parser claims.
- Start with a small manually validated emergency/public-service phrasebook.

## MVP Principle

The first public demo should prefer correctness transparency over visual
impressiveness:

- Show transcript.
- Show gloss/sign plan.
- Show confidence.
- Show fallback decisions.
- Render clips/avatar only when the mapped sign is known.
- Always keep subtitles visible.

## Red Lines

- No medical/legal/emergency authoritative use without human interpreter review.
- No hidden hallucinated gestures for unknown words.
- No use of signer likenesses without license and consent confirmation.
- No claim of "Kazakh sign language support" until native KRSL review passes.

