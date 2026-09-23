# Classification policy

`scripts/stale_branches.py` classifies each remote branch into exactly one
recommendation.

## Rule

1. A branch protected by a ruleset, or with an open pull request, is always
   `keep`, regardless of age or merged status.
2. Otherwise, a merged branch is `delete`.
3. Otherwise, an unmerged branch at or past the `--days` threshold is
   `archive`.
4. Otherwise, `keep`.

The default branch is always excluded from the report.

## Why deletion needs a human

Branch deletion is a destructive `git push --delete`. The script only prints
the command; a person runs it after explicit per-batch authorization. This
mirrors the "explicit authorization" guardrail every other skill in this
catalog uses for destructive or paid operations.

## Sources

- GitHub Docs, "Managing the automatic deletion of branches":
  <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-the-automatic-deletion-of-branches>
  — documents the `delete_branch_on_merge` repository setting this skill
  reads and proposes enabling.
- GitHub REST API, "Update a repository":
  <https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#update-a-repository>
  — the `PATCH /repos/{owner}/{repo}` endpoint that carries
  `delete_branch_on_merge`. The write itself belongs to `/gh-bootstrap` step 2.
- GitHub REST API, "Get rules for a branch":
  <https://docs.github.com/en/rest/repos/rules?apiVersion=2022-11-28#get-rules-for-a-branch>
  — `GET /repos/{owner}/{repo}/rules/branches/{branch}`, used to detect
  ruleset protection before recommending deletion.
- Git documentation, `git-branch`: <https://git-scm.com/docs/git-branch> —
  the `--merged` flag used to determine merged status.
- Git documentation, `git-rev-list`: <https://git-scm.com/docs/git-rev-list>
  — the `--left-right --count` form used for ahead/behind counts.
