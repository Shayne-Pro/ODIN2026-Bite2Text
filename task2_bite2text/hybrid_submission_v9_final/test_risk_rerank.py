#!/usr/bin/env python3
"""Unit tests for the conservative v9 retrieval gate."""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

# Import only the retrieval logic without loading the production mesh pipeline.
inference_stub = types.ModuleType("inference")
for name in (
    "env_path",
    "inference_sample",
    "input_files",
    "load_model",
    "postcorrect_triangles",
    "run_ios_normalizer",
    "sampled_coordinates",
):
    setattr(inference_stub, name, lambda *args, **kwargs: None)
sys.modules["inference"] = inference_stub

retrieval_stub = types.ModuleType("retrieval_inference")
retrieval_stub.descriptor_from_coord = lambda value: value
retrieval_stub.load_assets = lambda *args, **kwargs: None
sys.modules["retrieval_inference"] = retrieval_stub

photo_stub = types.ModuleType("photo_inference")
photo_stub.run_photo_inference = lambda *args, **kwargs: None
sys.modules["photo_inference"] = photo_stub

from hybrid_inference import CV_F1, select_report


class RiskRerankTests(unittest.TestCase):
    def setUp(self) -> None:
        self.heads = list(CV_F1)
        self.predicted = {head: "a" for head in self.heads}
        self.confidence = {head: 0.9 for head in self.heads}
        baseline_labels = {head: None for head in self.heads}
        baseline_labels[self.heads[0]] = "b"
        safe_labels = {head: None for head in self.heads}
        self.labels = [baseline_labels, safe_labels]
        self.config = {
            "enabled": True,
            "margin": 0.02,
            "unsupported_penalty": 0.005,
            "unsupported_gate": 5,
            "contradiction_threshold": 0.65,
            "contradiction_gate": 0.01,
            "contradiction_penalty": 0.5,
            "min_contradiction_improvement": 0.015,
            "no_new_unsupported": True,
        }

    def select(self, *, enabled: bool) -> tuple[int, dict[str, object]]:
        config = {**self.config, "enabled": enabled}
        result = select_report(
            descriptor=np.asarray([1.0]),
            predicted_labels=self.predicted,
            patient_ids=np.asarray(["baseline", "safer"]),
            database=np.asarray([[1.0], [0.995]], dtype=np.float64),
            mean=np.asarray([0.0]),
            scale=np.asarray([1.0]),
            reports=[
                "The dental arches are described.",
                "The dental arches are described conservatively.",
            ],
            candidate_labels=self.labels,
            top_k=2,
            blend_lambda=0.5,
            confidence=self.confidence,
            risk_config=config,
        )
        return result[0], result[-1]

    def test_reranks_close_high_confidence_contradiction(self) -> None:
        index, summary = self.select(enabled=True)
        self.assertEqual(index, 1)
        self.assertTrue(summary["reranked"])
        self.assertEqual(summary["reason"], "contradiction")

    def test_disable_flag_is_exact_v8_fallback(self) -> None:
        index, summary = self.select(enabled=False)
        self.assertEqual(index, 0)
        self.assertFalse(summary["reranked"])


if __name__ == "__main__":
    unittest.main()
