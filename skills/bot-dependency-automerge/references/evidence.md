# Evidence

Read this when the user asks why a default exists, or challenges one.
All sources were checked on 2026-11-04. Confidence uses `certain` and `speculating`.

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
| `gh pr merge --auto` merges at once instead of arming when nothing blocks the PR. | [cli/cli#8514][cli-8514] | `speculating`: the issue closed as stale with no fix |
| GitHub's Dependabot auto-merge example uses `on: pull_request`, a `user.login` gate, and `gh pr merge --auto`. | [Automating Dependabot with GitHub Actions][gh-automate] | `certain` |
| A Dependabot `pull_request` run gets a read-only token. The `permissions` key can raise it. Only Dependabot secrets are available. | [Troubleshooting Dependabot on GitHub Actions][gh-dbot-actions] | `certain` |
| A merge queue rejects `GITHUB_TOKEN`. | [Automating Dependabot with GitHub Actions][gh-automate] | `certain` |
| Events that `GITHUB_TOKEN` triggers start no new workflow runs, except dispatch events and approval-gated `pull_request` events. | [GITHUB_TOKEN][gh-token] | `certain` |
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

## Incidents

| Incident | What happened | Defense | Confidence |
| --- | --- | --- | --- |
| tj-actions/changed-files, 2025-03 | Attackers moved existing version tags to one malicious commit. | SHA pins | `speculating`: [StepSecurity][stepsec-tj] only |
| Nx s1ngularity, 2025-08-26 | A `pull_request_target` injection leaked the npm token. Malicious versions were live for 4 hours. | Release age, no `pull_request_target` | `certain`: [Nx post-mortem][nx] |
| chalk and debug, 2025-09-08 | A phished maintainer published malicious versions, removed a few hours later. | Release age | `speculating`: [Wiz][wiz-chalk] only |
| Shai-Hulud 2.0, 2025-11-21 to 2025-11-23 | A preinstall worm ran on developer machines and in CI. | Release age, lifecycle-script limits | `speculating`: [Wiz][wiz-shai] only |

[gh-automerge]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request
[cli-8514]: https://github.com/cli/cli/issues/8514
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
