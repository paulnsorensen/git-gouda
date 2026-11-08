# Harness matrix

Which agent harness reads which instruction file, in what precedence, under
what size cap. Every row cites a fetched primary source. The nested-file
rows were checked on 2026-10-13.

## Nested files at a glance

No checked harness replaces ancestor instruction files with the nearest
nested file. Each one loads the nested file in addition to its ancestors.
The nearer file wins only on conflict.

| Harness | Ancestors | Nested file | Conflict rule |
|---|---|---|---|
| Codex | concatenated, root first | concatenated, last | later file wins |
| Claude Code | loaded at launch | loaded on demand | concatenated, no override |
| Cursor | combined | combined | more specific wins |
| Gemini CLI | concatenated | loaded on tool access | not stated |
| Copilot CLI | walked up to the git root | loaded | nearest wins |
| VS Code agent | additive | experimental, off by default | no guaranteed order |

## AGENTS.md spec

- Plain Markdown, no required fields, no frontmatter. "The closest
  AGENTS.md to the edited file wins; explicit user chat prompts override
  everything." Source: <https://agents.md>
- For a monorepo, the spec says to place another `AGENTS.md` inside each
  package, and that "the closest one takes precedence". The page states no
  merge rule. Source: <https://agents.md>

## OpenAI Codex

- Discovery: `~/.codex/AGENTS.md` (global), then the project root down to
  the working directory. Codex includes at most one file per directory: it
  checks `AGENTS.override.md`, then `AGENTS.md`, then each name in
  `project_doc_fallback_filenames`. An override hides the `AGENTS.md` in
  the same directory. Codex skips empty files.
  Source: <https://developers.openai.com/codex/guides/agents-md/>
- Merge order: "Codex concatenates files from the root down, joining them
  with blank lines. Files closer to your current directory override
  earlier guidance because they appear later in the combined prompt."
  Source: <https://developers.openai.com/codex/guides/agents-md/>
- Cap: Codex "stops adding files once the combined size reaches the limit
  defined by `project_doc_max_bytes` (32 KiB by default)". The files
  nearest the working directory drop first. The docs list "Instructions
  truncated" under troubleshooting. They do not say whether Codex warns, or
  whether it cuts or skips the file that crosses the limit. The docs say to
  raise the limit or split instructions across nested directories.
  Source: <https://developers.openai.com/codex/guides/agents-md/>
- Codex review rules belong in the `AGENTS.md` closest to the code that
  they govern. Source: <https://developers.openai.com/codex/guides/agents-md/>

## Claude Code

- Ancestor `CLAUDE.md` files load at launch. Files in subdirectories load
  on demand, when Claude reads, writes, or edits a file there. Loaded files
  are "concatenated into context rather than overriding each other".
  Source: <https://code.claude.com/docs/en/memory>
- Claude Code reads `AGENTS.md` directly only when no `CLAUDE.md`,
  `.claude/CLAUDE.md`, or `CLAUDE.local.md` exists in the working directory
  or above it. `~/.claude/CLAUDE.md`, managed policy files, and
  `.claude/rules/` do not count. Direct reading needs Claude Code v2.1.277
  or later. The `claude-md-and-agents-md` setting loads both files. A
  `CLAUDE.md` that contains `@AGENTS.md` also loads both.
  Source: <https://code.claude.com/docs/en/memory>
- A nested `AGENTS.md` loads when Claude opens a file in that directory
  with the Read tool, and only when that directory has no `CLAUDE.md` file
  of its own. Source: <https://code.claude.com/docs/en/memory>
- Size: target under 200 lines per `CLAUDE.md`, because "longer files
  consume more context and reduce adherence". `@path` imports do not reduce
  context cost: imported files also load at launch, up to four hops deep.
  Source: <https://code.claude.com/docs/en/memory>
- Alternatives: a path-scoped rule in `.claude/rules/` loads when Claude
  reads or edits a matching file. `claudeMdExcludes` skips ancestor files
  by glob in a monorepo. Source: <https://code.claude.com/docs/en/memory>

## Cursor

- Cursor supports `AGENTS.md` at the project root and in subdirectories.
  "Instructions from nested AGENTS.md files are combined with parent
  directories, with more specific instructions taking precedence." The
  docs do not say when a nested file loads.
  Source: <https://cursor.com/docs/context/rules>
- Rules guidance: keep rules under 500 lines, and reference files instead
  of copying their contents. Source: <https://cursor.com/docs/context/rules>

## Gemini CLI

- Gemini CLI loads the global `~/.gemini/GEMINI.md`, the workspace files
  and their parents, and just-in-time files: when a tool touches a path, it
  scans that directory and its ancestors up to a trusted root. It
  concatenates every file it finds and sends the result with every prompt.
  Source: <https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md>
- The `context.fileName` setting can name `AGENTS.md`, so Gemini CLI reads
  it without a `GEMINI.md` copy. `/memory show` prints the concatenated
  context. Source: <https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md>
- `@file.md` imports nest up to five levels by default.
  Source: <https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/memport.md>

## GitHub Copilot

- Copilot coding agent added `AGENTS.md` support August 28, 2025.
  Source: <https://github.blog/changelog/2025-08-28-copilot-coding-agent-now-supports-agents-md-custom-instructions/>
- Copilot also reads `.github/copilot-instructions.md` (repo-wide, no
  frontmatter), `.github/instructions/*.instructions.md` (path-scoped, needs
  `applyTo` frontmatter), `CLAUDE.md`, and `GEMINI.md`. "The nearest
  AGENTS.md file in the directory tree will take precedence."
  Source: <https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions>
- Copilot CLI v1.0.11 discovers `AGENTS.md` at every directory level from
  the working directory up to the git root. This comes from an issue
  comment, not from vendor docs.
  Source: <https://github.com/github/copilot-cli/issues/1655>
- VS Code lists nested `AGENTS.md` files for its local agent only when the
  experimental `chat.useNestedAgentsMdFiles` setting is on. It is off by
  default. VS Code says that instruction sources are additive and that no
  file order or precedence rule is safe to rely on.
  Source: <https://code.visualstudio.com/docs/agent-customization/custom-instructions>
- Full Copilot-specific detail (path-scoped `applyTo` rules, code-review
  toggles, `excludeAgent`) lives in the sibling
  `github-copilot-repo-instructions` skill, not here.

## Governance

- AGENTS.md was released by OpenAI in August 2025 and is adopted across a
  large, actively growing set of repositories.
  Source: <https://agents.md>

## Size-cap summary

| Harness | Hard cap | Practical target |
|---|---|---|
| Codex | 32 KiB combined chain; nearest files drop first | well under the cap |
| Claude Code (`CLAUDE.md`) | none documented | under 200 lines |
| Cursor rules | none documented | under 500 lines |
| Copilot repo-wide file | none documented (GitHub's own guidance: ≤ 2 pages) | ≤ 2 pages |
| agents.md spec itself | none | not specified by the spec |

The check script (`../scripts/agents_md_check.py`) enforces the Codex 32
KiB figure as a hard fail and the ~200-line figure as a soft warning, since
that is the only harness-documented number with an enforceable exit code.
