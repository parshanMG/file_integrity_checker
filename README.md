# File Integrity Checker

A Python CLI tool that detects unauthorized or unexpected changes to files by comparing SHA-256 cryptographic hashes against a stored baseline. Useful for security auditing, configuration drift detection, and compliance monitoring.

---

## Features

- **Baseline creation** — snapshot the hash of every file in a directory
- **Integrity check** — compare the current state against the baseline and report:
  - Added files
  - Removed files
  - Modified files
- **No changes detected** message when everything matches
- Baselines stored as human-readable YAML files
- Fully unit tested with pytest

---

## Project Structure

```
file_integrity_checker/
├── checker.py          # Main CLI tool
├── test_checker.py     # pytest unit tests
├── baselines/          # Auto-created; stores baseline YAML files
└── README.md
```

---

## Requirements

- Python 3.8+
- `pyyaml`
- `pytest` (for running tests)

Install dependencies:

```bash
pip install pyyaml pytest
```

---

## Usage

### 1. Create a baseline

Snapshot the current state of a folder:

```bash
python checker.py create_baseline path/to/folder
```

This creates `baselines/<folder-name>.yaml` containing the SHA-256 hash of every file.

### 2. Check for changes

Compare the folder's current state against the baseline:

```bash
python checker.py check path/to/folder
```

Example output when changes are found:

```
Added files:
  + new_script.py
Removed files:
  - old_config.txt
Modified files:
  * app/settings.py
```

Example output when nothing has changed:

```
No changes detected. All files match the baseline.
```

---

## Running Tests

```bash
pytest test_checker.py -v
```

The test suite covers:

| Test | What it verifies |
|---|---|
| `test_hash_file_returns_string` | Returns a valid 64-char hex digest |
| `test_hash_file_same_content_same_hash` | Identical content produces identical hash |
| `test_hash_file_different_content_different_hash` | Different content produces different hash |
| `test_create_baseline_creates_yaml` | YAML baseline file is written to disk |
| `test_create_baseline_yaml_contains_all_files` | All files are recorded in the baseline |
| `test_check_no_changes` | Reports clean when nothing has changed |
| `test_check_detects_modified_file` | Flags files whose content changed |
| `test_check_detects_added_file` | Flags files added after the baseline |
| `test_check_detects_removed_file` | Flags files deleted after the baseline |
| `test_check_missing_baseline` | Prints helpful message when no baseline exists |

---

## How It Works

1. `hash_file()` reads a file in 8 KB chunks and feeds each chunk into a SHA-256 digest — memory-efficient for large files
2. `create_baseline()` walks the target directory recursively, hashes every file, and serializes the `{ relative_path: hash }` mapping to YAML
3. `check()` re-hashes all current files, loads the stored baseline, and computes the symmetric difference between the two sets

---

## Technologies

`Python` · `SHA-256` · `YAML` · `argparse` · `pytest` · `pathlib` · `Git`
