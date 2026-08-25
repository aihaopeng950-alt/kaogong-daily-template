# -*- coding: utf-8 -*-
"""
 SCF 
 GitHub API  workflow_dispatch
       GitHub Actions  /  / 163 
GitHub  cron 
      Actions
 Python urllibSCF  pip install

 SCF 
  - kaogong-morning MODE=morning cron = 0 0 7 * * * * 07:00
  - kaogong-evening MODE=evening cron = 0 0 22 * * * * 22:00
GH_PATGitHub token repo+workflow GH_REPOGH_WORKFLOWGH_REF
"""

import os
import json
import urllib.request
import urllib.error

GITHUB_API = "https://api.github.com"


def main_handler(event, context):
    token = os.environ.get("GH_PAT") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GH_REPO", "aihaopeng950-alt/kaogong-daily")
    workflow = os.environ.get("GH_WORKFLOW", "daily.yml")
    ref = os.environ.get("GH_REF", "main")
    mode = os.environ.get("MODE", "")  # morning / evening，由函数环境变量决定

    if not token:
        return {"ok": False, "error": "缺少 GH_PAT 环境变量（请在函数配置里设置）"}

    url = f"{GITHUB_API}/repos/{repo}/actions/workflows/{workflow}/dispatches"
    payload = {"ref": ref}
    if mode:
        payload["inputs"] = {"mode": mode}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "tencent-scf-kaogong-trigger")

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            code = resp.getcode()
            body = resp.read().decode("utf-8", "ignore")
            return {"ok": 200 <= code < 300, "mode": mode, "http_code": code, "body": body[:300]}
    except urllib.error.HTTPError as e:
        return {"ok": False, "mode": mode, "http_code": e.code,
                "body": e.read().decode("utf-8", "ignore")[:300]}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "mode": mode, "error": str(e)}
