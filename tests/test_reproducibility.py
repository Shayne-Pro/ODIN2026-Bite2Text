"""Public-data-free checks for asset handling and reproduction entry points."""
import hashlib
import csv
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


assets = load("assets", ROOT / "scripts/v9_assets.py")
prepare = load("prepare", ROOT / "scripts/prepare_reproduction.py")
geometry = load("geometry", ROOT / "task2_bite2text/ptv3_finetune/evaluate_geometry_retrieval.py")
cohort = load("cohort", ROOT / "scripts/check_reproduction_data.py")


class AssetsTests(unittest.TestCase):
    def test_release_manifest(self):
        manifest = json.loads(assets.MANIFEST.read_text())
        self.assertEqual(len(manifest["model_files"]), 9)
        for entry in [*manifest["archives"].values(), manifest["image_archive"],
                      manifest["model_archive"], *manifest["model_files"].values()]:
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
            self.assertGreater(entry["bytes"], 0)

    def test_invalid_member_names(self):
        for name in ("../a", "/a", "a/b", "a\\b", ".", ".."):
            with self.subTest(name=name), self.assertRaises(ValueError):
                assets.safe_flat_name(name)
        self.assertEqual(assets.safe_flat_name("./weights.pt"), "weights.pt")

    def make_archive(self, root, name="weights.pt", symlink=False):
        payload = b"test-only-not-a-checkpoint"
        archive = root / "model.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            if symlink:
                member.type = tarfile.SYMTYPE
                member.linkname = "/tmp/escape"
            tar.addfile(member, io.BytesIO(payload))
        manifest = {"model_archive": {"bytes": archive.stat().st_size, "sha256": assets.sha256(archive)},
                    "model_files": {"weights.pt": {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}}}
        return archive, manifest

    def test_verified_extract_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, manifest = self.make_archive(root)
            assets.extract_model(archive, root / "model", manifest)
            assets.verify_model(root / "model", manifest)
            with self.assertRaises(ValueError):
                assets.extract_model(archive, root / "model", manifest)
            (root / "model/weights.pt").write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                assets.verify_model(root / "model", manifest)

    def test_no_extraction_on_checksum_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, manifest = self.make_archive(root)
            manifest["model_archive"]["sha256"] = "0" * 64
            with self.assertRaises(ValueError):
                assets.extract_model(archive, root / "model", manifest)
            self.assertFalse((root / "model").exists())

    def test_reject_traversal_and_symlinks(self):
        for name, symlink in (("../weights.pt", False), ("weights.pt", True)):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                archive, manifest = self.make_archive(root, name, symlink)
                with self.assertRaises(ValueError):
                    assets.extract_model(archive, root / "model", manifest)
                self.assertFalse((root / "model").exists())


class InputTests(unittest.TestCase):
    def test_cohort_rejects_leaking_fold(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, cv, full = (root / name for name in ("data", "cv", "full"))
            observed = {f"synthetic{i}" for i in range(5)}
            for path, selected in ((data, observed | {"unlabeled"}), (full, observed)):
                self.make_cohort(path, selected)
            cv.mkdir()
            with (cv / "fold_assignments.csv").open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["patient_id", "fold"])
                writer.writerows((f"synthetic{i}", i + 1) for i in range(5))
            for i in range(5):
                fold = cv / f"fold{i + 1}"
                self.make_cohort(fold, observed)
                sample = fold / "train" / f"dental_synthetic{i}.npz"
                sample.rename(fold / "val" / sample.name)
                (fold / "test" / sample.name).touch()
            self.assertEqual(cohort.check(data, cv, full, 6, 5)["supervised_cases"], 5)
            (cv / "fold1/train/dental_synthetic0.npz").touch()
            with self.assertRaises(ValueError):
                cohort.check(data, cv, full, 6, 5)

    @staticmethod
    def make_cohort(root, selected):
        for split in ("train", "val", "test"):
            (root / split).mkdir(parents=True)
        for pid in selected:
            (root / "train" / f"dental_{pid}.npz").touch()
        with (root / "labels.csv").open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["patient_id", *[f"label_{i}" for i in range(12)]])
            writer.writerows([pid, *([-1 if pid == "unlabeled" else 0] * 12)] for pid in sorted(selected))
        (root / "head_vocabs.json").write_text(json.dumps({f"head{i}": ["value"] for i in range(12)}))

    def test_stage_read_only_pair_and_skip_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw"
            for patient in ("synthetic1", "synthetic2"):
                (raw / patient / "ios").mkdir(parents=True)
                (raw / patient / "ios/ios_lower.stl").write_bytes(b"synthetic")
            (raw / "synthetic1/ios/ios_upper.stl").write_bytes(b"synthetic")
            result = prepare.stage_ios(raw, root / "staged")
            self.assertEqual(result, {"pairs": 1, "skipped_missing_pair": 1})
            self.assertTrue((root / "staged/synthetic1/ios_lower.stl").is_symlink())
            with self.assertRaises(ValueError):
                prepare.stage_ios(raw, root / "staged")

    def test_geometry_validation_and_shape(self):
        import numpy as np
        for data in (np.zeros((4, 3)), np.ones((5, 3)), np.ones((2, 3)), np.full((4, 3), np.nan)):
            with self.assertRaises(ValueError):
                geometry.descriptor_from_coord(data)
        self.assertEqual(geometry.descriptor_from_coord(np.random.default_rng(1).normal(size=(20, 3))).shape, (3720,))


if __name__ == "__main__":
    unittest.main()
