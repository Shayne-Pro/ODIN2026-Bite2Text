# ODIN 2026 Bite2Text

This repository contains the reproducible code, deployment entry points, and
technical documentation for `shayne`'s individual submission to ODIN 2026
Task 2 (Bite2Text).

The final system combines standardized intraoral-scan geometry, a Point
Transformer V3 structured predictor, multiview photographic evidence, clinical
report retrieval, precision-oriented fact filtering, and contradiction-aware
reranking.

## Repository structure

- `task2_bite2text/ptv3_finetune/`: PTv3 dataset preparation, training, and OOF evaluation.
- `task2_bite2text/photo_pipeline/`: multiview photo training and multimodal evaluation.
- `task2_bite2text/hybrid_submission_v9_final/`: final offline Grand Challenge inference container.
- `task2_bite2text/radfact_glm_eval/`: local RadFact-Lite proxy evaluation adapter.

## Data and model files

Challenge datasets, patient-level records, trained weights, retrieval assets,
Docker exports, and generated experiment artifacts are intentionally excluded.
They must be obtained or regenerated in accordance with the challenge data
license. API credentials are read from environment variables and must never be
committed.

## Upstream projects

- [Bits2Bites](https://github.com/AImageLab-zip/Bits2Bites), pinned in the report at commit `8c3c685160c9cabe2462e9e23d2ffcd9ca78c63a`.
- [IOS-Normalizer](https://github.com/AImageLab-zip/IOS-Normalizer), pinned in the report at commit `ecebe110a15081ea435e5970bbe6cf472d8f2882`.
- [RadFact-Lite](https://github.com/AImageLab-zip/radfact_lite), pinned by the local adapter at commit `053f680be1c57225f94d67b198a34aa871b1127d`.
