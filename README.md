# ODIN 2026 Bite2Text

Reproducible source code and deployment entry points for `shayne`'s individual
submission to [ODIN 2026 Task 2 — Bite2Text](https://odin2026.grand-challenge.org/).
The method was developed by **Yan Sun**.

The final v9 system combines standardized intraoral-scan geometry, a Point
Transformer V3 (PTv3) structured predictor, multiview photographic evidence,
clinical-report retrieval, precision-oriented fact filtering, and conservative
contradiction-risk reranking.

- Grand Challenge method: [Bite2text Report](https://grand-challenge.org/algorithms/qwen3-vl-photo-orthodontic-report/)
- Final v9 evaluation: [3fac9821-fc34-45c4-bb1b-df4b912e28f7](https://odin2026.grand-challenge.org/evaluation/3fac9821-fc34-45c4-bb1b-df4b912e28f7/)
- Exact submitted algorithm source: [`0d0d83e`](https://github.com/Shayne-Pro/ODIN2026-Bite2Text/tree/0d0d83e1a962f361bc3b70e4d36ae129d338708b)

## Method overview

![Fact-constrained multimodal retrieval pipeline](figures/ODIN2026_Task2_Technical_Route.svg)

The editable source is available in
[`ODIN2026_Task2_Technical_Route.drawio`](figures/ODIN2026_Task2_Technical_Route.drawio).

## Final v9 configuration

| Component | Frozen setting |
|---|---:|
| Geometry retrieval | 3,720-D descriptor, cosine top-50 |
| PTv3 evidence | 12 heads, agreement coefficient `0.5` |
| Photo evidence | five views, 8 supported heads, coefficient `0.2` |
| Midline correction | confidence threshold `0.45` |
| Candidate score margin for risk reranking | `0.02` |
| Contradiction confidence threshold | `0.65` |
| Unsupported-sentence penalty | `0.005` |
| Contradiction-risk penalty | `0.5` |
| Minimum contradiction improvement | `0.015` |

On strict patient-separated five-fold out-of-fold evaluation over 867 labeled
cases, v9 obtained BLEU-4 `0.2684` and METEOR `0.4700`. These are development
results, not organizer-reported hidden-test RadFact scores.

## Repository structure

- `task2_bite2text/ptv3_finetune/`: PTv3 data preparation, training, and OOF evaluation.
- `task2_bite2text/photo_pipeline/`: multiview-photo training and multimodal evaluation.
- `task2_bite2text/hybrid_submission_v9_final/`: final Grand Challenge inference layer.
- `task2_bite2text/labeling/`: structured-label parser and schema.
- `task2_bite2text/radfact_glm_eval/`: local RadFact-Lite proxy adapter.
- `scripts/`: input auditing, IOS-normalization QA, and local smoke-test utilities.
- `report/`: five-page LNCS technical-report source.

Older submission directories are retained to document the progression from
geometry-only retrieval to the final multimodal, fact-constrained system.

## Technical report

The five-page LNCS source is
[`report/ODIN2026_Task2_shayne_TechnicalReport.tex`](report/ODIN2026_Task2_shayne_TechnicalReport.tex).
With [Tectonic](https://tectonic-typesetting.github.io/) installed, rebuild it
from the official LNCS class with:

```bash
mkdir -p output/pdf
cd report
tectonic --outdir ../output/pdf ODIN2026_Task2_shayne_TechnicalReport.tex
```

The PDF output is intentionally ignored until the organizer publishes the
final v9 RadFact-F1 and Final Score. Update the two not-released table cells
before submitting the final PDF.

## Reproducibility scope

This repository intentionally excludes challenge data, patient-level records,
clinical-report banks, trained weights, Docker exports, and generated
experiment artifacts. Consequently, cloning the repository is sufficient to
inspect and test the source, but **not** to reproduce the exact submitted image
without separately authorized model and data assets.

The excluded v9 model directory must contain:

```text
model/
├── config.py
├── head_vocabs.json
├── model_final.pth
├── photo_model_final.pt
├── photo_view_classifier.pt
├── retrieval_index.npz
├── retrieval_labels.json
└── retrieval_reports.json
```

The retrieval reports and labels are derived from challenge training data and
must be regenerated or obtained under the applicable challenge license. The
full-data PTv3 checkpoint used for the submitted model has SHA-256
`d7f3be80fadc361248b970a85861660ad527d7cf5e82232e563fb1fe363c6811`.

## Source-level validation

The final decision controls require only Python and NumPy at source-test time:

```bash
python3 -m venv .venv-tests
.venv-tests/bin/python -m pip install --requirement requirements-test.txt
cd task2_bite2text/hybrid_submission_v9_final
../../.venv-tests/bin/python -m unittest -v \
  test_report_sanitizer.py test_risk_rerank.py
```

Expected result: 11 tests pass. These tests cover the high-precision sentence
filter and the conservative v9 candidate-replacement gate; they do not require
challenge data, model weights, CUDA, or PyTorch. The same command runs in
GitHub Actions for every pull request.

## Container assembly

Requirements:

- Linux/amd64 Docker with Buildx;
- NVIDIA Container Toolkit and a CUDA-capable GPU for end-to-end inference;
- at least 16 GB host memory for the validated runtime profile;
- Git and network access while fetching the two pinned upstream repositories;
- the eight model assets listed above.

Prepare the excluded upstream build context and build the complete
PTv3-v3 -> hybrid-v5 -> final-v9 image chain with:

```bash
./scripts/build_v9_image.sh
```

`bootstrap_upstreams.sh` clones Bits2Bites and IOS-Normalizer at the pinned
commits below, applies the two checked-in Bits2Bites compatibility patches, and
copies only the required source into the ignored Docker build context. This
avoids redistributing IOS-Normalizer while making the image-layer build order
repeatable. Set `BITE2TEXT_VENDOR_ROOT` to keep the upstream clones elsewhere.

For a local end-to-end test, place one case under the official input layout and
mount the model assets through the supplied script:

```bash
export BITE2TEXT_TEST_INPUT_ROOT=/path/to/test/input
export BITE2TEXT_TEST_CASE=CASE_ID
export BITE2TEXT_TEST_GPU=0
./do_test_run.sh
```

The script runs with `--network none`, a 16 GB memory limit, and one GPU. It
verifies that the output is a non-empty JSON object at
`diagnostic-imaging-report.json` with exactly one `report` field.

## Training reproduction

Challenge data and derived reports cannot be redistributed. After obtaining
the datasets under their applicable terms, set the project root instead of
editing machine-specific paths:

```bash
export BITE2TEXT_PROJECT_ROOT="$PWD"
export CUDA_HOME=/usr/local/cuda-12.4
export CUDA_VISIBLE_DEVICES=0
./scripts/bootstrap_upstreams.sh
```

Place the authorized training data under the layouts documented in
`task2_bite2text/ptv3_finetune/README.md` and
`task2_bite2text/photo_pipeline/README.md`. The principal workflows are:

```bash
# Patient-separated PTv3 cross-validation.
./task2_bite2text/ptv3_finetune/run_ptv3_v3_cv5.sh

# Unified 867-case PTv3 model with the cross-validated 47-epoch schedule.
./task2_bite2text/ptv3_finetune/run_ptv3_v3_full867.sh

# Photo branch entry points and flags.
python3 task2_bite2text/photo_pipeline/train_multiview_12head.py --help
python3 task2_bite2text/photo_pipeline/train_multiview_full.py --help
```

The full-data training config reads `BITE2TEXT_PTV3_DATA_ROOT` when supplied.
Generated summaries store repository-relative paths so they remain portable.
The photo-training packages are pinned in
`task2_bite2text/photo_pipeline/requirements-training.txt`; the versions were
read from the environment used for the final model. PTv3 dependencies remain
locked by the pinned Bits2Bites `uv.lock`, while the submitted runtime packages
are pinned directly in `task2_bite2text/ptv3_submission/Dockerfile`.

## Input and output contract

The final container accepts paired upper/lower IOS meshes and an intraoral-photo
directory through the Grand Challenge input sockets. Missing or unreadable
photographs trigger a deterministic geometry-only fallback instead of failing
the case. The output contract is:

```json
{"report": "Generated orthodontic diagnostic report."}
```

## Data, security, and clinical-use statement

- API credentials are read only from environment variables and must never be committed.
- Patient-level images, meshes, reports, predictions, and cached LLM responses are excluded.
- The container does not require network access during inference.
- This project is for research and challenge evaluation only and is not a medical device.

## Upstream projects and licensing

- [Bits2Bites](https://github.com/AImageLab-zip/Bits2Bites), pinned at `8c3c685160c9cabe2462e9e23d2ffcd9ca78c63a`.
- [IOS-Normalizer](https://github.com/AImageLab-zip/IOS-Normalizer), pinned at `ecebe110a15081ea435e5970bbe6cf472d8f2882`.
- [RadFact-Lite](https://github.com/AImageLab-zip/radfact_lite), pinned by the local adapter at `053f680be1c57225f94d67b198a34aa871b1127d`.

See [`THIRD_PARTY_NOTICES`](THIRD_PARTY_NOTICES) for license texts and scope.
No challenge dataset, organizer evaluator, IOS-Normalizer source, or pretrained
third-party model is redistributed in this repository.

Original project code is released under the [MIT License](LICENSE). This does
not grant rights to challenge data, patient records, reports, pretrained
weights, retrieval banks, or excluded upstream assets.
