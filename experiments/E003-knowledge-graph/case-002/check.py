"""Evaluate the P3-B holdout against a submission on a fresh baseline copy."""

import argparse
from dataclasses import dataclass
import json
import re
import shutil
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


@dataclass(frozen=True)
class Batch:
    files: dict[str, str]
    yaml_count: int
    rejected: tuple[str, ...] = ()
    diagnostics: tuple[tuple[str, str], ...] = ()


BATCHES = {
    "yaml-only": Batch(
        {
            "folder.yml/SRC-001.yaml": "valid/SRC-001.yaml",
            "notes.txt": "valid/SRC-002.yaml",
        },
        1,
    ),
    "mixed": Batch(
        {
            "SRC-001.yaml": "valid/SRC-001.yaml",
            "north/SRC-002.yml": "valid/SRC-002.yaml",
            "south/deeper/SRC-002.yml": "valid/SRC-002.yaml",
        },
        1,
        ("north/SRC-002.yml", "south/deeper/SRC-002.yml"),
    ),
    "yml-only": Batch(
        {"children/SRC-001.yml": "valid/SRC-001.yaml"},
        0,
        ("children/SRC-001.yml",),
    ),
    "continue-validation": Batch(
        {
            "first/SRC-002.yml": "valid/SRC-002.yaml",
            "later/REQ-004.yaml": "invalid/dangling-reference.yaml",
        },
        1,
        ("first/SRC-002.yml",),
        (("later/REQ-004.yaml", "missing origin SRC-999"),),
    ),
    "exclude-rejected-source-from-index": Batch(
        {
            "source/SRC-001.yml": "valid/SRC-001.yaml",
            "REQ-001.yaml": "valid/REQ-001.yaml",
            "ART-001.yaml": "valid/ART-001.yaml",
            "TEST-001.yaml": "valid/TEST-001.yaml",
        },
        3,
        ("source/SRC-001.yml",),
        (("REQ-001.yaml", "missing origin SRC-001"),),
    ),
}


def contains_path(line, relative_path):
    return re.search(rf"(?:^|[/\s'\"`]){re.escape(relative_path)}(?=$|[:\s'\"`\]])", line)


def run_batch(repo, fixtures, parent, name, batch):
    directory = parent / name
    for relative_path, fixture in batch.files.items():
        path = directory / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(fixtures / fixture, path)

    process = subprocess.run(
        [sys.executable, "-B", "scripts/validate_truth.py", str(directory)],
        cwd=repo, capture_output=True, text=True, timeout=30,
    )
    expected_failure = bool(batch.rejected or batch.diagnostics)
    status = "FAIL" if expected_failure else "PASS"
    checks = {
        "exit": process.returncode == int(expected_failure),
        "yaml_count": re.search(
            rf"^{status}: {batch.yaml_count} YAML records; \d+ errors$",
            process.stdout, re.MULTILINE,
        ) is not None,
    }
    error_lines = process.stderr.splitlines()
    for relative_path in batch.rejected:
        checks[f"reject:{relative_path}"] = any(
            contains_path(line, relative_path) and ".yaml" in line
            for line in error_lines
        )
    for relative_path, diagnostic in batch.diagnostics:
        checks[f"validate:{relative_path}"] = any(
            contains_path(line, relative_path) and diagnostic in line for line in error_lines
        )
    if not expected_failure:
        checks["no_errors"] = not error_lines
    return {
        "checks": checks,
        "exit": process.returncode,
        "stdout": process.stdout.replace(str(parent) + "/", ""),
        "stderr": process.stderr.replace(str(parent) + "/", ""),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("fixtures", type=Path, help="examples/ in the unmodified baseline")
    args = parser.parse_args()
    with TemporaryDirectory(prefix="eg-p3b-check-") as temp:
        batches = {
            name: run_batch(args.repo, args.fixtures, Path(temp), name, batch)
            for name, batch in BATCHES.items()
        }
    regression = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=args.repo, capture_output=True, text=True, timeout=60,
    )
    passed = regression.returncode == 0 and all(
        all(batch["checks"].values()) for batch in batches.values()
    )
    print(json.dumps({
        "passed": passed,
        "batches": batches,
        "regression": {
            "exit": regression.returncode, "stdout": regression.stdout, "stderr": regression.stderr,
        },
    }, indent=2, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
