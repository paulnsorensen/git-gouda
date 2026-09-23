# Contributing to git-gouda

This repository ships repository-only agent skills. Keep changes focused on repository setup, protection, maintenance, and shared GitHub policy.

## Set up locally

    git clone https://github.com/paulnsorensen/git-gouda.git
    cd git-gouda
    just build

Install the tools listed in justfile before running the gate.

## Add or change a skill

Skills live at skills/name/SKILL.md. Keep bundled assets, references, and evals beside the skill. Add the skill to the Skills table in README.md.

Run these commands before opening a pull request:

    just build
    just ci

Add positive, negative-scope, and safety-guardrail evals. Keep evals as data; the validator does not execute semantic agent evaluations.

## Pull requests

Use a Conventional Commits title. Explain the behavior, verification command, and residual risk. Do not include credentials or machine-local files.

## Security

Report vulnerabilities privately through SECURITY.md. Do not open a public issue for a secret or exploitable defect.

## License

Contributions use the MIT license in LICENSE.
