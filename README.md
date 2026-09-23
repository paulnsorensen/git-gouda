# git-gouda

Repository-only agent skills for Git repository setup, protection, maintenance, and shared GitHub policy.

## Scope

This repository contains portable skills that operate on repository files, local repository tooling, and explicitly authorized GitHub repository policy. It does not contain personal machine setup, agent orchestration, or general-purpose application skills.
See [PROVENANCE.md](PROVENANCE.md) for import sources and intentional adaptations.

## Skills

| Skill | Purpose |
| --- | --- |
| [prek](skills/prek/SKILL.md) | Configure prek hooks for a repository. |
| [oss-hygiene](skills/oss-hygiene/SKILL.md) | Add community health and supply-chain hygiene files. |
| [gh-bootstrap](skills/gh-bootstrap/SKILL.md) | Configure merge defaults, rulesets, release notes, and optional release automation. |
| [safe-settings](skills/safe-settings/SKILL.md) | Scaffold shared GitHub settings-as-code with safe-settings. |
| [config-review-bot](skills/config-review-bot/SKILL.md) | Configure and audit CodeRabbit repository review policy. |

Each skill includes its complete references, templates, and evals. The validators reject missing resources and catalog drift.

## Install

Install one skill into the current repository with the GitHub CLI:

    gh skill install paulnsorensen/git-gouda config-review-bot --agent codex --scope project

Install from a local checkout when the repository is not published:

    gh skill install . config-review-bot --from-local --agent codex --scope project

Replace config-review-bot with any catalog name. Run just ci only when developing this catalog checkout; remote installation does not require the catalog justfile.

## Development

- just build formats and validates the repository.
- just ci runs the same checks without changing files.
- prek run --all-files runs local hooks.
