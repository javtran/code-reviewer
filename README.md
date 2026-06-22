# AI Code Reviewer

An automated GitHub PR reviewer powered by an LLM. When a pull request is opened or updated, a webhook triggers a Lambda function that fetches the diff, sends it to the Anthropic API for analysis, and posts structured review comments back to the PR.

## Architecture

```
GitHub PR → Webhook → AWS Lambda (Docker) → Anthropic API → PR Comments
                             ↓
                        PostgreSQL (RDS)
                             ↑
                      React Dashboard
```

**Stack:** Python · FastAPI · Docker · AWS Lambda · ECR · RDS (PostgreSQL) · Anthropic API · Next.js · GitHub Actions

## Layers

| Layer | Description | Status |
|-------|-------------|--------|
| 1 | GitHub webhook receiver + signature verification | ✅ |
| 2 | Docker + AWS Lambda deployment | 🔲 |
| 3 | LLM prompt + structured review output | 🔲 |
| 4 | PostgreSQL schema (repos, reviews, comments) | 🔲 |
| 5 | React dashboard (PR history + prompt editor) | 🔲 |
| 6 | CI/CD via GitHub Actions | 🔲 |

## Local Development

### Prerequisites
- Python 3.11+
- [ngrok](https://ngrok.com) for local webhook testing
- A GitHub personal access token with `pull_requests: write` and `contents: read` scopes

### Setup

```bash
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn python-dotenv httpx
```

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
WEBHOOK_SECRET=   # random string you set when registering the GitHub webhook
GITHUB_TOKEN=     # GitHub personal access token
```

### Run

```bash
uvicorn main:app --reload --port 8000
```

In a separate terminal:

```bash
ngrok http 8000
```

### Register the Webhook

1. Go to your target GitHub repo → **Settings → Webhooks → Add webhook**
2. Payload URL: `https://<your-ngrok-url>/webhook`
3. Content type: `application/json`
4. Secret: value of `WEBHOOK_SECRET` from your `.env`
5. Events: **Pull requests** only

Open a PR on the repo — your terminal will print the PR number, title, and unified diff for each changed file.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `WEBHOOK_SECRET` | Secret used to verify GitHub webhook signatures |
| `GITHUB_TOKEN` | GitHub PAT for fetching PR diffs and posting comments |

In production (Lambda), these are stored in **AWS Secrets Manager** — never hardcoded or committed.

## Security

- All webhook payloads are verified via HMAC-SHA256 (`X-Hub-Signature-256`) before processing
- Credentials are stored in AWS Secrets Manager, accessed at Lambda cold start
- The Lambda IAM role is scoped to only the secrets it needs
