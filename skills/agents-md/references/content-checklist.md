# Content checklist

What belongs in `AGENTS.md`, and what does not. Harness-behavior claims below
are cited. The Include and Exclude lists are this skill's guidance. Treat an
uncited harness claim as a proposal to verify, not a fact to ship.

## Include

- Exact build, test, and lint commands, verbatim from the project's own
  `justfile` or CI config — not paraphrased, not remembered.
- Quality gates: which command must pass before handoff, and what "pass"
  means (exit code, a count, an empty grep).
- Non-default conventions the project actually enforces (naming, layout,
  commit style).
- Safety and permission boundaries: what an agent must not touch, and why.
- PR and commit rules.
- Explicit "done" criteria for common task shapes.

This list is the guidance of this skill. The agents.md site frames the file
as an operational README for agents, not a second product README
(<https://agents.md>).

## Exclude

- Narrative history ("we used to do X, then switched to Y"). An agent needs
  the current rule, not the story behind it.
- Anything already in `README.md`. Duplication drifts; link instead of
  copying, or state only the operational delta.
- Secrets, tokens, internal URLs, or credentials — the file is committed
  and readable by anyone with repo access.
- Per-person preferences ("Alice likes tabs"). `AGENTS.md` is project
  policy, not one contributor's taste.
- Stale commands. A command that no longer exists in the `justfile` or CI
  is worse than no command — it sends an agent down a dead end. The bundled
  `scripts/agents_md_check.py` checks every backticked `just <recipe>`
  against the real `justfile`; treat a reported miss as a required fix, not
  a false positive.
- Long reference material that belongs in a linked doc instead of inline,
  such as detailed API documentation. Name the doc and when to read it.
  Applicable instructions consume context when loaded; harnesses differ in
  when they load files. Do not assume every file loads on every turn or equate
  context use with billed tokens. Claude Code's guidance excludes detailed
  API documentation (<https://code.claude.com/docs/en/best-practices>).
- Repository overviews and file-by-file layout descriptions. Claude Code's
  guidance excludes file-by-file descriptions
  (<https://code.claude.com/docs/en/best-practices>). The ETH overview
  ablation found no statistically significant accuracy effect for GPT-5.2;
  it does not establish that overviews never help.
- Style rules that a linter or formatter already enforces. The gate command
  already catches each violation.
- Anything that only CI or sandboxing should enforce (a rule an agent
  cannot violate even if it tried does not need to be stated as a rule).

Pruning test from Claude Code's guidance: for each line, ask "Would
removing this cause Claude to make mistakes?" If not, cut it
(<https://code.claude.com/docs/en/best-practices>).

## Effectiveness evidence is mixed

Do not present `AGENTS.md` as a guaranteed task-success lift. Two 2026
preprints reach different conclusions using different benchmarks and
methods:

- A Codex study using `gpt-5.2-codex` on 124 pull requests in 10 repositories
  associates `AGENTS.md` with 28.64% lower median runtime and 16.58% fewer
  output tokens. Comparable completion rests on a manual sanity check; the
  study does not establish semantic correctness or PR equivalence.
  Source: <https://arxiv.org/html/2601.20404v2> (30 March 2026).
- In the ETH Zurich and LogicStar.ai study, LLM-generated context files
  raised mean inference cost by 20% on SWE-bench Lite and 23% on CTXbench.
  Developer-written files also raised cost, but not by those same rates.
  Neither file type showed a statistically significant success difference
  from no file in those comparisons. The GPT-5.2 overview ablation also
  found no significant accuracy difference, not proof of equivalence.
  Source: <https://arxiv.org/html/2602.11988v3> (29 September 2026).

Keep useful repository rules, but do not promise a task-success gain or a
fixed token saving. See `harness-matrix.md` for loading and precedence.

## Nested AGENTS.md

For a monorepo or multi-package repository, add a nested `AGENTS.md` only
to a package that needs its own rules. Harnesses load the nested file
together with its ancestors, so the nested file holds only the package's
delta. Name each root rule that the nested file overrides. The spec says
only that the closest file takes precedence (<https://agents.md>). Codex,
Claude Code, Cursor, and Gemini CLI document additive loading; see
`harness-matrix.md` for the sources.
