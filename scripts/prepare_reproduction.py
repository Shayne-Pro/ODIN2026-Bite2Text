#!/usr/bin/env python3
"""Stage read-only IOS inputs or assemble newly retrained v9 assets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil


def stage_ios(raw: Path, output: Path, excluded: tuple[str, ...] = ()) -> dict:
    if not raw.is_dir():
        raise ValueError(f"Missing extracted Bite2Text patient root: {raw}")
    if output.exists():
        raise ValueError(f"Refusing to overwrite: {output}")
    pairs = []
    skipped = []
    for patient in sorted(p for p in raw.iterdir() if p.is_dir()):
        if patient.name in excluded:
            continue
        scans = [patient / "ios" / f"ios_{jaw}.stl" for jaw in ("lower", "upper")]
        if all(p.is_file() for p in scans):
            pairs.append((patient.name, scans))
        else:
            skipped.append(patient.name)
    if not pairs:
        raise ValueError("No raw patient/ios/ios_{lower,upper}.stl pairs found")
    output.mkdir(parents=True)
    for patient_id, scans in pairs:
        dest = output / patient_id
        dest.mkdir()
        for scan in scans:
            (dest / scan.name).symlink_to(scan.resolve())
    audit = {"pairs": len(pairs), "skipped_missing_pair": skipped, "explicit_exclusions": list(excluded)}
    (output / "staging_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    return {"pairs": len(pairs), "skipped_missing_pair": len(skipped)}


def assemble(output: Path, ptv3: Path, data: Path, photo: Path,
             view: Path, normalizer: Path, retrieval: Path) -> dict:
    if output.exists():
        raise ValueError(f"Refusing to overwrite: {output}")
    sources = {
        "model_final.pth": ptv3 / "model/model_last.pth",
        "config.py": ptv3 / "config.py",
        "head_vocabs.json": data / "head_vocabs.json",
        "photo_model_final.pt": photo,
        "photo_view_classifier.pt": view,
        "ios_normalizer_best.pt": normalizer,
        **{name: retrieval / name for name in
           ("retrieval_index.npz", "retrieval_reports.json", "retrieval_labels.json")},
    }
    for path in sources.values():
        if not path.is_file():
            raise ValueError(f"Missing asset: {path}")
    audit = json.loads((data / "full_dataset_audit.json").read_text())
    if audit["train_cases"] != 867:
        raise ValueError("Final v9 recipe requires exactly 867 supervised cases")
    import numpy as np  # Only assembly needs NumPy; no checkpoint deserialization.
    reports = json.loads(sources["retrieval_reports.json"].read_text())
    labels = json.loads(sources["retrieval_labels.json"].read_text())
    with np.load(sources["retrieval_index.npz"], allow_pickle=False) as index:
        if index["descriptors"].shape != (867, 3720):
            raise ValueError("Expected a (867, 3720) retrieval index")
        if index["patient_ids"].tolist() != reports["patient_ids"] or reports["patient_ids"] != labels["patient_ids"]:
            raise ValueError("Retrieval assets have inconsistent patient order")
    output.mkdir(parents=True)
    hashes = {}
    for name, path in sources.items():
        shutil.copyfile(path, output / name)
        hashes[name] = hashlib.sha256((output / name).read_bytes()).hexdigest()
    (output / "retrained_asset_hashes.json").write_text(json.dumps(hashes, indent=2) + "\n")
    return {"files": len(sources), "output": str(output), "exact_submitted_weights": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    stage = sub.add_parser("stage-ios")
    stage.add_argument("--raw-root", type=Path, required=True)
    stage.add_argument("--output-root", type=Path, required=True)
    stage.add_argument("--exclude-patient", action="append", default=[])
    pack = sub.add_parser("assemble-model")
    for name in ("output", "ptv3", "data", "photo", "view", "normalizer", "retrieval"):
        pack.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.command == "stage-ios":
        result = stage_ios(args.raw_root, args.output_root, tuple(args.exclude_patient))
    else:
        result = assemble(args.output, args.ptv3, args.data, args.photo,
                          args.view, args.normalizer, args.retrieval)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
