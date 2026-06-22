import hashlib
import hmac
import json
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request

load_dotenv()

app = FastAPI()

# Retrieve from .env
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN", "")

# Recomputes HMAC-SHA256 hash of the payload using webhook secret to compare to x_hub_signature_256
def verify_signature(payload: bytes, sig_header: str) -> bool:
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig_header)

@app.post("/webhook")
async def handle_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str     = Header(None),
):
    payload = await request.body()

    if not verify_signature(payload, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if x_github_event != "pull_request":
        return {"status": "ignored", "event": x_github_event}

    data   = json.loads(payload)
    action = data["action"]

    if action not in ("opened", "synchronize"):
        return {"status": "ignored", "action": action}

    pr     = data["pull_request"]
    owner  = data["repository"]["owner"]["login"]
    repo   = data["repository"]["name"]
    pr_num = pr["number"]
    title  = pr["title"]

    print(f"\nPR #{pr_num}: {title}")
    print(f"Repo: {owner}/{repo}")

    files = await fetch_pr_files(owner, repo, pr_num)
    for f in files:
        print(f"\n--- {f['filename']} (+{f['additions']} -{f['deletions']}) ---")
        print(f.get("patch", "(binary or no diff)"))

    return {"status": "ok", "pr": pr_num, "files": len(files)}

# Get all PR files using GitHub API
async def fetch_pr_files(owner: str, repo: str, pr_num: int) -> list:
    url     = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}/files"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept":        "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()