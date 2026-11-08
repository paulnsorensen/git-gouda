# Merge queues

Read this when the audit finds a merge queue on `BASE`.
Sources and confidence are in `evidence.md`.

## Detect

- **GitHub merge queue.** The rules API returns a `merge_queue` rule, and `.parameters.merge_method` is the queue's method. Only organization-owned repositories can use it.
- **Third-party queue.** Look for its config file, and for its app in the check runs of a recent bot PR head:

  ```bash
  gh api "repos/$R/commits/$SHA/check-runs" --jq '[.check_runs[] | .app.slug + ": " + .name] | unique'
  ```

| Queue | Config file | Signal |
| --- | --- | --- |
| Mergify | `.mergify.yml`, `.mergify.yaml`, `.mergify/config.yml`, `.mergify/config.yaml`, `.github/mergify.yml`, `.github/mergify.yaml` | app `mergify`, check `Mergify Merge Queue` |
| Kodiak | `.kodiak.toml` | app `kodiakhq` |
| Trunk | `.trunk/trunk.yaml` | bot `trunk-io`, branches `trunk-merge/**` |
| Aviator | none confirmed | `/aviator merge` comments |
| Graphite | none confirmed | app `graphite-app` |
| bors-ng | not checked | repository archived |

A queue app without a config file in the repository uses a dashboard or organization config. Report its rules as `unknown`.

## GitHub merge queue

Keep the arm-at-open path. Change three things:

1. Use the App token from `github-app-token.md`. `GITHUB_TOKEN` cannot add a PR to a merge queue.
2. Keep `allow_auto_merge` on. The UI enables auto-merge on a queue branch without it, but the API call that `gh` makes still fails (cli/cli#13398).
3. Make sure each workflow of a required check has the `merge_group` trigger. Without it, the check never reports in the queue and the merge fails. Ask before you add the trigger.

The template needs no other change. On a queue branch, `gh pr merge --auto` enables auto-merge or adds the PR to the queue, and the queue sets the merge method.
Renovate needs no change. With the default `platformAutomerge`, GitHub auto-merge adds the PR to the queue.

## Third-party queue

Do not arm GitHub auto-merge. It merges the PR through GitHub directly, outside the queue, unless a ruleset lets only the queue app merge.
Hand minor and patch PRs to the queue instead. Ask before you change the queue's config.

- **Dependabot:** set `QUEUE_LABEL` in the template to the label that the queue reads. Create the label first.
- **Renovate:** use this rule instead of `assets/renovate-automerge.json`. `automerge: false` keeps Renovate from arming GitHub auto-merge.

  ```json
  {
    "description": "Label minor and patch updates for the merge queue after a 3-day release age. Major updates stay manual.",
    "matchUpdateTypes": ["minor", "patch"],
    "addLabels": ["dependencies-automerge"],
    "automerge": false,
    "minimumReleaseAge": "3 days"
  }
  ```

| Queue | Queue side |
| --- | --- |
| Mergify | `merge_protections_settings.auto_merge_conditions: [label = dependencies-automerge]`. Merge Protections or the Mergify merge queue must be on. Mergify suggests `rebase-strategy: disabled` in `dependabot.yml`. |
| Kodiak | Skip the label. `[merge.automerge_dependencies]` with `versions = ["minor", "patch"]` and `usernames = ["dependabot"]` or `["renovate"]`, without `[bot]`. Leave the template out and keep Renovate `automerge: false`. |
| Trunk | Use the enqueue label from the Trunk web app as `QUEUE_LABEL`. |
| Aviator | Use the queue label from the Aviator config as `QUEUE_LABEL`. |
| Graphite | The Graphite docs read for this skill show no enqueue path for bot PRs. Report it. A human queues these PRs. |
| bors-ng | Archived. Report it and set up nothing. |

The label is safe to add at PR open. The queue still waits for its own conditions before it merges.
