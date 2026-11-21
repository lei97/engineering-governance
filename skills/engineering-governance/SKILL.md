---
name: engineering-governance
description: Apply transparent engineering governance to software tasks, including source-of-truth YAML, scoped changes, evidence review, and standard, creative, learning, reverse, or repair workflows. Use when planning, modifying, investigating, or verifying repository work.
---

# Engineering Governance

This skill guides engineering activity; the repository's `specifications/` files are the authoritative rules.

## Workflow

1. Identify user intent, authority, repository state, existing changes, and task boundaries.
2. Select mode from `../../specifications/modes.md`: `standard`, `creative`, `learning`, `reverse`, `repair`. Read the matching `references/<mode>.md` only when needed.
3. Apply common invariants from `../../specifications/principles.md` and `../../specifications/change-protocol.md`. Never use modes to bypass authorisation or undo unrelated changes.
4. For truth records, consult `../../specifications/source-of-truth.md` and `../../specifications/yaml-profile.md`. Preserve distinctions between confirmed requirement, observed behavior, and hypothesis.
5. Validate structured records with `python scripts/validate_truth.py <directory>` from this repository root. Validation is necessary but insufficient for semantic correctness.
6. Report changed files, checks run, unresolved risks and required human decisions. If knowledge is incomplete, state the uncertainty explicitly.

## Portability

When installed into another repository, paths pointing outside this skill directory may not resolve. Use the bundled `references/governance-summary.md` for essential invariants, and use upstream `specifications/` only when the governance repository is present. Project-specific truth data remains in the target repository; never infer project authority from this skill alone.
