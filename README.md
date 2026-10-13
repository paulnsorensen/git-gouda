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
| [release](skills/release/SKILL.md) | Decide the next semantic version, draft release notes, tag, and publish a GitHub release. |
| [justfile](skills/justfile/SKILL.md) | Create or migrate a justfile with ecosystem-aware recipes. |
| [ci-optimize](skills/ci-optimize/SKILL.md) | Optimize GitHub Actions wait time with measured evidence. |
| [build-optimize](skills/build-optimize/SKILL.md) | Optimize local build, test, and check commands with measured wall-time evidence. |
| [github-copilot-repo-instructions](skills/github-copilot-repo-instructions/SKILL.md) | Add or audit Copilot repository instructions and code review rules. |
| [codeowners](skills/codeowners/SKILL.md) | Author, validate, and enforce a CODEOWNERS file. |
| [actions-pinning](skills/actions-pinning/SKILL.md) | Pin GitHub Actions to commit SHAs and enforce pinning policy. |
| [pr-title-lint](skills/pr-title-lint/SKILL.md) | Enforce Conventional Commits pull request titles in CI. |
| [labels-as-code](skills/labels-as-code/SKILL.md) | Manage repository labels and PR auto-labeling as code. |
| [repo-attributes](skills/repo-attributes/SKILL.md) | Configure .gitattributes, .editorconfig, and .gitignore for a repository. |
| [branch-cleanup](skills/branch-cleanup/SKILL.md) | Configure branch deletion on merge and report stale branches. |
| [agents-md](skills/agents-md/SKILL.md) | Create, audit, and trim AGENTS.md and its harness mirrors. |
| [repo-audit](skills/repo-audit/SKILL.md) | Run a read-only audit of every catalog skill's checks and report gaps. |

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
