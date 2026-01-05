from cmbenchmark.services import scan_dataset

def test_scan_basic(tmp_path):
    # Create minimal dataset
    (tmp_path / "a.xmi").write_text("<model1 />")
    (tmp_path / "b.xml").write_text("<model2 />")
    (tmp_path / "ignore.png").write_text("binarydata")

    result = scan_dataset(str(tmp_path))

    assert result.totals["total_seen"] == 3
    assert result.totals["candidates"] == 2
    assert result.totals["unreadable"] == 0
    assert result.totals["too_large"] == 0
    assert result.totals["filtered"] == 1
    assert result.extensions[".xmi"] == 1
    assert result.extensions[".xml"] == 1
    assert sorted(result.candidates) == ["a.xmi", "b.xml"]
    assert "ignore.png" in result.filtered

def test_nested_directories(tmp_path):
    sub = tmp_path / "nested" / "models"
    sub.mkdir(parents=True)
    (sub / "a.xmi").write_text("<m/>")

    result = scan_dataset(str(tmp_path))

    assert "nested/models/a.xmi" in result.candidates

def test_empty_directory(tmp_path):
    result = scan_dataset(str(tmp_path))

    assert result.totals["total_seen"] == 0
    assert result.totals["candidates"] == 0
    assert result.totals["filtered"] == 0
    assert result.candidates == []
    assert result.filtered == []


def test_unreadable_file(tmp_path):
    f = tmp_path / "broken.xmi"
    f.write_text("<model />")
    f.chmod(0o000)   # Make unreadable

    result = scan_dataset(str(tmp_path))

    assert result.totals["unreadable"] == 1
    assert "broken.xmi" in result.unreadable
    assert "broke.xmi" not in result.candidates


def test_exclude_pattern(tmp_path):
    (tmp_path / "a.xmi").write_text("a")
    (tmp_path / "b.xml").write_text("b")

    result = scan_dataset(str(tmp_path), exclude=["*.xml"])

    assert "b.xml" not in result.candidates
    assert "a.xmi" in result.candidates
    assert "b.xml" in result.filtered
    assert result.totals["filtered"] == 1


def test_exclude_pattern_case_insensitive(tmp_path):
    (tmp_path / "a.xml").write_text("a")
    (tmp_path / "b.XML").write_text("b")
    (tmp_path / "c.Xml").write_text("c")

    # Exclude with uppercase pattern should exclude all case variations
    result = scan_dataset(str(tmp_path), exclude=["*.XML"])

    assert "a.xml" not in result.candidates
    assert "b.XML" not in result.candidates
    assert "c.Xml" not in result.candidates
    assert all(f in result.filtered for f in ["a.xml", "b.XML", "c.Xml"])
    assert result.totals["filtered"] == 3

    # Exclude with lowercase pattern should also exclude all case variations
    (tmp_path / "d.XML").write_text("d")
    result2 = scan_dataset(str(tmp_path), exclude=["*.xml"])

    assert "a.xml" not in result2.candidates
    assert "b.XML" not in result2.candidates
    assert "c.Xml" not in result2.candidates
    assert "d.XML" not in result2.candidates
    assert result2.totals["filtered"] == 4


def test_size_limit(tmp_path):
    small = tmp_path / "small.xmi"
    small.write_bytes(b"123")

    big = tmp_path / "big.xmi"
    big.write_bytes(b"x" * (2 * 1024 * 1024))  # 2 MB

    result = scan_dataset(str(tmp_path), size_limit_mb=1)

    assert "big.xmi" in result.too_large
    assert "big.xmi" not in result.candidates
    assert "small.xmi" in result.candidates
    


def test_duplicate_detection(tmp_path):
    content = "<model />"
    (tmp_path / "a.xmi").write_text(content)
    (tmp_path / "b.xmi").write_text(content)

    result = scan_dataset(str(tmp_path))
    
    # duplicates should not be included in candidates list (only one representative kept)
    assert len(result.candidates) == 1
    assert result.candidates[0] == "a.xmi"  # First alphabetically is kept
    assert len(result.duplicates_groups) == 1
    group = result.duplicates_groups[0]["members"]
    assert sorted(group) == ["a.xmi", "b.xmi"]  # Both still reported in duplicates_groups