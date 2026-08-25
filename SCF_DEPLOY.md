# 腾讯云 SCF 定点推送部署指南（邮件版）

> 目标：用腾讯云定时触发器，在 **精准的北京时间 7:00** 触发 GitHub Actions 发邮件，
> 解决 GitHub 自带 cron「不准时 / 偶发跳过」的痛点。
> 费用：SCF 每月 100 万次调用免费额度，每天触发 1 次，**零成本**。

---

## 当前触发设计
- **主触发（morning）**：腾讯云 SCF 定时器 `0 0 7 * * * *`，北京时间 07:00 调用 `workflow_dispatch`（mode=morning）。
- **主触发（evening）**：腾讯云 SCF 定时器 `0 0 22 * * * *`，北京时间 22:00 调用 `workflow_dispatch`（mode=evening）。
- **GitHub 自带 cron 已关闭**：`daily.yml` 仅保留 `workflow_dispatch`，不靠 GitHub 定时，避免与 SCF 重复触发。
- **防重复**：`main.py` 内置「同日同模式已发则跳过」逻辑，不会重复发送。

---

## 部署步骤

### 1. 准备一个 GitHub PAT（用于触发工作流）
- 地址：https://github.com/settings/tokens -> Generate new token (classic)
- 勾选 `repo`（含 `public_repo` / `repo:status`）即可触发 `workflow_dispatch`
- 复制生成的 `ghp_xxx`，下面填进 SCF 环境变量 `GH_PAT`

### 2. 新建 SCF 函数
- 控制台：https://console.cloud.tencent.com/scf
- 「函数服务」-> 新建 -> 自定义创建
- 函数名称：`kaogong-daily-trigger`
- 运行环境：**Python 3.10**（或 3.9+）
- 提交方法：在线编辑 / 上传代码（把本目录 `scf_trigger.py` 内容贴进去）
- 函数入口：`scf_trigger.main_handler`

### 3. 配置环境变量（函数配置 -> 环境变量）
| 键 | 值 |
|---|---|
| `GH_PAT` | 步骤 1 生成的 `ghp_xxx` |
| `GH_REPO` | `你的用户名/你的仓库名`（例如 `yourname/kaogong-daily`） |
| `GH_WORKFLOW` | `daily.yml` |
| `GH_REF` | `main` |

### 4. 配置定时触发器
- 「触发管理」-> 创建触发器 -> 触发方式：**定时触发**
- 触发周期（Cron）：`0 0 7 * * * *`
  （腾讯 SCF 为 7 段式：秒 分 时 日 月 周 年 -> 每天 07:00:00）
- 时区：**Asia/Shanghai（中国标准时间）**
- 自定义触发时间：勾选「启用」

### 5. 测试
- 在 SCF 控制台点「测试」，返回日志应为 `{"ok": true, "http_code": 204}`
- 去 GitHub 仓库 Actions 页确认出现一条新的 `workflow_dispatch` 运行，邮箱收到邮件。

---

## 排查
- `http_code 404`：`GH_REPO` / `GH_WORKFLOW` 写错，或 PAT 无该仓库权限。
- `http_code 401/403`：PAT 失效或权限不足（需 `repo`）。
- 邮件没收到但 Actions 显示成功：检查 163 邮箱授权码 / 收件人配置（见仓库 README）。
