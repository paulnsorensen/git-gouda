# repo-audit checks

One row per check. "Inspects" names the file, directory, or API endpoint the script reads. Citations point to the GitHub REST API docs for checks that call `gh api`.

| Check | Inspects | Citation |
| --- | --- | --- |
| prek | `prek.toml`, `.pre-commit-config.yaml` | — |
| oss-hygiene | `LICENSE`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/dependabot.yml`, `.github/workflows/*.yml` (scorecard, codeql, dependency-review name matches) | — |
| gh-bootstrap | `.github/release.yml`; with `--github`, `GET /repos/{owner}/{repo}` and `GET /repos/{owner}/{repo}/rulesets` | <https://docs.github.com/en/rest/repos/repos#get-a-repository>, <https://docs.github.com/en/rest/repos/rules#get-all-repository-rulesets> |
| safe-settings | `.github/settings.yml` | — |
| config-review-bot | `.coderabbit.yaml` | — |
| release | `git tag --list`, `CHANGELOG.md` | — |
| justfile | `justfile`, `Justfile` | — |
| ci-optimize | `.github/workflows/*.yml` for a `concurrency:` key | — |
| build-optimize | not computable statically; always `skipped` | — |
| github-copilot-repo-instructions | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md` | — |
| codeowners | `CODEOWNERS`, `docs/CODEOWNERS`, `.github/CODEOWNERS`; with `--github`, `GET /repos/{owner}/{repo}/codeowners/errors` | <https://docs.github.com/en/rest/repos/repos#list-codeowners-errors> |
| actions-pinning | `.github/workflows/*.yml`, regex match on `uses:` lines against a 40-hex-character SHA (no YAML parser) | — |
| pr-title-lint | `.github/workflows/*.yml`, text match for `action-semantic-pull-request` or `commitlint` | — |
| labels-as-code | `.github/labels.yml`, `.github/labeler.yml` | — |
| repo-attributes | `.gitattributes`, `.editorconfig`, `.gitignore` | — |
| branch-cleanup | with `--github`, `GET /repos/{owner}/{repo}` (`delete_branch_on_merge`) | <https://docs.github.com/en/rest/repos/repos#get-a-repository> |
| agents-md | `AGENTS.md` file size and line count | — |
