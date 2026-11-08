# Conventional Commits and squash-merge titles

## Conventional Commits 1.0.0

Source: [conventionalcommits.org/en/v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
(verified 200).

A commit or PR title has the shape:

```
<type>[optional scope][optional !]: <description>
```

Common types (from the [conventional-commit-types](https://github.com/commitizen/conventional-commit-types)
convention the action defaults to):

| Type | Meaning |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Neither a fix nor a feature |
| `perf` | A performance improvement |
| `test` | Adding or correcting tests |
| `build` | Build system or dependencies |
| `ci` | CI configuration |
| `chore` | Other changes that do not modify source or tests |

A breaking change appends `!` after the type/scope, before the colon, for
example `refactor!: drop support for Node.js 12`. Conventional Commits also
allows a `BREAKING CHANGE:` footer, but a PR title has only one line, so the
`!` marker is the only way to signal a breaking change in the title itself.

## Why the PR title becomes the commit subject

Source: [docs.github.com – Configuring commit squashing for pull requests](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/configuring-commit-squashing-for-pull-requests)
(verified 200).

When a repository's squash-merge commit title default is set to "Default to
PR title" (the API value `squash_merge_commit_title: PR_TITLE`), merging a
pull request writes the PR title as the subject line of the single squash
commit on the default branch. From that point the title is permanent history
— it shows up in `git log --oneline`, in `git blame`, and in any tool that
reads commit subjects (including auto-generated release notes). A CI check
on the title is the only gate before that happens, since GitHub does not
validate title format on its own.

## amannn/action-semantic-pull-request

Source: [github.com/amannn/action-semantic-pull-request](https://github.com/amannn/action-semantic-pull-request#readme)
(verified 200), pinned in this repository's own `.github/workflows/validate.yml`
at `48f256284bd46cdaab1048c3721360e808335d50` (`v6.1.1`).

The action validates the PR title against the Conventional Commits header
shape and reports a failing check when it does not match. Configuration
options used by [`assets/pr-title.yml`](../assets/pr-title.yml):

- `types` — newline-delimited allow-list of types (regex, anchored)
- `scopes` — newline-delimited allow-list of scopes (regex, anchored)
- `requireScope` — whether a scope is mandatory; this skill defaults it to
  `false`
- `subjectPattern` — an additional regex the description must match, for
  example `^(?![A-Z]).+$` to reject a leading capital letter
- `ignoreLabels` — newline-delimited PR labels that skip validation entirely

The action needs only `pull-requests: read` unless the WIP-prefix feature is
used, which the template in this skill does not enable.

## Refreshing the pin

To move to a newer release, resolve the new tag to a commit SHA and update
both this reference and [`assets/pr-title.yml`](../assets/pr-title.yml):

```bash
gh api repos/amannn/action-semantic-pull-request/git/refs/tags/vX.Y.Z --jq '.object.sha'
```
