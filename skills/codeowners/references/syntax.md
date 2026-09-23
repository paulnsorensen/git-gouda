# CODEOWNERS syntax and precedence

Reference detail for steps 1–3 of the protocol.

Primary source: [About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) (docs.github.com).

## File location

GitHub reads `CODEOWNERS` from exactly one of three locations, in this
order of precedence:

1. The repository root.
2. `docs/CODEOWNERS`.
3. `.github/CODEOWNERS`.

Only the first location found takes effect. A file in a second location is
ignored, not merged.

## Rule syntax

Each non-comment, non-blank line is a rule:

```
<pattern> <owner> [<owner> ...]
```

- `<pattern>` uses `.gitignore`-style path matching.
- `<owner>` is a GitHub username prefixed with `@`, a team prefixed with
  `@org/team-name`, or an email address tied to a GitHub account.
- A line can list more than one owner; all listed owners are requested for
  review.

## Pattern matching rules

- `*` matches anything except `/`.
- `**` matches any number of path segments.
- A pattern with a leading `/` anchors to the repository root.
- A pattern without a leading `/` can match at any depth in the tree.
- A pattern ending in `/` matches a directory and everything under it.
- Patterns with spaces need the space escaped with `\`.

## Precedence: last match wins

CODEOWNERS evaluates rules top to bottom and applies the **last** matching
rule to a given file, not the first. This means:

- Put broad, general rules near the top of the file.
- Put narrow, specific overrides near the bottom.
- A trailing `*` rule (`* @org/default-owners`) is a catch-all fallback
  only if nothing more specific appears below it — keep it first, not
  last, so later rules can override it.

## Owner resolution requirements

- A `@username` owner must be a collaborator with write access to the
  repository (directly or through team/org membership).
- A `@org/team-name` owner is only effective if that team has been
  explicitly granted write access to the repository. Org membership alone
  does not grant CODEOWNERS effect.
- An owner that does not resolve is not an error at parse time; GitHub
  silently skips it. Confirm every handle and team resolves — see
  Guardrails in `SKILL.md` — rather than relying on the API to catch it.
- Use `gh api repos/{owner}/{repo}/codeowners/errors` (step 4 of the
  protocol) to catch syntax and unresolved-owner problems after push.

## Comments and sections

- A line starting with `#` is a comment and is ignored.
- Group related rules under a comment header per area (for example,
  `# Frontend`, `# Infrastructure`) to keep a large file readable. GitHub's
  pull request review UI can render these as named sections when the
  comment matches a supported section-header format; treat the comment as
  documentation first, since section rendering is a UI convenience, not a
  matching behavior.
