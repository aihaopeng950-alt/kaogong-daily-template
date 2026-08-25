# -*- coding: utf-8 -*-
"""
腾讯云 SCF 定时触发器函数
作用：在精准的北京时间调用 GitHub API 触发 workflow_dispatch，
      由 GitHub Actions 完成天气查询 / 内容生成 / 163 邮件发送。
为什么需要它：GitHub 自带的 cron 在低频私有仓库上可能延迟数分钟甚至偶发跳过；
      用腾讯云定时触发器可保证准时「叫醒」Actions，规避延迟。
依赖：仅 Python 标准库（urllib），SCF 运行时无需 pip install。

部署：本文件作为 SCF 函数代码，部署两个函数：
  - kaogong-morning：环境变量 MODE=morning，定时触发器 cron = 0 0 7 * * * *（北京时间 07:00）
  - kaogong-evening：环境变量 MODE=evening，定时触发器 cron = 0 0 22 * * * *（北京时间 22:00）
函数共同环境变量：GH_PAT（GitHub token，需 repo+workflow 权限）、GH_REPO、GH_WORKFLOW、GH_REF
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
