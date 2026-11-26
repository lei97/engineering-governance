"""Calibrate the checker or verify the archived deliveries with Python 3.12."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from prepare import CASE, ROOT, prepare

RUN = ROOT / "run-01"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha(path.read_bytes())


def evaluate(stage, source):
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        (work / "dispatch.py").write_text(source, encoding="utf-8")
        shutil.copyfile(CASE / "test_dispatch.py", work / "test_dispatch.py")
        public = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "-v", "test_dispatch"],
            cwd=work, capture_output=True, text=True, timeout=30,
        )
        held = subprocess.run(
            [sys.executable, "-B", str(ROOT / "holdout.py"), str(stage), "dispatch.py"],
            cwd=work, capture_output=True, text=True, timeout=30,
        )
        return {
            "public_exit": public.returncode,
            "holdout_exit": held.returncode,
            "checks": json.loads(held.stdout),
        }


def calibrate():
    starter = (CASE / "dispatch.py").read_text(encoding="utf-8")
    routed = starter.replace(
        "def export(events: Iterable[Event])",
        "def export(events: Iterable[Event], *, depot: str | None = None)",
    ).replace(
        'if event.kind != "note"]',
        'if event.kind != "note" and (depot is None or event.kind == "void" or event.depot == depot)]',
    )
    equality_only = routed.replace(' or event.kind == "void"', "")
    paged = routed + '''


def page(
    events: Iterable[Event], *, after: int, limit: int, depot: str | None = None,
) -> tuple[list[Event], int]:
    scanned = sorted((event for event in events if event.seq > after), key=lambda event: event.seq)[:limit]
    emitted = export(scanned, depot=depot)
    return emitted, scanned[-1].seq if scanned else after
'''
    delivered_checkpoint = paged.replace("scanned[-1].seq if scanned", "emitted[-1].seq if emitted")
    controls = [
        (1, "before_change", starter, {"scoped_shipment", "depotless_void", "receiver_reconciliation"}),
        (1, "equality_only", equality_only, {"depotless_void", "receiver_reconciliation"}),
        (1, "valid_routing", routed, set()),
        (2, "delivered_checkpoint", delivered_checkpoint, {"raw_scan_limit", "empty_page_advances", "paged_stream_continuity"}),
        (2, "valid_paging", paged, set()),
    ]
    results = {}
    for stage, label, source, expected_failures in controls:
        results[label] = evaluate(stage, source)
        result = results[label]
        failures = {name for name, check in result["checks"].items() if not check["passed"]}
        if result["public_exit"] or failures != expected_failures:
            raise ValueError(f"Calibration mismatch for {label}: {result}")
    return results


def validate_archive():
    frozen = json.loads((RUN / "freeze.json").read_text(encoding="utf-8"))
    for name, expected in frozen["files"].items():
        if sha_file(ROOT / name) != expected:
            raise ValueError(f"Changed input or checker: {name}")
    if calibrate() != frozen["calibration"]:
        raise ValueError("Calibration results changed.")

    deliveries = json.loads((RUN / "submissions.json").read_text(encoding="utf-8"))
    expected_pairs = {(chain, stage) for chain in frozen["groups"] for stage in (1, 2)}
    if len(deliveries) != len(expected_pairs) or {(row["chain"], row["stage"]) for row in deliveries} != expected_pairs:
        raise ValueError("Missing, unexpected or duplicate deliveries.")

    prior = {}
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        for row in sorted(deliveries, key=lambda entry: (entry["stage"], entry["chain"])):
            chain, stage = row["chain"], row["stage"]
            packet = work / f"{stage}-{chain}"
            group = frozen["groups"][chain]
            prepare(packet, group, stage, prior.get(chain))
            validate_packet(packet, row)
            result = evaluate(stage, row["source"])
            if result != row["evaluation"]:
                raise ValueError(f"Score changed for {stage}-{chain}.")
            if stage == 1:
                prior[chain] = work / f"{chain}.py"
                prior[chain].write_text(row["source"], encoding="utf-8")
            passed = sum(check["passed"] for check in result["checks"].values())
            print(f"T{stage} {chain} ({group}): {passed}/{len(result['checks'])} holdout checks, public exit {result['public_exit']}")


def validate_packet(packet, row):
    hashes = {
        path.relative_to(packet).as_posix(): sha_file(path)
        for path in sorted(packet.rglob("*"))
        if path.is_file()
    }
    if hashes != row["packet_sha256"]:
        raise ValueError(f"Packet reconstruction mismatch for T{row['stage']} {row['chain']}.")
    events = row["trace"]
    for action in ("launch", "forecast", "finish"):
        if sum(event["action"] == action for event in events) != 1:
            raise ValueError(f"Missing or repeated {action}.")
    forecast = next(event for event in events if event["action"] == "forecast")
    finish = events[-1]
    source_sha = sha(row["source"].encode())
    tests = [event for event in events if event["action"] == "test"]
    times = [event["utc_ns"] for event in events]
    if (
        events[0]["action"] != "launch" or times != sorted(times)
        or not tests or not forecast["utc_ns"] <= tests[0]["utc_ns"] <= finish["utc_ns"]
        or forecast["sha256"] != sha(row["forecast"].encode())
        or forecast["source_sha256"] != hashes["dispatch.py"]
        or finish["action"] != "finish" or finish["source_sha256"] != source_sha
        or tests[-1]["source_sha256"] != source_sha
        or finish["report_sha256"] != sha(row["report"].encode())
    ):
        raise ValueError(f"Inconsistent delivery trace for T{row['stage']} {row['chain']}.")

    reads = [event for event in events if event["action"] == "read"]
    if len(reads) > 2 or sum(event["bytes"] for event in reads) > 2048:
        raise ValueError("History budget exceeded.")
    for read in reads:
        name = f".history/{read['name']}"
        if hashes.get(name) != read["sha256"] or (packet / name).stat().st_size != read["bytes"]:
            raise ValueError(f"History read mismatch: {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calibrate", action="store_true")
    args = parser.parse_args()
    if args.calibrate:
        print(json.dumps(calibrate(), indent=2, ensure_ascii=False))
    else:
        validate_archive()


if __name__ == "__main__":
    main()
