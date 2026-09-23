---
license: MIT
name: actions-pinning
description: >
  Inventory, classify, and pin every `uses:` reference in GitHub Actions
  workflows, composite actions, and reusable workflows to a verified commit
  SHA, then keep those pins fresh with Dependabot. Use when the user says
  "pin actions", "unpinned actions", "SHA pin", "supply chain for
  workflows", or invokes /actions-pinning. Do NOT use for permissions and
  injection hardening of workflow files (route to /oss-hygiene) or for CI
  run-time speed (route to /ci-optimize).
---

# actions-pinning

Pins every `uses:` reference in GitHub Actions workflows, composite
actions, and reusable workflows to a commit SHA, verifies each SHA
belongs to the claimed action repository, and keeps the pins current
with Dependabot.

This skill covers supply-chain pinning only. `/oss-hygiene` covers
`Token-Permissions` and `Dangerous-Workflow` hardening for the same
workflow files; `/ci-optimize` covers wall-clock speed. Run those
separately.

## Protocol

### 1. Inventory

Run the bundled scanner against every workflow and composite/reusable
workflow file:

```bash
python3 scripts/pin_check.py .
```

It walks `.github/workflows/**` and `.github/actions/**`, prints a
table of `(file, line, action, ref, status)` for every `uses:` line,
and exits 1 when any reference is unpinned. Use `--json` for
machine-readable output when scripting the remaining steps.

### 2. Classify

The scanner assigns one status per reference:

| Status | Meaning | Action needed |
|---|---|---|
| `pinned-sha` | already a full 40-character commit SHA | none |
| `unpinned-tag` | a tag such as `v4` or `v4.1.0` | resolve to a SHA |
| `unpinned-branch` | a branch ref such as `main` | resolve to a SHA |
| `missing-ref` | no `@ref` at all | resolve to a SHA |
| `local` | a local `./path` action | skip — not a supply-chain risk |
| `docker` | a `docker://image` reference | flag separately — SHA pinning applies to the image digest, not this scanner |

### 3. Resolve each tag or branch to a commit SHA

For each `unpinned-tag`, `unpinned-branch`, or `missing-ref` finding:

```bash
# Lightweight tag or branch: the ref object is the commit directly.
gh api repos/{owner}/{repo}/git/ref/tags/{tag} --jq '.object'

# Annotated tag: the ref object is a tag object, not a commit.
# Dereference it to get the commit SHA.
gh api repos/{owner}/{repo}/git/tags/{tag_sha} --jq '.object.sha'
```

**Impostor-commit check — always run before rewriting a pin.** Confirm
the resolved SHA actually belongs to the action's own repository, not
a fork, a rewritten ref, or a spoofed value:

```bash
gh api repos/{owner}/{repo}/commits/{sha}
```

A 404 here means the SHA does not belong to that repository. Stop and
re-resolve; do not write an unverified SHA.

Once verified, rewrite the line:

```yaml
uses: owner/repo@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
```

Keep the original tag as a trailing comment — it is the human-readable
version marker; the SHA is the enforced pin.

### 4. Keep pins fresh with Dependabot

Add (or merge into an existing `dependabot.yml`) the `github-actions`
ecosystem entry in `assets/dependabot-actions-snippet.yml`. Dependabot
resolves tag bumps to new commit SHAs automatically and opens a PR
with the version comment updated — review and merge those PRs rather
than hand-editing pins later.

Version updates (not security updates) default to a 3-day
registry-availability cooldown as of 2026-07-14; a newly published tag
won't appear in a Dependabot PR until it clears that window. See
`references/policy.md` for the source.

For the full `dependabot.yml` scaffold across every ecosystem in the
repo, use `/oss-hygiene` — this skill only owns the `github-actions`
entry.

### 5. Repository and organization pinning policy

GitHub can enforce SHA pinning at the allowed-actions policy level
(repo, org, or enterprise), including blocking specific actions
outright. Read the current policy before proposing any change:

```bash
gh api repos/{owner}/{repo}/actions/permissions
```

This is a read. Never call the corresponding write endpoints
(`PUT repos/{owner}/{repo}/actions/permissions` and the
`selected-actions` / `allowed_actions` variants) without the user's
explicit authorization for that specific change — policy changes can
block other workflows in the repo from running.

### 6. Flag mutable downloads inside workflow scripts

Regex pinning covers `uses:` only. While reading each workflow, also
flag (findings only, no rewrite) any `run:` step that fetches code
outside the pinned-action mechanism:

- `curl ... | sh` or `curl ... | bash` piping a remote script straight
  into a shell.
- `wget` from a URL with no version or checksum.
- `pip install package` (or `npm install`, `gem install`, ...) with no
  version pin.

These are supply-chain risk in the same family as an unpinned action,
but fixing them is per-ecosystem and often changes build behavior —
report them, do not rewrite them.

### 7. Optional: zizmor

If `zizmor` is installed, run it for a second opinion (it also checks
`bot-conditions` and composite-action internals this scanner does
not):

```bash
zizmor .github/workflows/
```

Skip silently if it is not installed — it is optional tooling, not a
required gate.

### 8. Verify

Re-run the scanner after every rewrite batch:

```bash
python3 scripts/pin_check.py . && echo "all uses: references pinned"
```

Exit 0 with no `unpinned-tag`, `unpinned-branch`, or `missing-ref`
rows means every actionable reference is pinned. Report `local` and
`docker` rows separately — they are informational, not failures.

## What this skill is NOT for

- `Token-Permissions` and `Dangerous-Workflow` hardening (least-privilege
  `permissions:` blocks, `pull_request_target` risk, `${{ github.event.* }}`
  interpolation into shell) — use `/oss-hygiene`.
- CI run-time speed — use `/ci-optimize`.
- Choosing or writing the full `dependabot.yml` for non-Actions
  ecosystems — use `/oss-hygiene`.
- Applying an org-wide allowed-actions policy without the repo owner's
  explicit authorization for that specific write.

## References

- `references/policy.md` — cited primary sources for `uses:` syntax,
  SHA pinning, the allowed-actions policy, SHA resolution endpoints,
  the Dependabot cooldown, and zizmor.
- `scripts/pin_check.py` — the inventory/classification scanner used
  in steps 1, 2, and 8 (`--self-test` runs its embedded fixtures;
  `--json` for machine-readable output).
- `assets/dependabot-actions-snippet.yml` — the `github-actions`
  ecosystem entry for `dependabot.yml`.
