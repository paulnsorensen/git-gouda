# Import provenance

The four initial repository skills come from skillz-that-grillz commit 6515e91194227d6ea641a0064c979bb58823331e.

## Intentional adaptations

- The catalog contains exactly five repository-only skills.
- gh-bootstrap defaults to a no-queue PR and CI ruleset. Merge queues require an eligible organization-owned repository and plan.
- safe-settings follows the renamed github-community-projects/safe-settings repository at pinned release 2.1.17. Its workflow uses Node 22 and npm ci.
- safe-settings labels.exclude uses the pinned schema shape, a list of regex strings. Its reference documents identity-based array merging.
- config-review-bot is new and covers CodeRabbit only. It separates schema validity, path coverage, and completed-review evidence.
- Copilot files, personal setup, agent orchestration, and unrelated source skills are excluded.
- Imported manifests remove harness-specific model, context, and tool-routing metadata so installations remain portable across agents.

## Evidence

- [GitHub merge queue requirements](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)
- [CodeRabbit configuration](https://docs.coderabbit.ai/reference/configuration)
- [CodeRabbit path instructions](https://docs.coderabbit.ai/configuration/path-instructions)
- [safe-settings 2.1.17 source](https://github.com/github-community-projects/safe-settings/tree/2.1.17)
