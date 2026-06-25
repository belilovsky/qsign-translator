# Native Signer Validation

Automated metrics are not enough for sign-language generation. Every public
release must include review by fluent RSL/KRSL signers.

## Review Packet

For each generated sample, store:

- input audio/text;
- transcript;
- normalized text;
- gloss/sign plan;
- generated video or clip sequence;
- model/backend versions;
- confidence;
- reviewer notes.

## Rating Dimensions

Use a 1-5 scale:

1. Meaning preservation.
2. Sign choice.
3. Word order / grammar.
4. Non-manual markers.
5. Fingerspelling correctness.
6. Timing and transitions.
7. Overall understandability.

## Blocking Cases

Do not publish as supported if reviewers flag:

- wrong meaning in medical/legal/emergency phrases;
- offensive or culturally inappropriate sign;
- hallucinated sign for unknown word;
- missing question/negation marker when meaning depends on it;
- signer likeness or clip used without valid consent.

## Initial Sample Set

- greetings;
- identity/name;
- need help;
- location;
- time/date;
- emergency;
- medical basic needs;
- transport;
- education;
- public service instructions.

