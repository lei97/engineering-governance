"""Replay P4 evidence and construct isolated distribution packets from frozen Git content."""

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory

import yaml


CASE = Path(__file__).resolve().parent
ROOT = CASE.parents[2]
REVISIONS = {
    "old": "9c38156fa8c277507ab30529af6d0480e8cbf833",
    "new": "83a21206ebf9e1addf6aa115a9f3c6427c2a40bf",
}
SOURCE_PATHS = ("scripts", "schemas", "specifications", "tests", "examples")
COMMON = ("task.md", "history.md", "evidence.json")
EXTRAS = {"A": (), "B": ("summary.md",), "C": ("graph.md",)}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def file_manifest(directory):
    return {
        path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*")) if path.is_file()
    }


def snapshot(version, directory):
    directory.mkdir(parents=True)
    data = git("archive", REVISIONS[version], *SOURCE_PATHS)
    with tarfile.open(fileobj=BytesIO(data)) as archive:
        archive.extractall(directory, filter="data")


def fixtures():
    def load(name):
        return yaml.safe_load(git("show", f"{REVISIONS['old']}:examples/{name}"))

    source = load("valid/SRC-001.yaml")
    unrelated = load("invalid/dangling-reference.yaml")
    dependent = load("invalid/missing-acceptance.yaml")
    dependent["acceptance"] = ["测试来源仍可解析。"]
    return {
        "1": {"REQ-004.yaml": unrelated},
        "2": {"a/SRC-001.yaml": dict(source, relations="REQ-002"), "z/REQ-004.yaml": unrelated},
        "3": {"a/SRC-001.yaml": dict(source, kind=["source"]),
              "b/REQ-005.yaml": dependent, "z/REQ-004.yaml": unrelated},
        "4": {"b/REQ-005.yaml": dependent, "z/REQ-004.yaml": unrelated},
        "5": {"a/SRC-001.yaml": dict(source, relations=[]), "z/REQ-004.yaml": unrelated},
        "6": {"a/SRC-001.yaml": dict(source, relations=["REQ-002"]), "z/REQ-004.yaml": unrelated},
        "7": {"a/SRC-001.yaml": dict(source, id={"bad": "SRC-001"}, origin="SRC-998"),
              "b/REQ-005.yaml": dependent, "z/REQ-004.yaml": unrelated},
    }


def replay(root):
    root = root.resolve()
    for version in REVISIONS:
        snapshot(version, root / version)
    evidence = {"revisions": REVISIONS, "batches": {}}
    for label, records in fixtures().items():
        directory = root / "batches" / label
        inputs = {path: yaml.safe_dump(record, allow_unicode=True) for path, record in records.items()}
        for path, content in inputs.items():
            file = directory / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(content, encoding="utf-8")
        results = {}
        for version in REVISIONS:
            source = root / version
            run = subprocess.run(
                [sys.executable, "-B", "scripts/validate_truth.py", str(directory)],
                cwd=source, capture_output=True, text=True, timeout=30,
            )
            results[version] = {
                "exit_code": run.returncode,
                "stdout": run.stdout,
                "stderr": run.stderr.replace(str(directory) + "/", "").replace(str(source) + "/", ""),
            }
        evidence["batches"][label] = {"inputs": inputs, "results": results}
    return evidence


def packet(group, destination):
    destination.mkdir(parents=True)
    for filename in (*COMMON, *EXTRAS[group]):
        shutil.copyfile(CASE / filename, destination / filename)
    for version in REVISIONS:
        snapshot(version, destination / "source" / version)
    return file_manifest(destination)


def verify_evidence(replayed):
    stored = json.loads((CASE / "evidence.json").read_text(encoding="utf-8"))
    if stored != replayed:
        raise ValueError("replayed CLI evidence differs from evidence.json")
    gold = json.loads((CASE / "gold.json").read_text(encoding="utf-8"))
    for label, batch in replayed["batches"].items():
        for version, run in batch["results"].items():
            expected = gold["batches"][label][version]
            stderr = run["stderr"].splitlines()
            exception = stderr[-1] if stderr and stderr[0].startswith("Traceback") else None
            summary = run["stdout"].strip() or None
            diagnostics = [line.removeprefix("ERROR: ") for line in stderr if line.startswith("ERROR: ")]
            matches = (
                run["exit_code"] == 1
                and exception == expected["uncaught_exception"]
                and summary == expected["summary"]
                and diagnostics == expected["diagnostics"]
                and (exception is None and summary is not None) == expected["batch_completed"]
            )
            if not matches:
                raise ValueError(f"batch {label}, {version}: CLI evidence differs from gold.json")
    return {"batches": len(replayed["batches"]), "replayed_versions": len(REVISIONS)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--packet", choices=EXTRAS)
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    if args.packet:
        if args.destination is None:
            parser.error("--packet requires --destination")
        result = packet(args.packet, args.destination)
    else:
        with TemporaryDirectory(prefix="eg-p4-evidence-") as temp:
            result = replay(Path(temp))
        if args.verify:
            result = verify_evidence(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
