# Source Registry

This registry tracks candidate components for a free RU/KZ sign-language
translator. Statuses are conservative:

- `verified`: source exists and was checked directly.
- `needs-license-check`: useful, but production use depends on license/consent.
- `research-only`: useful for papers/architecture, not ready as a dependency.
- `needs-code-check`: paper/project exists, but code/data availability is unclear.

## Core Candidates

| Source | Area | Languages | Status | License Notes | Production Use | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Slovo | RSL dataset/models | RU/RSL | verified, needs-license-check | Public pages state a Creative Commons Attribution-ShareAlike 4.0 variant; exact dataset/model terms still need repository license review | Candidate for dictionary, retrieval, recognition | 20,400 videos, 1,000 classes, 194 signers. Isolated signs only. |
| Easy Sign | RSL recognition app/model | RU/RSL | verified | LICENSE is Creative Commons Attribution-ShareAlike 4.0 | Good spike dependency, with attribution/share-alike obligations | CPU-friendly isolated recognition, ~1,598 gestures according to README. |
| Bukva | RSL dactyl dataset | RU/RSL | verified, needs-license-check | Public pages state a Creative Commons Attribution-ShareAlike 4.0 variant; exact dataset/model terms still need repository license review | Strong OOV fallback source | Dactyl/fingerspelling is essential for names and terms. |
| Logos | RSL pretrain dataset/encoder | RU/RSL | verified, needs-license-check | Repository LICENSE is Apache 2.0; dataset/weights terms still need review | Research and possible encoder backbone | EMNLP 2025; likely important for transfer learning. |
| RuSignBot / mimic_text2video | Text-to-RSL video | RU/RSL | verified, needs-license-check | Code license follows MimicMotion Apache 2.0; SVD/DWPose/MimicMotion weights and Slovo-derived assets need separate checks | Best RSL video-generation spike | Text -> gloss/video retrieval -> MimicMotion avatar video. |
| KRSL20 | KRSL recognition dataset | KRSL | verified, needs-license-check | Academic dataset; verify download terms | Research/reference | 5,200 videos, 20 signs, non-manual markers. |
| FluentSigners-50 | KRSL continuous dataset | KRSL | verified, needs-license-check | Academic/research terms | Research/reference | Useful for signer-independent continuous recognition. |
| KRSL-OnlineSchool | Large KRSL corpus | KRSL | verified, needs-code-check | Dataset availability and license need author check | Strategic data source | Paper reports 890h cleaned video, 325h gloss annotations. |
| sign-language-translator | Framework | Multi | verified | Apache 2.0 | Good architecture dependency | Extensible text/sign framework; no built-in RSL/KRSL production model. |
| faster-whisper | ASR | RU/KZ | verified | MIT | Strong MVP ASR | Self-hosted, can be paired with VAD. |
| ISSAI / Kazakh ASR | ASR | KZ | needs-code-check | Check exact model licenses | Candidate KZ ASR | Test against real Kazakh/code-switching audio. |
| SignLLM | Sign production | Multi | research-only | Check repo/model license | R&D only for now | Promising text/prompt to pose generation, not RU/KZ-ready. |
| SignGen | Sign video generation | Multi | research-only | Check code/weights license | R&D only for now | End-to-end sign video generation candidate. |
| SignAvatars | 3D sign motion dataset | Multi | research-only | Check dataset/model license | R&D only for now | Useful for avatar/motion representation ideas. |

## License Questions To Resolve

1. Can Slovo videos and pretrained weights be used in a free public web service?
2. Can generated videos derived from Slovo/RuSignBot motion be publicly served?
3. What exact consent terms cover signers in Slovo, Bukva, KRSL20, FluentSigners-50,
   and KRSL-OnlineSchool?
4. Are KRSL-OnlineSchool videos and gloss annotations downloadable, or available
   only after author approval?
5. Are Kazakh text-to-KSL gloss parser code and corpus actually open, and under
   which terms?

## Primary URLs Checked

- Slovo: https://github.com/hukenovs/slovo
- Easy Sign: https://github.com/ai-forever/easy_sign
- Bukva: https://github.com/ai-forever/bukva
- Logos: https://github.com/ai-forever/Logos
- RuSignBot / MimicMotion adapter: https://github.com/ds-hub-sochi/mimic_text2video
- sign-language-translator: https://github.com/sign-language-translator/sign-language-translator
- KRSL20: https://krslproject.github.io/krsl20/
- KRSL-OnlineSchool paper: https://aclanthology.org/2022.signlang-1.24.pdf
