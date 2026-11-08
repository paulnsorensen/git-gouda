# Evidence

Read this when the user asks why a default exists, or challenges one.
Sources were checked on 2026-11-04. Merge-queue sources and the `gh` source were checked on 2026-11-08. Confidence uses `certain` and `speculating`.

## Origin

A daily cloud routine reached most bot PRs after CI was green. It failed to land them for four reasons:

1. GitHub refused to enable auto-merge on a PR in clean status.
2. The fallback direct merge was blocked in the cloud session, by the proxy and by the permission classifier.
3. Some repositories had `allow_auto_merge` set to `false`.
4. Repositories without required checks merged as soon as auto-merge was enabled, before CI finished.

The fix arms auto-merge inside each repository when the PR opens, while checks are pending.

## Platform facts

| Claim | Source | Confidence |
| --- | --- | --- |
| GitHub shows auto-merge only on a PR that cannot merge immediately. | [Automatically merging a pull request][gh-automerge] | `certain` |
| `gh pr merge --auto` merges at once when the merge state is `CLEAN`, `HAS_HOOKS`, or `UNSTABLE`, and arms auto-merge otherwise. | [gh source, `isImmediatelyMergeable`][gh-merge-src] | `certain` |
| GitHub's Dependabot auto-merge example uses `on: pull_request`, a `user.login` gate, and `gh pr merge --auto`. | [Automating Dependabot with GitHub Actions][gh-automate] | `certain` |
| A Dependabot `pull_request` run gets a read-only token. The `permissions` key can raise it. Only Dependabot secrets are available. | [Troubleshooting Dependabot on GitHub Actions][gh-dbot-actions] | `certain` |
| `GITHUB_TOKEN` cannot add a PR to a merge queue. | [Automating Dependabot with GitHub Actions][gh-automate] | `certain` |
| Events that `GITHUB_TOKEN` triggers start no new workflow runs, except `workflow_dispatch`, `repository_dispatch`, and approval-gated `pull_request` events. | [GITHUB_TOKEN][gh-token], [Events that trigger workflows][gh-events] | `certain` |
| The actor of a merge by auto-merge armed with `GITHUB_TOKEN` is not documented. | no source found | `speculating` |
| Dependabot applies a default 3-day cooldown to version updates, not to security updates. | [Dependabot options reference][dbot-options] | `certain` |
| Dependabot updates SHA-pinned actions and their version comments, but raises no alerts for them. | [GitHub security features for Actions][gh-actions-sec] | `certain` |
| Renovate `platformAutomerge` is on by default. It falls back to Renovate-based automerge when native auto-merge is not available. | [Renovate configuration options][renovate-options] | `certain` |
| Without required checks, the platform can merge Renovate PRs before tests finish or after they fail. | [Renovate configuration options][renovate-options] | `certain` |
| Later `packageRules` entries override earlier ones for the same option. | [Renovate configuration options][renovate-options] | `certain` |
| With `automerge` and `minimumReleaseAge`, Renovate opens the PR at once and adds a pending `renovate/stability-days` check. | [Renovate configuration options][renovate-options] | `certain` |
| `config:best-practices` adds `helpers:pinGitHubActionDigests` and a 3-day release age for npm only. | [Renovate security presets][renovate-security] | `certain` |
| zizmor `bot-conditions` flags `github.actor == 'dependabot[bot]'` as spoofable. | [zizmor audits][zizmor] | `certain` |
| A GitHub Actions policy can block actions and require full-SHA pins (2025-08-15). | [GitHub changelog][gh-sha-policy] | `certain` |
| Arming fails on a PR that changes a workflow file: the API requires the `workflows` scope, which `GITHUB_TOKEN` cannot request. | [cli/cli#11493][cli-11493] | `certain` |
| `actions: write` lets `GITHUB_TOKEN` arm such a PR. | [cli/cli#11493][cli-11493]: two users confirm, the maintainer doubts it | `speculating` |

## Merge queues

| Claim | Source | Confidence |
| --- | --- | --- |
| Merge queues are available in public organization-owned repositories, and in private ones on GitHub Enterprise Cloud. | [Managing a merge queue][gh-mq] | `certain` |
| A required check needs the `merge_group` trigger. Otherwise the check does not report and the merge fails. | [Managing a merge queue][gh-mq] | `certain` |
| On a queue branch, `gh pr merge` enables auto-merge before required checks pass and adds the PR to the queue after they pass. The queue sets the merge method. | [gh pr merge manual][gh-pr-merge], [gh source][gh-merge-src] | `certain` |
| A queued PR can report merge state `CLEAN`, so a `BLOCKED`-only guard skips it. | live GraphQL read of merge-demo/mergequeue-github#934 | `certain` |
| The API call that enables auto-merge fails on a queue branch when `allow_auto_merge` is off. | [cli/cli#13398][cli-13398], open | `speculating`: open issue, not documented |
| Renovate with default `platformAutomerge` adds PRs to a GitHub merge queue through auto-merge, which needs `allow_auto_merge`. | [Renovate automerge][renovate-automerge] | `certain` |
| Renovate merges only when every status check passed, unless `ignoreTests` is set. | [Renovate configuration options][renovate-options] | `certain` |
| Mergify reads `.mergify.yml`, `.mergify.yaml`, `.mergify/config.yml`, `.mergify/config.yaml`, `.github/mergify.yml`, or `.github/mergify.yaml`. | [Mergify file format][mergify-file] | `certain` |
| Mergify `auto_merge_conditions` queues a matching PR when its merge queue is on. It has a `dependabot-update-type` condition. | [Mergify auto-merge][mergify-auto], [Mergify Dependabot][mergify-dbot] | `certain` |
| Kodiak `automerge_dependencies` merges minor and patch PRs from `dependabot` or `renovate`. | [Kodiak recipes][kodiak] | `certain` |
| Trunk and Aviator queue a PR on a comment command or a configurable label. | [Trunk reference][trunk], [Aviator MergeQueue][aviator] | `certain` |
| Without enforcement, a direct GitHub merge bypasses the Graphite queue. | [Graphite merge queue setup][graphite] | `certain` |
| GitHub auto-merge also bypasses Mergify, Kodiak, Trunk, and Aviator queues. | no vendor states it; inferred from the Graphite statement | `speculating` |
| bors-ng is archived. | `gh api repos/bors-ng/bors-ng`: `archived: true` | `certain` |

## Incidents

| Incident | What happened | Defense | Confidence |
| --- | --- | --- | --- |
| tj-actions/changed-files, 2025-03 | Attackers moved existing version tags to one malicious commit. | SHA pins | `speculating`: [StepSecurity][stepsec-tj] only |
| Nx s1ngularity, 2025-08-26 | A `pull_request_target` injection leaked the npm token. Malicious versions were live for 4 hours. | Release age, no `pull_request_target` | `certain`: [Nx post-mortem][nx] |
| chalk and debug, 2025-09-08 | A phished maintainer published malicious versions, removed a few hours later. | Release age | `speculating`: [Wiz][wiz-chalk] only |
| Shai-Hulud 2.0, 2025-11-21 to 2025-11-23 | A preinstall worm ran on developer machines and in CI. | Release age, lifecycle-script limits | `speculating`: [Wiz][wiz-shai] only |

[gh-automerge]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request
[gh-automate]: https://docs.github.com/en/code-security/dependabot/working-with-dependabot/automating-dependabot-with-github-actions
[gh-dbot-actions]: https://docs.github.com/en/code-security/dependabot/troubleshooting-dependabot/troubleshooting-dependabot-on-github-actions
[gh-token]: https://docs.github.com/en/actions/concepts/security/github_token
[dbot-options]: https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference
[gh-actions-sec]: https://docs.github.com/en/actions/how-tos/security-for-github-actions/security-guides/using-githubs-security-features-to-secure-your-use-of-github-actions
[renovate-options]: https://docs.renovatebot.com/configuration-options/
[renovate-security]: https://docs.renovatebot.com/presets-security/
[zizmor]: https://docs.zizmor.sh/audits/
[gh-sha-policy]: https://github.blog/changelog/2025-08-15-github-actions-policy-now-supports-blocking-and-sha-pinning-actions/
[stepsec-tj]: https://www.stepsecurity.io/blog/harden-runner-detection-tj-actions-changed-files-action-is-compromised
[nx]: https://nx.dev/blog/s1ngularity-postmortem
[wiz-chalk]: https://www.wiz.io/blog/widespread-npm-supply-chain-attack-breaking-down-impact-scope-across-debug-chalk
[wiz-shai]: https://www.wiz.io/blog/shai-hulud-2-0-ongoing-supply-chain-attack
[gh-merge-src]: https://github.com/cli/cli/blob/8fcd6a643f993ee12b70ad0edeab741ed133c9f1/pkg/cmd/pr/merge/merge.go
[gh-pr-merge]: https://cli.github.com/manual/gh_pr_merge
[gh-events]: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
[gh-mq]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
[cli-13398]: https://github.com/cli/cli/issues/13398
[cli-11493]: https://github.com/cli/cli/issues/11493
[renovate-automerge]: https://docs.renovatebot.com/key-concepts/automerge/
[mergify-file]: https://docs.mergify.com/configuration/file-format/
[mergify-auto]: https://docs.mergify.com/merge-protections/auto-merge/
[mergify-dbot]: https://docs.mergify.com/integrations/dependabot/
[kodiak]: https://kodiakhq.com/docs/recipes
[trunk]: https://docs.trunk.io/merge-queue/using-the-queue/reference
[aviator]: https://docs.aviator.co/mergequeue
[graphite]: https://graphite.com/docs/set-up-merge-queue
