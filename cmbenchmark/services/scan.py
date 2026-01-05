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


def _matches_patterns(file_path: Path, patterns: List[str], dataset_root: Optional[Path] = None) -> bool:
    """
    Check if a file path matches any of the given glob patterns (case-insensitive).
    
    Patterns are matched against:
    1. The filename only (e.g., "*.xml")
    2. The relative path from dataset root (e.g., "test/*", "subdir/file.xml")
    3. The full absolute path (for backward compatibility)
    
    Supports recursive patterns with "**" (e.g., "test/**" matches all files in test/ and subdirectories).
    
    Args:
        file_path: Absolute path to the file
        patterns: List of glob patterns to match
        dataset_root: Optional root directory for relative path matching
    """
    if not patterns:
        return True
    
    file_name = file_path.name.lower()
    file_str = str(file_path).lower()
    
    # Compute relative path if dataset_root is provided
    rel_path_str = None
    if dataset_root:
        try:
            rel_path_str = str(file_path.relative_to(dataset_root)).lower()
        except ValueError:
            # file_path is not relative to dataset_root, skip relative matching
            pass
    
    for pattern in patterns:
        pattern_lower = pattern.lower()
        
        # Handle recursive patterns (**)
        if "**" in pattern_lower:
            # Convert ** pattern to work with fnmatch
            # Replace ** with * for simple matching, or use pathlib for recursive
            if rel_path_str:
                # For recursive patterns, check if the relative path starts with the pattern prefix
                # e.g., "test/**" should match "test/anything" and "test/subdir/file"
                pattern_prefix = pattern_lower.split("**")[0].rstrip("/")
                if pattern_prefix and rel_path_str.startswith(pattern_prefix):
                    return True
                # Also try with * instead of ** for fnmatch
                pattern_with_star = pattern_lower.replace("**", "*")
                if fnmatch.fnmatch(rel_path_str, pattern_with_star):
                    return True
        
        # Match against filename
        if fnmatch.fnmatch(file_name, pattern_lower):
            return True
        # Match against relative path (most common for directory patterns)
        if rel_path_str and fnmatch.fnmatch(rel_path_str, pattern_lower):
            return True
        # Match against full absolute path (for backward compatibility)
        if fnmatch.fnmatch(file_str, pattern_lower):
            return True
    
    return False


def scan_dataset(
    dataset_path: str,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    size_limit_mb: Optional[int] = None,
) -> DatasetInfo:
    """
    Scan a dataset directory for model files and generate statistics.

    Args:
        dataset_path: Path to dataset directory
        include: List of file patterns to include. If None, uses default patterns.
        exclude: List of file patterns to exclude. Applied after include filtering.
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

    # Determine include patterns: use provided patterns or defaults
    if include is not None:
        include_patterns = include.copy()
    else:
        include_patterns = DEFAULT_INCLUDE_PATTERNS.copy()
    
    # Normalize exclude patterns (empty list if None)
    exclude_patterns = exclude.copy() if exclude else []

    # Step 2: Build Candidate File List
    total_seen = 0
    candidate_files: List[Path] = []
    filtered_files: List[str] = []

    # Walk directory tree
    for file_path in dataset_dir.rglob("*"):
        if not file_path.is_file():
            continue

        total_seen += 1

        # Apply include filter
        if not _matches_patterns(file_path, include_patterns, dataset_dir):
            filtered_files.append(str(file_path.relative_to(dataset_dir)))
            continue

        # Skip excluded patterns
        if exclude_patterns and _matches_patterns(file_path, exclude_patterns, dataset_dir):
            filtered_files.append(str(file_path.relative_to(dataset_dir)))
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
            "exclude": sorted(exclude_patterns),  # Sort for consistent output
            "size_limit_mb": size_limit_mb,
        },
        totals={
            "total_seen": total_seen,
            "candidates": len(candidates_list),
            "unreadable": len(unreadable_files),
            "too_large": len(too_large_files),
            "filtered": len(filtered_files),
        },
        extensions=extension_counts,
        duplicates_groups=duplicates_groups,
        too_large=[str(f) for f in too_large_files],
        unreadable=[str(f) for f in unreadable_files],
        candidates=candidates_list,
        filtered=sorted(filtered_files),  # Sort for consistent output
    )

