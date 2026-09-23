---
name: config-review-bot
description: >
  Audit or configure CodeRabbit repository review policy from effective sources.
  Use for CodeRabbit setup, configuration review, path coverage, or a specific
  pull-request review audit. Keep audits read-only by default and separate
  schema validity, path coverage, and completed-review evidence.
license: MIT
---

# config-review-bot

Audit or configure CodeRabbit for this repository.

## Scope

This skill covers repository-local CodeRabbit configuration. It does not install the CodeRabbit app or CLI, start a paid review, post comments, change branch protection or rulesets, or configure another review bot. Setup changes need explicit authorization.

## Protocol

1. Read repository instructions, CI, `.coderabbit.yaml`, and any repository evidence about organization or workspace settings.
2. Identify the effective source. Name the repository file, inherited organization or workspace source, UI setting, or **unknown** when the UI or inherited source is not available.
3. If a pull request is named, record its exact head SHA and base branch before making claims.
4. Read the current official CodeRabbit configuration and path-instruction documentation.
5. For setup, propose the smallest repository-local change. Do not install an app, trigger a review, post feedback, enable paid features, or mutate enforcement.
6. Validate the YAML with the current official schema when available. Report **valid**, **invalid**, or **cannot validate** separately from coverage and review completion.
7. Check real path coverage against repository paths, including dotfiles, hidden asset directories, extensionless files, and templates. Use CodeRabbit minimatch semantics, not a schema-only inference.
8. For a specified pull request, verify review events, findings, and the exact head SHA. A green status or valid YAML does not prove a completed review.
9. Report evidence gaps and changed paths. Keep audit mode read-only.

## Configuration shape

Use the official schema at <https://coderabbit.ai/integrations/schema.v2.json> and current references at <https://docs.coderabbit.ai/reference/configuration> and <https://docs.coderabbit.ai/configuration/path-instructions>. Keep configuration small:

- `reviews.profile` controls feedback volume. It does not enforce merge policy.
- `reviews.path_instructions` uses entries shaped as `{path, instructions}` with repository-relative minimatch patterns.
- Test representative tracked names, including `skills/**/SKILL.md`, `skills/**/assets/**`, `skills/**/references/**`, `skills/**/evals/**`, and `.github/**`.
- Avoid duplicating formatter, YAML, or CI checks already enforced by repository gates.

## Safety rules

- Audit and explain before editing.
- Never add credentials or tokens.
- Never infer effective UI or inherited settings when unavailable; report the evidence gap.
- Never claim schema validity, path coverage, or review completion from another result.
- Never imply a review ran from `.coderabbit.yaml` or a status check alone.
- Ask before changing an existing policy that differs from the request.

## Resources

- [CodeRabbit configuration reference](https://docs.coderabbit.ai/reference/configuration)
- [CodeRabbit path instructions](https://docs.coderabbit.ai/configuration/path-instructions)
- [CodeRabbit schema](https://coderabbit.ai/integrations/schema.v2.json)

## Inline example

```yaml
reviews:
  profile: chill
  path_instructions:
    - path: "skills/**/SKILL.md"
      instructions: "Check portability, scope, and resource references."
```
