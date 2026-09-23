# Agent Instructions for git-gouda

This document guides agents and automation working in this repository.

## Quality gates

- just build formats Markdown and YAML, then runs every validator and test.
- just ci runs the same checks without autofixes.
- prek run --all-files runs the local hook set.

Run just ci before handoff. Do not claim a gate passed when it did not run.

## Repository scope

The README.md skill table is the catalog source of truth. Keep exactly one SKILL.md at skills/name/SKILL.md for each catalog entry.

Skills must remain repository-only. Do not add personal machine setup, agent orchestration, or unrelated application workflows.

## Development notes

- Use Python 3.12 and the standard library where practical.
- Keep every skill self-contained.
- Add evals for positive behavior, negative scope, and safety guardrails.
- Keep source provenance in the skill directory or catalog.
- Use Conventional Commits.
