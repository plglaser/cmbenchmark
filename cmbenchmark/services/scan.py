"""Scan service for dataset analysis."""

import hashlib
import fnmatch
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from cmbenchmark.types.models import DatasetInfo


# Default file extensions to include (supported model file types)
DEFAULT_INCLUDE_PATTERNS = ["*.xmi", "*.uml", "*.xml", "*.bpmn", "*.bpmn2", "*.ecore", "*.archimate"]


def _compute_file_hash(file_path: Path) -> Optional[str]:
    """Compute SHA256 hash of a file."""
    try:
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception:
        return None


def _matches_patterns(file_path: Path, patterns: List[str]) -> bool:
    """Check if a file path matches any of the given glob patterns (case-insensitive)."""
    if not patterns:
        return True
    file_str = str(file_path).lower()
    file_name = file_path.name.lower()
    for pattern in patterns:
        pattern_lower = pattern.lower()
        if fnmatch.fnmatch(file_name, pattern_lower) or fnmatch.fnmatch(file_str, pattern_lower):
            return True
    return False


def _parse_exclude_patterns(exclude_str: Optional[str]) -> List[str]:
    """Parse exclude patterns from comma-separated string."""
    if not exclude_str:
        return []
    return [pattern.strip() for pattern in exclude_str.split(",") if pattern.strip()]


def scan_dataset(
    dataset_path: str,
    exclude: Optional[str] = None,
    size_limit_mb: Optional[int] = None,
) -> DatasetInfo:
    """
    Scan a dataset directory for model files and generate statistics.

    Args:
        dataset_path: Path to dataset directory
        exclude: Comma-separated list of file patterns to exclude (e.g., "*.xml").
                 Can be used to exclude specific file types from the default include list.
        size_limit_mb: Maximum file size in MB (files exceeding this will be marked as too_large)

    Returns:
        DatasetInfo object containing scan results
        
    Raises:
        ValueError: If dataset path is invalid
    """
    # Step 1: Initialize
    dataset_dir = Path(dataset_path).resolve()
    if not dataset_dir.exists():
        raise ValueError(f"Dataset path does not exist: {dataset_path}")
    if not dataset_dir.is_dir():
        raise ValueError(f"Dataset path is not a directory: {dataset_path}")
    if not os.access(dataset_dir, os.R_OK):
        raise ValueError(f"Dataset path is not readable: {dataset_path}")

    # Always use default include patterns
    include_patterns = DEFAULT_INCLUDE_PATTERNS.copy()
    
    # Parse user exclude patterns
    exclude_patterns = _parse_exclude_patterns(exclude)

    # Step 2: Build Candidate File List
    total_seen = 0
    candidate_files: List[Path] = []

    # Walk directory tree
    for file_path in dataset_dir.rglob("*"):
        if not file_path.is_file():
            continue

        total_seen += 1

        # Apply include filter (always use default include patterns)
        if not _matches_patterns(file_path, include_patterns):
            continue

        # Skip excluded patterns (only if user provided exclude patterns)
        if exclude_patterns and _matches_patterns(file_path, exclude_patterns):
            continue

        candidate_files.append(file_path)

    # Step 3: Sanity & Safety Checks
    unreadable_files: List[str] = []
    too_large_files: List[str] = []
    file_hashes: Dict[str, List[Path]] = {}  # hash -> list of files with that hash
    extension_counts: Dict[str, int] = {}
    size_limit_bytes = (size_limit_mb * 1024 * 1024) if size_limit_mb else None

    for file_path in candidate_files:
        # Track extension
        ext = file_path.suffix or ".noext"
        extension_counts[ext] = extension_counts.get(ext, 0) + 1

        # Check readability
        try:
            with open(file_path, "rb") as f:
                f.read(1)  # Try to read at least one byte
        except Exception:
            unreadable_files.append(str(file_path.relative_to(dataset_dir)))
            continue

        # Check size threshold
        try:
            file_size = file_path.stat().st_size
            if size_limit_bytes and file_size > size_limit_bytes:
                too_large_files.append(str(file_path.relative_to(dataset_dir)))
        except Exception:
            # If we can't get file size, skip duplicate detection for this file
            continue

        # Compute hash for duplicate detection
        file_hash = _compute_file_hash(file_path)
        if file_hash:
            if file_hash not in file_hashes:
                file_hashes[file_hash] = []
            file_hashes[file_hash].append(file_path)

    # Build duplicate groups (only groups with 2+ files)
    duplicates_groups: List[Dict[str, Any]] = []
    duplicate_files_to_exclude: set[Path] = set()  # Files to exclude from candidates (all but first in each group)
    
    for file_hash, files in file_hashes.items():
        if len(files) > 1:
            # Sort files for deterministic selection (keep first, exclude rest)
            sorted_files = sorted(files, key=lambda p: str(p.relative_to(dataset_dir)))
            duplicates_groups.append({
                "count": len(files),
                "members": [str(f.relative_to(dataset_dir)) for f in sorted_files]
            })
            # Mark all but the first file as duplicates to exclude
            duplicate_files_to_exclude.update(sorted_files[1:])

    # Build candidates list (relative paths), excluding too_large, unreadable, and duplicate files
    too_large_set = set(too_large_files)
    unreadable_set = set(unreadable_files)
    candidates_list = [
        str(f.relative_to(dataset_dir))
        for f in candidate_files
        if str(f.relative_to(dataset_dir)) not in too_large_set
        and str(f.relative_to(dataset_dir)) not in unreadable_set
        and f not in duplicate_files_to_exclude
    ]

    # Step 4: Create Summary
    scanned_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return DatasetInfo(
        dataset_root=str(dataset_dir),
        scanned_at=scanned_at,
        parameters={
            "include": sorted(include_patterns),  # Sort for consistent output
            "exclude": sorted(exclude_patterns) if exclude_patterns else [],  # Sort for consistent output
            "size_limit_mb": size_limit_mb,
        },
        totals={
            "total_seen": total_seen,
            "candidates": len(candidates_list),
            "unreadable": len(unreadable_files),
            "too_large": len(too_large_files),
        },
        extensions=extension_counts,
        duplicates_groups=duplicates_groups,
        too_large=[str(f) for f in too_large_files],
        unreadable=[str(f) for f in unreadable_files],
        candidates=candidates_list,
    )

