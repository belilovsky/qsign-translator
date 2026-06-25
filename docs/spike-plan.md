# Technical Spike Plan

## Week 1: Local Proof

1. Run the deterministic sign-plan CLI on RU/KZ text.
2. Add a small curated lexicon of 100 public-service words.
3. Benchmark `faster-whisper` on 10 RU, 10 KZ, and 10 code-switching samples.
4. Clone and run `mimic_text2video` in a separate experiment folder.
5. Verify Slovo/Bukva/Easy Sign licenses from repository files, not summaries.

Success criteria:

- Text -> sign-plan is deterministic and test-covered.
- Unknown words degrade to dactyl/subtitle.
- ASR output can feed the planner.
- One local video backend path is selected for the next iteration.

## Week 2: Retrieval Demo

1. Build a `clip_id -> mp4` local dictionary.
2. Generate ffmpeg concat files from sign plans.
3. Produce 5 RU demo videos and 3 KZ/KRSL placeholder demos.
4. Extend the FastAPI wrapper:
   - `POST /v1/translate/text` - present in the scaffold;
   - `POST /v1/translate/audio` - next after ASR benchmark;
   - `GET /v1/jobs/{id}` - next after async video generation exists.
5. Add native signer review workflow document.

Success criteria:

- End-to-end text -> gloss -> clip plan -> mp4 works for a small phrase set.
- Every output contains transcript, gloss, confidence, and warnings.

## Month 2-3: Research MVP

1. Add validated RSL/KRSL phrasebook and domain tags.
2. Evaluate LLM-assisted gloss generation against native signer references.
3. Spike RuSignBot/MimicMotion for RSL avatar generation.
4. Contact KRSL dataset authors for access and license terms.
5. Define production data governance and consent forms.
