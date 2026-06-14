import hashlib
import yaml
import argparse
from pathlib import Path

BASELINES_DIR = Path("baselines")

def hash_file(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def create_baseline(folder):
    folder = Path(folder)
    hashes = {}
    for file in folder.rglob("*"):
        if file.is_file():
            relative = str(file.relative_to(folder))
            hashes[relative] = hash_file(file)
    BASELINES_DIR.mkdir(exist_ok=True)
    output_file = BASELINES_DIR / f"{folder.name}.yaml"
    with open(output_file, "w") as f:
        yaml.dump(hashes, f)
    print(f"Baseline created for {len(hashes)} file(s) in '{folder}' -> {output_file}")

def check(folder):
        folder = Path(folder)
        baseline_file = BASELINES_DIR / f"{folder.name}.yaml"
        if not baseline_file.exists():
            print(f"No baseline found for '{folder}'. Please create a baseline first.")
            return

        with open(baseline_file, "r") as f:
            baseline_hashes = yaml.safe_load(f)

        current_hashes = {}
        for file in folder.rglob("*"):
            if file.is_file():
                relative = str(file.relative_to(folder))
                current_hashes[relative] = hash_file(file)

        # Compare hashes
        added_files = set(current_hashes.keys()) - set(baseline_hashes.keys())
        removed_files = set(baseline_hashes.keys()) - set(current_hashes.keys())
        modified_files = {f for f in current_hashes if f in baseline_hashes and current_hashes[f] != baseline_hashes[f]}

        if not added_files and not removed_files and not modified_files:
            print("No changes detected. All files match the baseline.")
        else:
            if added_files:
                print("Added files:")
                for f in added_files:
                    print(f"  + {f}")
            if removed_files:
                print("Removed files:")
                for f in removed_files:
                    print(f"  - {f}")
            if modified_files:
                print("Modified files:")
                for f in modified_files:
                    print(f"  * {f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="File Integrity Checker")
    subparsers = parser.add_subparsers(dest="command")

    # baseline mode
    baseline_parser = subparsers.add_parser("create_baseline")
    baseline_parser.add_argument("folder", help="Path to the folder to baseline")

    # check mode (to be implemented)
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("folder", help="Path to the folder to check")

    args = parser.parse_args()

    if args.command == "create_baseline":
        create_baseline(args.folder)
    elif args.command == "check":
        check(args.folder)
    else:
        parser.print_help()


