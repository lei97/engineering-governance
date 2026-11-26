"""Serve the packet's history budget and timestamp forecasts and deliveries."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

PACKET = Path(__file__).resolve().parent
LEDGER = PACKET / "trace.jsonl"
MAX_READS = 2
MAX_BYTES = 2048


def digest(name):
    return hashlib.sha256((PACKET / name).read_bytes()).hexdigest()


def log(action, **details):
    with LEDGER.open("a", encoding="utf-8") as output:
        print(json.dumps({"action": action, "utc_ns": time.time_ns(), **details}), file=output)


def main():
    command, *arguments = sys.argv[1:]
    config = json.loads((PACKET / ".packet.json").read_text(encoding="utf-8"))
    entries = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines()]
    actions = {entry["action"] for entry in entries}
    history = config["history"]

    if command == "launch" and not actions:
        log("launch")
    elif command == "index":
        data = "\n".join(f"{name}\t{size}" for name, size in history.items())
        payload = (data + "\n" if data else "(no history)\n").encode()
        log("index", bytes=len(payload))
        sys.stdout.buffer.write(payload)
    elif command == "read" and len(arguments) == 1:
        name = arguments[0]
        previous = [entry for entry in entries if entry["action"] == "read"]
        if name not in history or len(previous) >= MAX_READS:
            log("rejected_read", name=name, reason="unknown file or read limit")
            sys.exit("Unknown file or read budget exhausted.")
        payload = (PACKET / ".history" / name).read_bytes()
        if sum(entry["bytes"] for entry in previous) + len(payload) > MAX_BYTES:
            log("rejected_read", name=name, reason="byte limit")
            sys.exit("History byte budget exhausted.")
        log("read", name=name, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
        sys.stdout.buffer.write(payload)
    elif command == "forecast" and actions.isdisjoint({"forecast", "test", "finish"}):
        source = digest("dispatch.py")
        if source != config["base_sha256"]:
            sys.exit("Forecast requires unchanged starter source.")
        log("forecast", sha256=digest("forecast.md"), source_sha256=source)
        print("Forecast sealed.")
    elif command == "test" and "forecast" in actions and "finish" not in actions:
        result = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "-v", "test_dispatch"],
            cwd=PACKET,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout + result.stderr
        log("test", exit=result.returncode, output=output, source_sha256=digest("dispatch.py"))
        print(output, end="")
        return result.returncode
    elif command == "finish" and {"forecast", "test"} <= actions and "finish" not in actions:
        forecast = next(entry for entry in entries if entry["action"] == "forecast")
        tested = next(entry for entry in reversed(entries) if entry["action"] == "test")
        source = digest("dispatch.py")
        if forecast["sha256"] != digest("forecast.md") or tested["source_sha256"] != source:
            sys.exit("Preserve the forecast and run the public tests on the final source.")
        log("finish", source_sha256=source, report_sha256=digest("report.md"))
        print("Delivery sealed.")
    else:
        sys.exit("Unknown command or invalid step order.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
