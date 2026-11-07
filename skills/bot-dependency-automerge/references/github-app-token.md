# GitHub App token variant

Read this when push workflows must run after an auto-merge, or when the base branch has a merge queue.

## Why

- Events that `GITHUB_TOKEN` triggers start no new workflow runs, except dispatch events. A GitHub App installation token or a personal access token avoids this limit.
- A merge queue rejects `GITHUB_TOKEN`. The merge step needs a personal access token or a GitHub App token that can merge.
- Prefer a GitHub App over a personal access token. The App token expires after one hour and has only the permissions you request.

## Setup

The user does these steps. The skill never creates an App or stores a key.

1. Create a GitHub App with repository permissions **Contents: Read and write** and **Pull requests: Read and write**.
2. Install the App on the repository only.
3. Store the client ID and the private key as **Dependabot** secrets. A Dependabot run reads only Dependabot secrets, not Actions secrets.

   ```bash
   gh secret set AUTOMERGE_APP_CLIENT_ID --app dependabot
   gh secret set AUTOMERGE_APP_PRIVATE_KEY --app dependabot < app-private-key.pem
   ```

## Workflow change

In `.github/workflows/dependabot-automerge.yml`, lower the job permissions to `contents: read` and `pull-requests: read`.
Add this step before the arm step:

```yaml
      - name: Create App token
        id: app-token
        uses: actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510 # v3.3.0
        with:
          client-id: ${{ secrets.AUTOMERGE_APP_CLIENT_ID }}
          private-key: ${{ secrets.AUTOMERGE_APP_PRIVATE_KEY }}
          permission-contents: write
          permission-pull-requests: write
```

In the arm step, set `GH_TOKEN: ${{ steps.app-token.outputs.token }}`.
Resolve the latest `actions/create-github-app-token` release and its commit before you write the pin. Use the commands in `SKILL.md` step 5.

## Verify

- After the first auto-merge, run `gh run list --event push --branch BASE --limit 3`. A push run for the merge commit shows that the token change works.
- On a merge-queue branch, run `gh pr view PR --json autoMergeRequest,mergeStateStatus`. A non-null `autoMergeRequest` shows that the PR is armed.
