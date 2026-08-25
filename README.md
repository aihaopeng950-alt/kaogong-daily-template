# kaogong-daily

Automated daily email push for Chinese civil-service (gongkao) exam prep.

Runs entirely on GitHub Actions. No local computer needed.

## What it sends
- Morning (~07:00 Beijing): knowledge point + current affairs + shenglun (essay) material (Five-in-One) + idiom pairs + national-exam countdown banner.
- Evening (~22:00 Beijing): next-day weather + next-day class schedule + study plan.

## Setup
1. Fork / use this template to create your own repo.
2. Add these Secrets in Settings -> Secrets and variables -> Actions:
   - EMAIL_USER, EMAIL_AUTH_CODE, EMAIL_TO
   - LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
3. The workflow `daily.yml` already contains a schedule; enable Actions if needed.

(c) ahp
