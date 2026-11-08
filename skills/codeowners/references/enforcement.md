# Enforcing CODEOWNERS with rulesets

Reference detail for step 5 of the protocol: turning `CODEOWNERS` from a
review-request list into an enforced merge gate.

## `CODEOWNERS` alone does not block a merge

A `CODEOWNERS` file causes GitHub to auto-request review from the matching
owners on a pull request. It does not, by itself, prevent a merge if those
owners never approve. Enforcement is a separate ruleset setting.

## `require_code_owner_review`

The default-branch ruleset's `pull_request` rule takes a
`require_code_owner_review` boolean parameter. When `true`, at least one
required approval must come from a matched code owner before the pull
request can merge.

Primary source: [Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets) (docs.github.com).

Read the current rule before writing:

```bash
gh api "repos/$REPO/rulesets/<id>" --jq '.rules[] | select(.type=="pull_request")'
```

Update only the one field, preserving every other `pull_request` parameter
from the existing ruleset (`required_approving_review_count`,
`dismiss_stale_reviews_on_push`, `require_last_push_approval`,
`required_review_thread_resolution`, `allowed_merge_methods` where
present):

```json
{
  "type": "pull_request",
  "parameters": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews_on_push": true,
    "require_code_owner_review": true,
    "require_last_push_approval": false,
    "required_review_thread_resolution": true
  }
}
```

Get explicit user authorization before the `PUT` — this is a live policy
change to the default branch, not a local file edit.

## The required-reviewer ruleset rule (complementary, not a replacement)

GitHub shipped a separate ruleset rule, "required review by specific
teams," in public preview on 2025-11-03 and GA on 2026-02-17. It requires
a configurable number of approvals from one or more named teams, scoped to
file or folder patterns, enforced directly at the ruleset level.

Sources:

- [Required review by specific teams now available in rulesets](https://github.blog/changelog/2025-11-03-required-review-by-specific-teams-now-available-in-rulesets) (github.blog, 2025-11-03, public preview)
- [Required reviewer rule is now generally available](https://github.blog/changelog/2026-02-17-required-reviewer-rule-is-now-generally-available) (github.blog, 2026-02-17, GA)

Key differences from `CODEOWNERS` + `require_code_owner_review`:

| | `CODEOWNERS` | Required-reviewer rule |
|---|---|---|
| Where it lives | A file in the repository tree | A ruleset rule, queryable and settable via the API |
| What it does | Auto-requests reviewers; gates a merge only when paired with `require_code_owner_review` | Directly gates a merge on team approval, independent of any file |
| Scope | Per-repository file | Can be set at org or enterprise level across many repositories |
| Ownership source | One file, hand-authored | Rule parameters, settable without touching repository content |

GitHub's own framing, per the changelog posts above, is that this rule
**augments** `CODEOWNERS`, not replaces it: `CODEOWNERS` continues to
drive auto-requested reviewers and per-file ownership documentation, while
the required-reviewer rule enforces approval policy at the ruleset level
and scales more easily across repositories.

Mention this rule as an available option when a user asks about enforcing
ownership. Do not configure it without the user explicitly asking for it,
and never mutate a live ruleset without authorization (see Guardrails in
`SKILL.md`).
