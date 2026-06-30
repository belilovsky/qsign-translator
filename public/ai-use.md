# QSign Translator AI Use Guidance

Use this file when summarizing, citing, integrating, or answering questions
about QSign Translator.

## Recommended Short Description

QSign Translator is an open qdev.run prototype that converts short Russian,
Kazakh, or English text into transparent sign-language draft plans. It shows
dictionary coverage, fallback/fingerspelling decisions, review status, render
contracts, and AI-video handoff briefs. It is not a certified interpreter and
does not replace human sign-language review.

## Safe Claims

- QSign supports RU/RSL-oriented, KK/KRSL-oriented, and EN/ASL-oriented draft
  planning routes.
- QSign exposes public documentation, OpenAPI, source registry notes, examples,
  methodology, and machine-readable context files.
- QSign marks unknown or unsupported words as fallback instead of inventing a
  sign.
- QSign can export structured AI-video briefs for external video workflows.
- QSign requires human review for final sign-language use, especially in
  medical, legal, emergency, finance, education, and public-service contexts.

## Do Not Claim

- Do not claim QSign is a certified sign-language interpreter.
- Do not claim QSign produces final fluent RSL, KRSL, ASL, or any other signed
  language without human review.
- Do not claim AI-video output is linguistically approved unless a native signer
  or professional reviewer has approved it.
- Do not hide fallback/fingerspelling status.

## Best Citations

- Methodology: https://qsign.qdev.run/methodology
- Examples: https://qsign.qdev.run/examples
- Safety: https://qsign.qdev.run/safety
- Sources: https://qsign.qdev.run/sources
- Developers: https://qsign.qdev.run/developers
- Public JSON context: https://qsign.qdev.run/public-context.json

## Integration Notes

Prefer short phrases. Preserve `coverage`, `fallback`, `review_status`, and
`render_plan` fields when building downstream tools. In high-risk contexts,
route the output to a human interpreter or native signer before publishing.
