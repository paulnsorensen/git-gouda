# GitHub Actions pinning policy reference

Primary sources for the claims this skill makes. Re-check dates and
behavior against these pages before citing them in prose, since GitHub
changes defaults over time.

## `uses:` syntax and SHA pinning

- [Workflow syntax: `jobs.<job_id>.steps[*].uses`][uses-syntax] — the
  `owner/repo@ref` and `owner/repo@sha` forms, local `./path` actions,
  and `docker://image` references.
- [Security hardening for GitHub Actions: using third-party actions][hardening]
  — GitHub's own recommendation to pin actions to a full-length commit
  SHA rather than a tag or branch, because a tag can move to a
  different commit.

## Repository and organization allowed-actions policy

- [Managing GitHub Actions settings for a repository][repo-settings] —
  the `allowed_actions` policy (all / local-and-GitHub / selected) and
  the API surface this skill reads with `gh api
  repos/{owner}/{repo}/actions/permissions`.
- [Disabling or limiting GitHub Actions for your organization][org-settings]
  — the organization-level equivalent.
- [GitHub Actions policy now supports blocking and SHA-pinning
  actions][blocking-changelog] (2025-08-15) — allowed-actions policies
  can now block specific actions with a `!action` entry, and can
  require every allowed action to be pinned to a full-length commit
  SHA org-, enterprise-, or repo-wide. Unpinned workflows fail closed
  under that policy.

## Resolving a tag to a commit SHA

- [Get a reference][git-ref] — `GET
  /repos/{owner}/{repo}/git/ref/tags/{tag}` returns the object a tag
  points at. For a lightweight tag the object is the commit directly.
- [Get a tag][git-tag] — `GET /repos/{owner}/{repo}/git/tags/{tag_sha}`
  dereferences an *annotated* tag object to its target commit SHA; a
  ref lookup on an annotated tag returns the tag object SHA, not the
  commit SHA, so this second call is required for annotated tags.
- [Get a commit][get-commit] — `GET
  /repos/{owner}/{repo}/commits/{sha}` is the impostor-commit check:
  it must succeed **against the action's own repository**, confirming
  the resolved SHA actually belongs there and was not supplied by an
  unrelated fork or a spoofed value.

## Dependabot cooldown for version updates

- [Dependabot version updates introduce default package
  cooldown][cooldown-changelog] (2026-07-14) — version updates default
  to a 3-day registry-availability delay across all ecosystems,
  including `github-actions`, with no configuration required. Security
  updates are exempt and still open immediately. Configurable through
  the `cooldown` block in `dependabot.yml`.

## Static analysis

- [zizmor release notes][zizmor] — a Rust static analyzer for GitHub
  Actions workflows and composite actions; its default policy flags
  non-SHA-pinned `uses:` references for any action outside the
  `actions/` org.

[uses-syntax]: https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions#jobsjob_idstepsuses
[hardening]: https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions
[repo-settings]: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository
[org-settings]: https://docs.github.com/en/organizations/managing-organization-settings/disabling-or-limiting-github-actions-for-your-organization
[blocking-changelog]: https://github.blog/changelog/2025-08-15-github-actions-policy-now-supports-blocking-and-sha-pinning-actions
[git-ref]: https://docs.github.com/en/rest/git/refs
[git-tag]: https://docs.github.com/en/rest/git/tags
[get-commit]: https://docs.github.com/en/rest/commits/commits
[cooldown-changelog]: https://github.blog/changelog/2026-07-14-dependabot-version-updates-introduce-default-package-cooldown
[zizmor]: https://docs.zizmor.sh/release-notes
