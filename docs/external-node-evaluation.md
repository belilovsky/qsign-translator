# External Node Evaluation

Last updated: 2026-06-27

## Goal

Identify external GitHub and Hugging Face components that can strengthen QSign
without replacing the current prototype with a research stack that is too heavy
or too weakly validated for our RU/KZ workflow.

## Strong Candidates

### sign-language-translator

- Repository: `sign-language-translator/sign-language-translator`
- Role for QSign: architecture reference and optional adapter target
- Why it matters:
  - already models a text-to-sign pipeline instead of only gesture recognition;
  - has explicit rule-based and lexicon-oriented design;
  - fits our current transparent planner philosophy.

Decision:

- do not hard-swap QSign to this package right now;
- use it as a contract reference for future adapter design and phrase/gloss
  routing.

### Bukva

- Repository: `ai-forever/bukva`
- Role for QSign: dactyl fallback improvement source
- Why it matters:
  - directly relevant to names, terms, and unknown-word fallback;
  - complements our current explicit dactyl path.

Decision:

- keep as the best next-step external source for fallback quality;
- do not wire it in blindly until the local asset and license path are checked.

### Easy Sign

- Repository: `ai-forever/easy_sign`
- Role for QSign: future sign-input or recognition mode
- Why it matters:
  - useful when QSign grows beyond text/audio input;
  - not a direct replacement for our text-to-sign pipeline.

Decision:

- track as a future input-mode node, not a current planner dependency.

## Useful Research References, Not Immediate Product Dependencies

### spoken-to-signed-translation

- Repository: `sign-language-processing/spoken-to-signed-translation`
- Role for QSign: end-to-end pipeline reference for
  `text -> gloss -> pose -> video`

Decision:

- valuable as a design reference;
- too large and language-misaligned to drop into the current production path.

### SLRT / SignAvatars

- Role for QSign: avatar and motion R&D references

Decision:

- keep in the future video-avatar track;
- do not introduce into the current production repo as a live dependency.

## Hugging Face Assessment

### sltAI rule-based corpus

- Dataset family looked promising at first glance, but public metadata and
  validation are too weak for direct production use.

Decision:

- do not import directly into runtime lexicon;
- revisit only if we add a cleaning and license-verification pipeline.

## Product Direction After Review

The safest near-term path is:

1. keep the current QSign planner as the live product core;
2. continue growing the reviewed curated layer in
   `data/curated_overrides.json`;
3. continue importing broad RU coverage from archived Slovo assets;
4. evaluate Bukva next for stronger dactyl and OOV handling;
5. treat avatar/video generation as a separate downstream system, not as proof
   of linguistic quality.
