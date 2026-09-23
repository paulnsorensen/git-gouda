# Label scheme and action verification

Reference detail for the default label set, the release-notes mapping, and how the two GitHub Actions used by this skill were verified.

## Default label set

| Label | Purpose | Source |
|---|---|---|
| `type/feat`, `type/fix`, `type/docs`, `type/style`, `type/refactor`, `type/perf`, `type/test`, `type/build`, `type/ci`, `type/chore`, `type/revert` | One per Conventional Commits type | `/pr-title-lint` checks these same type names in the PR title |
| `priority/critical`, `priority/high`, `priority/medium`, `priority/low` | Triage priority | local convention |
| `status/blocked`, `status/in-progress`, `status/needs-review` | Triage state | local convention |
| `good first issue`, `help wanted` | Community-standards labels | GitHub's own defaults |
| `dependencies` | Dependency-bump PRs | GitHub's own default (also Dependabot's label) |
| `breaking` | Breaking change | local convention |

## Mapping to `/gh-bootstrap`'s `.github/release.yml`

`/gh-bootstrap` ships `.github/release.yml` with categories keyed on bare label names, not the `type/` prefix:

| `release.yml` category | Its label keys | This skill's nearest label |
|---|---|---|
| Breaking changes | `breaking-change`, `breaking` | `breaking` (already matches) |
| Features | `enhancement`, `feature` | `type/feat` |
| Fixes | `bug`, `bugfix`, `fix` | `type/fix` |
| Documentation | `documentation`, `docs` | `type/docs` |
| Dependencies | `dependencies` | `dependencies` (already matches) |
| Internal | `chore`, `refactor`, `ci`, `build`, `test` | `type/chore`, `type/refactor`, `type/ci`, `type/build`, `type/test` |

Only `breaking` and `dependencies` share a spelling with `release.yml` out of the box. Two ways to close the gap, both edits to `/gh-bootstrap`'s file rather than this skill's:

1. Add the `type/*` names as extra entries under each `release.yml` category's `labels:` list.
2. Apply both label spellings to affected PRs (e.g. `type/feat` and `enhancement`) until the categories are updated.

This skill documents the mapping; it does not edit `release.yml` on its own — that file belongs to `/gh-bootstrap`.

## Verifying the sync action

Two maintained actions sync a YAML file to a repository's labels: `crazy-max/ghaction-github-labeler` and `EndBug/label-sync`. Verify either before pinning it, and re-verify before reusing a SHA from an older run:

```bash
gh api repos/crazy-max/ghaction-github-labeler --jq '{archived, pushed_at, stargazers_count}'
LATEST=$(gh api repos/crazy-max/ghaction-github-labeler/releases/latest --jq '.tag_name')
gh api repos/crazy-max/ghaction-github-labeler/git/ref/tags/"$LATEST" --jq '.object'
# If .object.type is "tag" (an annotated tag), dereference it once more:
#   gh api repos/<owner>/<repo>/git/tags/<sha> --jq '.object.sha'
```

Verified for this skill on 2026-09-23: `crazy-max/ghaction-github-labeler` at `v6.0.0` (`548a7c3603594ec17c819e1239f281a3b801ab4d`, lightweight tag pointing directly at the commit) — not archived, pushed within the week, 172 stars. `EndBug/label-sync` at `v2.3.3` was also verified as a viable alternative (not archived, active); its tag is annotated, so the object it points to needs one extra dereference to reach the commit SHA. `crazy-max/ghaction-github-labeler` is pinned in `assets/labels-sync.yml` for its more recent push activity; re-run the verification above before trusting either SHA in a future update.

## Verifying `actions/labeler`

```bash
LATEST=$(gh api repos/actions/labeler/releases/latest --jq '.tag_name')
gh api repos/actions/labeler/git/ref/tags/"$LATEST" --jq '.object.sha'
```

Verified for this skill on 2026-09-23: `v7.0.0` at `bf12e9b00b37c5c0ca2b87b79b2daf7891dbda13`, pinned in `assets/pr-labeler.yml`.

## Citations

- GitHub Docs, "Managing labels": <https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels>
- `gh label` manual: <https://cli.github.com/manual/gh_label>
- `actions/labeler` README: <https://github.com/actions/labeler#readme>
- `crazy-max/ghaction-github-labeler` README: <https://github.com/crazy-max/ghaction-github-labeler#readme>
