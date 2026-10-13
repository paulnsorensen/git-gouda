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
  Every harness loads the full file on every turn
  (<https://code.claude.com/docs/en/memory>;
  <https://developers.openai.com/codex/guides/agents-md/>), so length is a
  recurring token cost, not a one-time read. Claude Code's guidance lists
  "Detailed API documentation (link to docs instead)" under exclude
  (<https://code.claude.com/docs/en/best-practices>).
- Repository overviews and file-by-file layout descriptions. Claude Code's
  guidance excludes "File-by-file descriptions of the codebase"
  (<https://code.claude.com/docs/en/best-practices>). The ETH preprint
  below found that repository overviews do not help.
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

- One preprint reports lower median runtime (28.64%) and lower output
  token use (16.58%) on 124 pull requests in 10 repositories, with
  comparable task completion. The finding is correlational.
  Source: <https://arxiv.org/abs/2601.20404> ("On the Impact of AGENTS.md
  Files on the Efficiency of AI Coding Agents")
- The ETH Zurich and LogicStar.ai preprint reports that context files do
  not generally improve task success rates and raise inference cost by
  over 20% on average. It finds them useful for non-standard
  coding practices, and finds repository overviews unhelpful.
  Source: <https://arxiv.org/abs/2602.11988> ("Evaluating AGENTS.md: Are
  Repository-Level Context Files Helpful for Coding Agents?")

Keep the file for the token-cost and precedence reasons in
`harness-matrix.md`, not on a promised task-success guarantee.

## Nested AGENTS.md

For a monorepo or multi-package repository, add a nested `AGENTS.md` only
to a package that needs its own rules. Harnesses load the nested file
together with its ancestors, so the nested file holds only the package's
delta. Name each root rule that the nested file overrides. The spec says
only that the closest file takes precedence (<https://agents.md>). Codex,
Claude Code, Cursor, and Gemini CLI document additive loading; see
`harness-matrix.md` for the sources.
