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
- Long reference material that belongs in a linked doc instead of inline.
  Every harness loads the full file on every turn
  (<https://code.claude.com/docs/en/memory>;
  <https://learn.chatgpt.com/docs/agent-configuration/agents-md>), so length
  is a recurring token cost, not a one-time read.
- Anything that only CI or sandboxing should enforce (a rule an agent
  cannot violate even if it tried does not need to be stated as a rule).

## Effectiveness evidence is mixed

Do not present `AGENTS.md` as a guaranteed task-success lift. Two 2026
preprints reach different conclusions using different benchmarks and
methods:

- One preprint reports a root `AGENTS.md` correlates with reduced token
  usage and faster completion on real pull requests — a correlational
  finding on efficiency, not a controlled trial of task success.
  Source: <https://arxiv.org/abs/2601.20404> ("On the Impact of AGENTS.md
  Files on the Efficiency of AI Coding Agents")
- A separate study from ETH Zurich / LogicStar.ai found no significant
  improvement in task-success rate on SWE-bench Lite or a custom CTXbench
  benchmark. That preprint's own primary URL was not independently
  re-verified in this pass; cite the efficiency preprint above directly,
  and describe this second study as a named, findable conflicting result
  rather than restating its numbers second-hand.

Keep the file for the token-cost and precedence reasons in
`harness-matrix.md`, not on a promised task-success guarantee.

## Nested AGENTS.md

For a monorepo or multi-package repository, add a nested `AGENTS.md` per
package and state explicitly whether it inherits the root file's rules or
replaces them — the spec does not merge files automatically.
Source: <https://agents.md>
