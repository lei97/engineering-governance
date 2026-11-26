"""Run the frozen behavioral checks against one dispatch.py submission."""

import argparse
import importlib.util
import json
import sys
from pathlib import Path


def load_source(source):
    spec = importlib.util.spec_from_file_location("dispatch", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def cases(module, stage):
    event = module.Event
    east = event(5, "ship", "P1", "east")
    audit = event(8, "note", "P3")
    west = event(19, "ship", "P2", "west")
    void = event(26, "void", "P1")
    late = event(33, "ship", "P3", "east")
    batch = [late, west, audit, void, east]
    unscoped = [east, west, void, late]
    eastbound = [east, void, late]
    westbound = [west, void]

    def receiver_states():
        return [
            sorted(module.active_movements(depot, module.export(iter(batch), depot=depot)))
            for depot in ("east", "west")
        ]

    def resume_empty_page():
        first = module.page(iter(batch), after=5, limit=2, depot="east")
        second = module.page(iter(batch), after=first[1], limit=2, depot="east")
        return first, second

    def drain(depot):
        output = []
        after = 0
        for _ in range(len(batch) + 1):
            emitted, checkpoint = module.page(iter(batch), after=after, limit=1, depot=depot)
            if checkpoint == after:
                return output, checkpoint
            output.extend(emitted)
            after = checkpoint
        raise AssertionError("checkpoint did not stabilize after draining the input")

    if stage == 1:
        return [
            ("unscoped_export", lambda: module.export(iter(batch)), unscoped),
            ("scoped_shipment", lambda: module.export(iter([west, audit, east]), depot="east"), [east]),
            ("depotless_void", lambda: [module.export(iter([void]), depot=d) for d in ("east", "west")], [[void], [void]]),
            ("receiver_reconciliation", receiver_states, [["P3"], ["P2"]]),
        ]
    return [
        ("raw_scan_limit", lambda: module.page(iter(batch), after=0, limit=2, depot="east"), ([east], 8)),
        ("empty_page_advances", resume_empty_page, (([], 19), ([void, late], 33))),
        ("exhausted_checkpoint", lambda: module.page(iter(batch), after=90, limit=2), ([], 90)),
        ("paged_stream_continuity", lambda: [drain(d) for d in (None, "east", "west")], [(unscoped, 33), (eastbound, 33), (westbound, 33)]),
        ("scoped_export_retained", lambda: module.export(iter(batch), depot="east"), eastbound),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", type=int, choices=(1, 2))
    parser.add_argument("source", type=Path)
    args = parser.parse_args()

    try:
        checks = cases(load_source(args.source), args.stage)
    except Exception as exc:
        print(json.dumps({"load_error": f"{type(exc).__name__}: {exc}"}))
        return 1

    results = {}
    for name, run, expected in checks:
        try:
            actual = run()
            passed = actual == expected
            results[name] = {"passed": passed}
            if not passed:
                results[name].update(expected=repr(expected), actual=repr(actual))
        except Exception as exc:
            results[name] = {"passed": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(results, ensure_ascii=False))
    return int(any(not check["passed"] for check in results.values()))


if __name__ == "__main__":
    sys.exit(main())
