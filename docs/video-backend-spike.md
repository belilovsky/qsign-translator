# Video Backend Spike

## Candidate: RuSignBot / mimic_text2video

Repository:

```text
https://github.com/ds-hub-sochi/mimic_text2video
branch: feature/refactoring
```

Local checkout:

```text
experiments/mimic_text2video
```

The checkout is intentionally ignored by git.

## Observed Files

The repository already includes useful Slovo-derived matching assets:

- `misc/gloss_words_SLOVO.txt` - 941 lines, 940 unique gloss words after
  normalization;
- `misc/gloss_embeddings_SLOVO.npy`;
- `misc/annotations_cleared_19.06.2023_SLOVO.csv` - 20,401 lines;
- `inference_text2video.py`;
- `tg_bot.py`;
- `configs/test_mimic.yaml`.

Local sizes:

- `misc/`: about 3.1 MB;
- full checkout: about 124 MB, excluding additional downloaded weights.

## Required Heavy Assets

The README requires:

- Stable Video Diffusion `stabilityai/stable-video-diffusion-img2vid-xt-1-1`;
- DWPose pretrained models;
- MimicMotion checkpoint;
- `mimic_weigths.zip` from Google Drive;
- Slovo video dataset for actual inference.

This means full text-to-video generation is a GPU/heavy-asset task, not a
lightweight repository test.

## Immediate Use

Before downloading all video/model assets, we can reuse the smaller matching
materials for a controlled text-to-gloss lookup spike:

1. Load `gloss_words_SLOVO.txt`.
2. Compare our seed lexicon coverage.
3. Use existing embeddings later for semantic fallback.
4. Keep generated sign plans separate from video generation.

Initial inspection result:

- seed RU direct overlap with Slovo gloss words: `привет`;
- the next useful step is semantic/lemma mapping, not only exact token matching.
