# Product Benchmark

Last updated: 2026-06-20

This benchmark tracks real products, research prototypes, and user needs that
should shape QSign Translator.

## Summary

The strongest comparable products do not present automatic sign translation as a
magic black box. They expose a controlled workflow: input, text/transcript,
gloss or selected signs, avatar/video output, speed controls, visible confidence,
and a clear boundary between automated translation and human interpretation.

For QSign, this means the product should stay transparent:

- transcript is always visible;
- sign plan is always visible;
- every fallback is visible;
- sources/license status are visible;
- native signer review is a first-class product workflow;
- high-risk domains are gated until validated.

## Benchmarked Services

| Service | What It Does Well | Product Pattern To Borrow | Caution |
| --- | --- | --- | --- |
| Hand Talk | Text/audio to sign-language avatar; free app; website plugin; friendly avatar; learning mode; adjustable signing speed reported by third-party reviews. | Clear avatar output, speed control, dictionary/learning surface, embeddable widget idea. | ASL/BSL/Libras focus, not RU/KZ; quality must be validated per sign language. |
| Signapse | Enterprise text/content to ASL/BSL with AI video selection and blending; clear process: library, selection, blending, integration. | Explain the pipeline in-product; source library selection + blending/assembly stage; enterprise integration mode. | Commercial/closed; claims need independent validation. |
| SignON | Community-driven EU sign/spoken translation project. | Community governance and multilingual design from day one. | Research/project ecosystem, not a plug-and-play RU/KZ service. |
| SignAll | Automatic sign-language translation with Gallaudet partnership history. | Partnership with Deaf institutions as credibility and validation layer. | Hardware/camera sign-to-text is harder than text-to-sign; avoid overpromising. |
| Silence Speaks | Text-to-BSL/ASL avatars; developed with Deaf community; focuses on dialect, context, emotional tone; transport/workplace/education use cases. | Community-built positioning, contextual tone, deployment in public-service contexts. | News/product claims; exact technical stack and quality are not public. |
| Sign-Speak / AI avatar discussions | Represents growing AI avatar category and community skepticism. | Add trust, consent, and “human interpreter needed” boundaries directly in UI. | Deaf community reactions can be strongly negative when AI is framed as replacing humans. |
| Ava / Rogervoice / captioning apps | Speech-to-text accessibility, live captions, calls, workplace conversations. | ASR transcript should remain useful even when sign output is incomplete. | Captioning is not sign translation; text may not be accessible to all Deaf signers. |

## User Needs Observed Across Research And Communities

### Communication

- A Deaf user may need sign-first output, not only captions.
- A hearing user may need help communicating in a sign language they do not know.
- A public-service employee needs short, validated phrases more than unrestricted
  free-form generation.
- A family/education setting needs slow playback and repeatable learning mode.

### Trust

- Users need to know when the output is machine-generated.
- Users need confidence and fallback visibility.
- Users need to know when human interpretation is required.
- Users need source and validation provenance, especially for medical, legal,
  emergency, transport, and finance scenarios.

### Control

- Playback speed.
- Pause/replay sign units.
- Show/hide subtitles.
- Switch between avatar, clips, gloss plan, and transcript.
- Inspect a single sign and its source.
- Replace a fallback with a reviewed sign later.

### Accessibility

- Large touch targets.
- Keyboard navigation.
- Captions always visible.
- Adjustable playback speed.
- High contrast mode.
- Plain-language transcript.
- Mobile-first flow for field/public-service contexts.

### Community And Ethics

- Do not frame the product as replacing signers/interpreters.
- Involve native RSL/KRSL signers early.
- Treat signers' video/likeness as consent-sensitive data.
- Avoid “fixing deafness” framing; present it as access and communication
  infrastructure.

## Feature Gap Against Benchmarks

| Capability | Current QSign | Benchmark Expectation | Priority |
| --- | --- | --- | --- |
| Text input | Present | Present | Done |
| Audio upload | Visual placeholder | Working ASR upload | P1 |
| Transcript | Visual/plan only | Always visible and editable | P1 |
| Gloss/sign plan | Present | Inspectable per sign | P1 |
| Avatar/video output | Placeholder | Playback with speed/replay | P1 |
| Source registry | Present | Source + license + validation surfaced | P1 |
| Native review workflow | Documented | In-app review queue | P1 |
| User feedback | Missing | “Wrong sign / unclear / offensive” feedback | P1 |
| High-risk domain gates | Documented | Enforced in UI/API | P1 |
| Embeddable widget | Missing | Website/plugin mode | P2 |
| Learning mode | Missing | Dictionary/sign-by-sign learning | P2 |
| Speed control | Static | Adjustable 0.5x/0.75x/1x | P2 |
| RU/KZ/EN code-switching | Planned | Explicit route + transcript confidence | P2 |
| Offline/low bandwidth | Missing | Cache/reuse generated clips | P3 |

## Product Principles For QSign

1. **Transparent before impressive**: show transcript, gloss, confidence, and
   fallback before showing a polished video.
2. **Validated domains first**: start with public-service, education, transport,
   and basic assistance phrases.
3. **No silent hallucinations**: unknown words become dactyl/subtitle, not an
   invented sign.
4. **Community-centered**: native signers review outputs and can correct the
   lexicon.
5. **Replaceable engines**: ASR, video generation, and avatar models are adapters;
   the sign-plan layer is the core asset.

## Sources

- Hand Talk app and plugin: https://www.handtalk.me/en
- Hand Talk Google Play listing: https://play.google.com/store/apps/details?id=br.com.handtalk
- Hand Talk App Store listing: https://apps.apple.com/us/app/hand-talk-learn-sign-language/id659816995
- Signapse: https://signapse.ai/
- SignON project: https://signon-project.eu/
- Gallaudet and SignAll partnership: https://gallaudet.edu/interpretation-and-translation/gallaudet-partners-with-signall-to-develop-automatic-sign-language-translation-software/
- ACM survey on Deaf community perspectives on ASLT: https://dl.acm.org/doi/fullHtml/10.1145/3597638.3614507
- Arm overview of sign-language translation systems: https://developer.arm.com/community/arm-community-blogs/b/ai-blog/posts/sign-language-translation-using-machine-learning
- Wired on Silence Speaks: https://www.wired.com/story/silence-speaks-deaf-ai-signing/
- Sorenson app overview for Deaf users: https://sorenson.com/blog/vrs/the-best-apps-for-deaf-people-in-2025/
