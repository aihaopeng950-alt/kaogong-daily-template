# 考公每日推送工具（开源模板）

每天 **早 7:00 / 晚 22:00** 自动向邮箱推送：天气、公考常识、时政、申论五位一体素材、培训班课表、距离国考倒计时。

## 怎么用（3 步）
1. 点仓库右上角 **Use this template**（或 Fork）→ 生成你自己的仓库副本。
2. 在你自己的仓库 `Settings → Secrets and variables → Actions` 里填 **6 个密钥**（见下）。
3. 配置定时触发：腾讯云 SCF 定时器，或启用 `daily.yml` 里预留的 GitHub 自带 schedule（详见 `复刻使用说明.html`）。

## 6 个密钥（只在你自己的仓库填）
- 邮箱类：`EMAIL_USER` / `EMAIL_AUTH_CODE` / `EMAIL_TO`（发件用 163 邮箱）
- 大模型类：`LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`（DeepSeek 兼容接口）

## 完整教程
打开仓库里的 **`复刻使用说明.html`**，复制头部「给 AI 的总段提示词」发给 WorkBuddy，
AI 会自动读取本仓库全部代码并帮你完成部署——无需你手写任何代码。

> 本仓库为模板，不含任何私密信息；密钥请只在你自己的仓库里配置。
