#!/usr/bin/env python3
"""Download and prepare the benchmark datasets used by this repository."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = REPO_ROOT / "data"
DEFAULT_DOWNLOAD_DIR = REPO_ROOT / "downloads"

EAMODELSET_URL = (
    "https://github.com/me-big-tuwien-ac-at/EAModelSet/releases/download/v0.0.3/eamodelset.zip"
)
MODELSET_URL = "https://github.com/modelset/modelset-dataset/releases/download/v0.9.4/modelset.zip"
ATLANTIC_ZOO_URL = "https://github.com/atlanmod/atlantic-zoo/archive/refs/heads/main.zip"


@dataclass(frozen=True)
class DatasetTask:
    name: str
    description: str
    output_dir: str
    run: Callable[[Path, Path, bool], int]


def _download(url: str, destination: Path, force: bool) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        print(f"Using cached archive: {destination}")
        return destination

    print(f"Downloading {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "cmbenchmark-dataset-downloader"})
    with urllib.request.urlopen(request) as response, destination.open("wb") as file:
        shutil.copyfileobj(response, file)
    return destination


def _safe_extract_zip(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    base = destination.resolve()
    with zipfile.ZipFile(archive) as zip_file:
        for member in zip_file.infolist():
            target = (destination / member.filename).resolve()
            if base != target and base not in target.parents:
                raise RuntimeError(f"Unsafe ZIP member path: {member.filename}")
        zip_file.extractall(destination)


def _prepare_output_dir(path: Path, force: bool) -> None:
    if path.exists() and force:
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _copy_flat_unique(files: Iterable[Path], output_dir: Path, suffix: str) -> int:
    count = 0
    used_names: set[str] = set()
    for source in sorted(files):
        name = f"{source.stem}{suffix}"
        if name in used_names:
            parent_slug = "_".join(source.parent.parts[-3:])
            name = f"{parent_slug}_{source.stem}{suffix}"
        if name in used_names:
            index = 2
            while f"{source.stem}_{index}{suffix}" in used_names:
                index += 1
            name = f"{source.stem}_{index}{suffix}"
        used_names.add(name)
        _copy_file(source, output_dir / name)
        count += 1
    return count


def _find_single_directory(root: Path, name: str) -> Path:
    matches = [path for path in root.rglob(name) if path.is_dir()]
    if not matches:
        raise RuntimeError(f"Could not find directory '{name}' below {root}")
    return sorted(matches, key=lambda path: len(path.parts))[0]


def prepare_eamodelset(data_dir: Path, downloads_dir: Path, force: bool) -> int:
    archive = _download(EAMODELSET_URL, downloads_dir / "eamodelset.zip", force)
    output_dir = data_dir / "eamodelset"
    _prepare_output_dir(output_dir, force)

    with tempfile.TemporaryDirectory(prefix="cmbenchmark-eamodelset-") as tmp:
        extract_dir = Path(tmp)
        _safe_extract_zip(archive, extract_dir)
        processed_models = _find_single_directory(extract_dir, "processed-models")
        files = processed_models.glob("*/model.archimate")
        count = 0
        for source in sorted(files):
            model_id = source.parent.name
            _copy_file(source, output_dir / f"{model_id}.archimate")
            count += 1

    print(f"Prepared {count} EA ModelSet ArchiMate models in {output_dir}")
    return count


def _extract_modelset(archive: Path) -> tempfile.TemporaryDirectory[str]:
    tmp = tempfile.TemporaryDirectory(prefix="cmbenchmark-modelset-")
    _safe_extract_zip(archive, Path(tmp.name))
    return tmp


def _modelset_root(extract_dir: Path) -> Path:
    raw_data_dirs = sorted(extract_dir.rglob("raw-data"))
    for raw_data_dir in raw_data_dirs:
        if (raw_data_dir / "repo-genmymodel-uml" / "data").is_dir():
            return raw_data_dir.parent
    raise RuntimeError(f"Could not find ModelSet root below {extract_dir}")


def prepare_modelset_uml(data_dir: Path, downloads_dir: Path, force: bool) -> int:
    archive = _download(MODELSET_URL, downloads_dir / "modelset.zip", force)
    output_dir = data_dir / "modelset-uml"
    _prepare_output_dir(output_dir, force)

    with _extract_modelset(archive) as tmp:
        source_dir = _modelset_root(Path(tmp)) / "raw-data" / "repo-genmymodel-uml" / "data"
        count = _copy_flat_unique(source_dir.glob("*.xmi"), output_dir, ".xmi")

    print(f"Prepared {count} ModelSet UML XMI models in {output_dir}")
    return count


def prepare_modelset_ecore(data_dir: Path, downloads_dir: Path, force: bool) -> int:
    archive = _download(MODELSET_URL, downloads_dir / "modelset.zip", force)
    output_dir = data_dir / "modelset"
    _prepare_output_dir(output_dir, force)

    with _extract_modelset(archive) as tmp:
        source_dir = _modelset_root(Path(tmp)) / "raw-data" / "repo-ecore-all" / "data"
        count = 0
        for source in sorted(path for path in source_dir.rglob("*.ecore") if path.is_file()):
            _copy_file(source, output_dir / source.relative_to(source_dir))
            count += 1

    print(f"Prepared {count} ModelSet Ecore models in {output_dir}")
    return count


def prepare_atlantic_zoo(data_dir: Path, downloads_dir: Path, force: bool) -> int:
    archive = _download(ATLANTIC_ZOO_URL, downloads_dir / "atlantic-zoo-main.zip", force)
    output_dir = data_dir / "atlanticzoo"
    _prepare_output_dir(output_dir, force)

    with tempfile.TemporaryDirectory(prefix="cmbenchmark-atlantic-zoo-") as tmp:
        extract_dir = Path(tmp)
        _safe_extract_zip(archive, extract_dir)
        source_dir = _find_single_directory(extract_dir, "AtlantEcore")
        count = 0
        for source in sorted(path for path in source_dir.rglob("*.ecore") if path.is_file()):
            _copy_file(source, output_dir / source.relative_to(source_dir))
            count += 1

    print(f"Prepared {count} Atlantic Zoo Ecore models in {output_dir}")
    return count


TASKS: dict[str, DatasetTask] = {
    "eamodelset": DatasetTask(
        name="eamodelset",
        description="EA ModelSet ArchiMate files only",
        output_dir="data/eamodelset",
        run=prepare_eamodelset,
    ),
    "modelset-uml": DatasetTask(
        name="modelset-uml",
        description="ModelSet UML XMI files only",
        output_dir="data/modelset-uml",
        run=prepare_modelset_uml,
    ),
    "modelset-ecore": DatasetTask(
        name="modelset-ecore",
        description="ModelSet Ecore files only",
        output_dir="data/modelset",
        run=prepare_modelset_ecore,
    ),
    "atlanticzoo": DatasetTask(
        name="atlanticzoo",
        description="Atlantic Zoo Ecore files",
        output_dir="data/atlanticzoo",
        run=prepare_atlantic_zoo,
    ),
}


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and prepare CM-Benchmarking datasets into the data/ directory."
    )
    parser.add_argument(
        "--only",
        action="append",
        choices=sorted(TASKS),
        help="Prepare only the selected dataset. Can be passed multiple times.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Output data directory. Defaults to {DEFAULT_DATA_DIR}",
    )
    parser.add_argument(
        "--downloads-dir",
        type=Path,
        default=DEFAULT_DOWNLOAD_DIR,
        help=f"Archive cache directory. Defaults to {DEFAULT_DOWNLOAD_DIR}",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download archives and replace the selected output directories.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available datasets and exit.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    if args.list:
        for task in TASKS.values():
            print(f"{task.name:15} {task.description} -> {task.output_dir}")
        return 0

    selected = args.only or list(TASKS)
    total = 0
    for name in selected:
        task = TASKS[name]
        print(f"\n== {task.description} ==")
        total += task.run(args.data_dir.resolve(), args.downloads_dir.resolve(), args.force)

    print(f"\nDone. Prepared {total} model files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
