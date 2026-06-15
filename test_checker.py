import pytest
from pathlib import Path
import checker

# -----------------------------------------------------------------------------
# What is a test?
#   A test is just a function whose name starts with "test_".
#   Inside it, you call the code you wrote and then use "assert" to check
#   that the result is what you expect. If the assert fails, pytest marks
#   the test as FAILED and shows you why.
#
# What is a fixture?
#   A fixture is a helper that sets up (and tears down) something your tests
#   need — like a temporary folder full of files. pytest runs it automatically
#   when a test asks for it by name in its parameters.
# -----------------------------------------------------------------------------


# ── Fixture ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_folder(tmp_path):
    """
    pytest's built-in `tmp_path` gives us a fresh temporary directory for
    every test. We create a sub-folder called 'monitored' to hold the test
    files. This keeps the baselines directory (tmp_path / 'baselines') outside
    the folder being scanned, so check() won't mistake the YAML file for a
    newly added file.
    """
    folder = tmp_path / "monitored"
    folder.mkdir()
    (folder / "a.txt").write_text("hello")
    (folder / "b.txt").write_text("world")
    return folder


# ── Tests for hash_file ───────────────────────────────────────────────────────

def test_hash_file_returns_string(tmp_path):
    """hash_file should return a hex string."""
    f = tmp_path / "sample.txt"
    f.write_text("some content")
    result = checker.hash_file(f)
    assert isinstance(result, str)
    assert len(result) == 64          # SHA-256 produces a 64-char hex digest


def test_hash_file_same_content_same_hash(tmp_path):
    """Two files with identical content must produce the same hash."""
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f1.write_text("identical")
    f2.write_text("identical")
    assert checker.hash_file(f1) == checker.hash_file(f2)


def test_hash_file_different_content_different_hash(tmp_path):
    """Two files with different content must produce different hashes."""
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f1.write_text("hello")
    f2.write_text("world")
    assert checker.hash_file(f1) != checker.hash_file(f2)


# ── Tests for create_baseline ─────────────────────────────────────────────────

def test_create_baseline_creates_yaml(tmp_folder, tmp_path, monkeypatch):
    """
    create_baseline should write a .yaml file in BASELINES_DIR.
    `monkeypatch` lets us temporarily redirect BASELINES_DIR to a safe
    temp location so we don't litter the real baselines/ folder.
    """
    fake_baselines = tmp_path / "baselines"
    monkeypatch.setattr(checker, "BASELINES_DIR", fake_baselines)

    checker.create_baseline(tmp_folder)

    expected = fake_baselines / f"{tmp_folder.name}.yaml"
    assert expected.exists()


def test_create_baseline_yaml_contains_all_files(tmp_folder, tmp_path, monkeypatch):
    """The generated YAML should have an entry for every file in the folder."""
    fake_baselines = tmp_path / "baselines"
    monkeypatch.setattr(checker, "BASELINES_DIR", fake_baselines)

    checker.create_baseline(tmp_folder)

    import yaml
    baseline_file = fake_baselines / f"{tmp_folder.name}.yaml"
    with open(baseline_file) as f:
        data = yaml.safe_load(f)

    # tmp_folder has a.txt and b.txt
    assert "a.txt" in data
    assert "b.txt" in data


# ── Tests for check ───────────────────────────────────────────────────────────

def test_check_no_changes(tmp_folder, tmp_path, monkeypatch, capsys):
    """
    After creating a baseline, running check on the same unmodified folder
    should report no changes.
    `capsys` captures whatever the code prints so we can assert on it.
    """
    fake_baselines = tmp_path / "baselines"
    monkeypatch.setattr(checker, "BASELINES_DIR", fake_baselines)

    checker.create_baseline(tmp_folder)
    checker.check(tmp_folder)

    output = capsys.readouterr().out
    assert "No changes detected" in output


def test_check_detects_modified_file(tmp_folder, tmp_path, monkeypatch, capsys):
    """If a file's content changes after the baseline, check should flag it."""
    fake_baselines = tmp_path / "baselines"
    monkeypatch.setattr(checker, "BASELINES_DIR", fake_baselines)

    checker.create_baseline(tmp_folder)

    # Modify one file AFTER the baseline was taken
    (tmp_folder / "a.txt").write_text("changed content")

    checker.check(tmp_folder)
    output = capsys.readouterr().out
    assert "Modified files" in output
    assert "a.txt" in output


def test_check_detects_added_file(tmp_folder, tmp_path, monkeypatch, capsys):
    """A file that didn't exist at baseline time should appear as added."""
    fake_baselines = tmp_path / "baselines"
    monkeypatch.setattr(checker, "BASELINES_DIR", fake_baselines)

    checker.create_baseline(tmp_folder)

    (tmp_folder / "new.txt").write_text("brand new")

    checker.check(tmp_folder)
    output = capsys.readouterr().out
    assert "Added files" in output
    assert "new.txt" in output


def test_check_detects_removed_file(tmp_folder, tmp_path, monkeypatch, capsys):
    """A file present at baseline time but now deleted should appear as removed."""
    fake_baselines = tmp_path / "baselines"
    monkeypatch.setattr(checker, "BASELINES_DIR", fake_baselines)

    checker.create_baseline(tmp_folder)

    (tmp_folder / "b.txt").unlink()   # delete the file

    checker.check(tmp_folder)
    output = capsys.readouterr().out
    assert "Removed files" in output
    assert "b.txt" in output


def test_check_missing_baseline(tmp_folder, tmp_path, monkeypatch, capsys):
    """If no baseline exists yet, check should print a helpful message."""
    fake_baselines = tmp_path / "baselines"
    monkeypatch.setattr(checker, "BASELINES_DIR", fake_baselines)

    # Intentionally skip create_baseline
    checker.check(tmp_folder)

    output = capsys.readouterr().out
    assert "No baseline found" in output
