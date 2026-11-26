"""Reconstruct one experiment packet in a new destination directory."""

import argparse
import difflib
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASE = ROOT / "case"
SHARED_FILES = ("test_dispatch.py", "instructions.md")


def prepare(destination, group, stage, prior=None):
    starter = (CASE / "dispatch.py").read_bytes()
    source = prior.read_bytes() if prior is not None else starter
    destination.mkdir()
    (destination / "dispatch.py").write_bytes(source)
    shutil.copyfile(CASE / f"task-{stage}.md", destination / "task.md")
    for name in SHARED_FILES:
        shutil.copyfile(CASE / name, destination / name)
    shutil.copyfile(ROOT / "trace.py", destination / "trace.py")
    history = {}
    if group == "B":
        history = {path.name: path.read_bytes() for path in sorted((CASE / "history").iterdir())}
        if prior is not None:
            change = difflib.unified_diff(
                starter.decode().splitlines(keepends=True),
                source.decode().splitlines(keepends=True),
                fromfile="a/dispatch.py",
                tofile="b/dispatch.py",
            )
            history["r040-predecessor.diff"] = "".join(change).encode()
        (destination / ".history").mkdir()
        for name, payload in history.items():
            (destination / ".history" / name).write_bytes(payload)
    config = {
        "base_sha256": hashlib.sha256(source).hexdigest(),
        "history": {name: len(payload) for name, payload in history.items()},
    }
    (destination / ".packet.json").write_text(json.dumps(config) + "\n", encoding="utf-8")
    (destination / "trace.jsonl").touch()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=("A", "B"))
    parser.add_argument("stage", type=int, choices=(1, 2))
    parser.add_argument("destination", type=Path)
    parser.add_argument("--prior", type=Path, help="Sealed stage-one dispatch.py for this chain")
    args = parser.parse_args()
    if (args.stage == 2) != (args.prior is not None):
        parser.error("Stage two requires --prior and stage one starts from the frozen fixture.")
    prepare(args.destination, args.group, args.stage, args.prior)


if __name__ == "__main__":
    main()
