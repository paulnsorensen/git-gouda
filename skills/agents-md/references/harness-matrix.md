# Harness matrix

Which agent harness reads which instruction file, in what precedence, under
what size cap. Every row cites a fetched, live-checked primary source.

## AGENTS.md spec

- Plain Markdown, no required fields, no frontmatter. Conflicts resolve to
  "closest file wins, an explicit chat prompt overrides everything."
  Source: <https://agents.md>
- Nested `AGENTS.md` files use nearest-file-in-directory-tree precedence
  relative to the file being edited. A large monorepo can carry many nested
  files, each scoped to its own subtree. Source: <https://agents.md>

## OpenAI Codex

- Discovery order: `~/.codex/AGENTS.md` (global), then project root down to
  the current working directory. Per directory, Codex checks
  `AGENTS.override.md`, then `AGENTS.md`, then any configured fallback
  filename.
  Source: <https://learn.chatgpt.com/docs/agent-configuration/agents-md>
- The combined chain of loaded files is capped at 32 KiB by default
  (`project_doc_max_bytes`, configurable). Later, closer files win on
  conflict; truncation past the cap is silent — no error, no warning.
  Source: <https://learn.chatgpt.com/docs/agent-configuration/agents-md>;
  corroborated by the `PROJECT_DOC_MAX_BYTES` constant referenced in
  <https://github.com/openai/codex/issues/7138>

## GitHub Copilot

- Copilot coding agent added `AGENTS.md` support August 28, 2025.
  Source: <https://github.blog/changelog/2025-08-28-copilot-coding-agent-now-supports-agents-md-custom-instructions/>
- Copilot also reads `.github/copilot-instructions.md` (repo-wide, no
  frontmatter), `.github/instructions/*.instructions.md` (path-scoped, needs
  `applyTo` frontmatter), `CLAUDE.md`, and `GEMINI.md`. Multiple `AGENTS.md`
  files anywhere in the repo are supported; nearest file in the directory
  tree wins. A single root `CLAUDE.md`/`GEMINI.md` is an alternative to
  `AGENTS.md`, not an addition to it.
  Source: <https://docs.github.com/en/copilot/reference/custom-instructions-support>;
  <https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions>
- Full Copilot-specific detail (path-scoped `applyTo` rules, code-review
  toggles, `excludeAgent`) lives in the sibling
  `github-copilot-repo-instructions` skill, not here.

## Claude Code

- Claude Code reads `AGENTS.md` natively only when no `CLAUDE.md` or
  `CLAUDE.local.md` exists in the working directory or any parent above it.
  If a `CLAUDE.md` already contains an `@AGENTS.md` import, both files load.
  A present `CLAUDE.local.md` counts against the "no CLAUDE.md" check and
  silently disables native `AGENTS.md` reading unless the "Project
  instructions" setting changes this.
  Source: <https://code.claude.com/docs/en/memory>
- `CLAUDE.md` has no hard byte cap, but vendor guidance targets under 200
  lines: longer files still load in full, but adherence to their content
  drops. `@path` imports organize content but do not reduce the context
  loaded — imported files load in full at launch, up to 4 import hops deep.
  Source: <https://code.claude.com/docs/en/memory>
- This precedence rule is the one place Claude Code diverges from the
  agents.md spec's uniform "nearest file wins": Claude Code's trigger is
  "no CLAUDE.md above this file", not "nearest AGENTS.md wins regardless of
  CLAUDE.md". Do not assume the two behave the same way when both a root
  `CLAUDE.md` and a nested `AGENTS.md` are present.

## Governance

- AGENTS.md was released by OpenAI in August 2025 and is adopted across a
  large, actively growing set of repositories.
  Source: <https://agents.md>

## Size-cap summary

| Harness | Hard cap | Practical target |
|---|---|---|
| Codex | 32 KiB combined, silent truncation | well under the cap |
| Claude Code (`CLAUDE.md`) | none documented | under ~200 lines |
| Copilot repo-wide file | none documented (GitHub's own guidance: ≤ 2 pages) | ≤ 2 pages |
| agents.md spec itself | none | not specified by the spec |

The check script (`../scripts/agents_md_check.py`) enforces the Codex 32
KiB figure as a hard fail and the ~200-line figure as a soft warning, since
that is the only harness-documented number with an enforceable exit code.
