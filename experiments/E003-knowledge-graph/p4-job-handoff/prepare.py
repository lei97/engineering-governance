"""Render equal-content P4 materials and build intentionally scoped packets."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil


CASE = Path(__file__).resolve().parent
COMMON = ("task.md", "sources.md")
EXTRA = {"A": None, "B": "summary.md", "C": "graph.md"}


def render(claims):
    summary = ["# 历史交接摘要", ""]
    nodes = {}
    edges = []
    for claim in claims:
        subject = claim["subject"]
        target = claim["object"]
        scope = claim["scope"]
        status = claim["status"]
        source = claim["source"]
        relation = claim["relation"]
        identity = claim["id"]
        summary.append(f"- **{identity}** {subject}{relation}{target}。范围：{scope}。状态：{status}。证据：{source}。")
        for value in (subject, target):
            nodes.setdefault(value, f"N{len(nodes) + 1}")
        edges.append(f"| {identity} | {nodes[subject]} | {relation} | {nodes[target]} | {scope} | {status} | {source} |")
    graph = ["# 历史交接关系图", "", "边从源节点指向目标节点。", "",
             "| 节点 | 含义 |", "| --- | --- |"]
    graph.extend(f"| {node} | {label} |" for label, node in nodes.items())
    graph.extend(["", "| ID | 源 | 关系 | 目标 | 范围 | 状态 | 证据 |",
                  "| --- | --- | --- | --- | --- | --- | --- |", *edges])
    return {"summary.md": "\n".join(summary) + "\n", "graph.md": "\n".join(graph) + "\n"}


def packet(group, destination):
    destination.mkdir(parents=True)
    for name in COMMON:
        shutil.copyfile(CASE / name, destination / name)
    if EXTRA[group]:
        shutil.copyfile(CASE / EXTRA[group], destination / "history-note.md")
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(destination.iterdir())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--render", action="store_true")
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--packet", choices=EXTRA)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    if args.packet:
        if args.destination is None:
            parser.error("--packet requires --destination")
        print(json.dumps(packet(args.packet, args.destination), indent=2))
        return
    claims = json.loads((CASE / "claims.json").read_text(encoding="utf-8"))
    for name, content in render(claims).items():
        path = CASE / name
        if args.render:
            path.write_text(content, encoding="utf-8")
        elif path.read_text(encoding="utf-8") != content:
            raise ValueError(f"{name} does not match the historical claims")


if __name__ == "__main__":
    main()
