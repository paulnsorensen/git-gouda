# safe-settings deployment

Reference for step 3 of the protocol: picking and configuring the deployment path.

Authoritative sources:

- <https://github.com/github-community-projects/safe-settings/blob/2.1.17/docs/deploy.md>
- <https://github.com/github-community-projects/safe-settings/blob/2.1.17/docs/github-action.md>
- <https://github.com/github-community-projects/safe-settings/blob/2.1.17/docs/AWS-README.md>

## Two deployment shapes

| Shape | Real-time? | Hosting cost | Setup cost | Use when |
|---|---|---|---|---|
| GitHub Actions cron | No (cron interval) | None (Actions minutes) | Low | Starting out, small/medium org, drift fixed every N hours is fine |
| Hosted Probot app | Yes (webhooks) | Lambda / Docker / Heroku / k8s | Medium | Large org, immediate reconciliation matters, you want PR dry-run checks live |

The skill scaffolds the GHA path by default. Switch to hosted once the org is committed and the cron interval feels too coarse.

## GitHub Actions path (default)

The workflow at `assets/full-sync.yml` does the whole job:

1. Checkout the admin repo (this repo)
2. Checkout `github-community-projects/safe-settings` at pinned version 2.1.17
3. Install Node deps
4. Run `npm run full-sync` with the App credentials in env vars

Tradeoffs:

- **Pro:** zero hosting, no public webhook URL, all the App credentials live as repo secrets
- **Pro:** the run log in Actions is the audit trail
- **Con:** drift detected only at the cron tick, not when someone clicks a setting in the UI
- **Con:** for huge orgs (>1000 repos) a full sync takes 30-60 minutes and burns Actions minutes

Tuning:

- The cron interval (`"0 */4 * * *"` = every 4 hours) is the main lever. Tighten for active orgs, loosen for stable ones.
- Add `workflow_dispatch` (already in the template) so admins can trigger an immediate sync after merging a settings PR.
- Pin the release tag and its verified commit in the workflow. Refresh both deliberately — `main` can break.

## Hosted Probot path

Same app code, different deployment.

Required env vars on the host:

| Var | Source |
|---|---|
| `APP_ID` | App settings page |
| `WEBHOOK_SECRET` | Generated when you create the App |
| `PRIVATE_KEY` | App private key, base64-encoded contents of the `.pem` |
| `GH_ORG` | The org name |
| `ADMIN_REPO` | Defaults to `admin`; common choice is `.github` |
| `CONFIG_PATH` | Defaults to `.github`; the directory under `ADMIN_REPO` holding the settings files |

Optional:

| Var | Effect |
|---|---|
| `GHE_HOST` | GitHub Enterprise Server hostname (e.g. `github.mycompany.com`) — required on GHES |
| `WEBHOOK_PROXY_URL` | SMEE URL for local development |
| `NODE_TLS_REJECT_UNAUTHORIZED=0` | Bypass TLS validation (don't ship to production) |

### Deployment options

| Target | Doc |
|---|---|
| AWS Lambda | `AWS-README.md` (uses the SafeSettings-Template repo) |
| Docker / Docker Compose | `deploy.md` |
| Kubernetes | `deploy.md` (build the Docker image, deploy as a Deployment + Service) |
| Heroku | `deploy.md` |

The Lambda path is the most "supported" production option and has its own template repo to copy.

### Webhook setup

The hosted app needs a public URL for GitHub to send webhooks to:

- Webhook URL: `https://your-host.example.com/api/github/webhooks`
- Content type: `application/json`
- Secret: same as `WEBHOOK_SECRET`
- Events: the manifest flow subscribes to the right events automatically

If you're behind a NAT or firewall during dev, use [smee.io](https://smee.io) and set `WEBHOOK_PROXY_URL`.

## Creating the GitHub App

Both paths need the same App. The cleanest way to create it is the manifest flow:

```bash
git clone https://github.com/github-community-projects/safe-settings
cd safe-settings
cp .env.example .env
# Edit .env: set GH_ORG=<your-org>
npm install
npm run dev
# Open the printed URL, click "Register a GitHub App", install on the org.
# The App is created with the right permissions and event subscriptions automatically.
```

After registration, save these from the App settings page:

- App ID (numeric)
- Client ID
- Client secret (generate a new one)
- Private key (download the `.pem`)
- Webhook secret (generate)

Install the App on the org and grant it access to all repositories.

## Permissions the App needs

The manifest flow asks for the right scopes. For reference, safe-settings needs:

- **Repository permissions:** Administration (RW), Contents (RW), Metadata (R), Pull requests (RW), Issues (RW), Custom properties (RW), Actions (R), Checks (RW), Environments (RW), Statuses (RW), Variables (RW)
- **Organization permissions:** Members (RW), Custom properties (Admin), Administration (RW)
- **Subscribe to events:** push, repository, member, team, pull_request, custom_property_values, branch_protection_rule, check_run, check_suite, create, repository_ruleset

Don't hand-roll this — let the manifest flow set it up.

## Refreshing the safe-settings version

The pinned `SAFE_SETTINGS_VERSION` tag and `SAFE_SETTINGS_COMMIT` in the GHA workflow should be bumped together on each release. Process:

```bash
gh release list --repo github-community-projects/safe-settings --limit 5
gh release view <new-tag> --repo github-community-projects/safe-settings
```

Read the release notes for breaking changes (especially around schema), update `SAFE_SETTINGS_VERSION` in `.github/workflows/safe-settings.yml`, open a PR, and merge after the configured guardrails pass. The default cron workflow has no PR dry-run; verify that hosted-app PR checks are configured before claiming that guardrail.
