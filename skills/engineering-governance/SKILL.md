---
name: engineering-governance
description: Apply transparent engineering governance to software tasks, including source-of-truth YAML, scoped changes, evidence review, and standard, creative, learning, reverse, or repair workflows. Use when planning, modifying, investigating, or verifying repository work.
---

# Engineering Governance

The Engineering Governance distribution's `specifications/` files are the authoritative governance rules. Project requirements and authorization come from the target project.

## Workflow

1. Identify user intent, authority, repository state, existing changes, and task boundaries.
2. Locate the governance root as described below. Select `standard`, `creative`, `learning`, `reverse`, or `repair` using `specifications/modes.md` there. Read the matching `references/<mode>.md` as needed.
3. Apply `specifications/principles.md` and `specifications/change-protocol.md` from that root, including the interpretation check for work based on confirmed requirements.
4. For truth records, consult `specifications/source-of-truth.md` and `specifications/yaml-profile.md` at that root. With the dependencies installed, run `python3 "<governance-root>/scripts/validate_truth.py" "<record-directory>"`, substituting the resolved governance root and the target project's record directory. Verify the intended meaning separately from structural validation.
5. Report changed files, checks run, remaining uncertainty, and required human decisions.

## Portability

Use the Engineering Governance root explicitly supplied for the task, or `ENGINEERING_GOVERNANCE_ROOT` if set. Otherwise, check `../..` relative to the directory containing the real `SKILL.md` file. Use that candidate when it has the distribution layout, including `specifications/modes.md`, `schemas/knowledge.schema.json`, and `scripts/validate_truth.py`. Treat the target project's own specifications as project material.

When the governance specifications are unavailable, use `references/governance-summary.md` and report that you used the portable summary. Structural validation requires the validator, its Schema, and its Python dependencies from a full installation. Report when the check could not run.
