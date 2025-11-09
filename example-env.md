ДЛЯ ФРОНТЕНДА

NEXT_PUBLIC_ENV_MODE="staging" #production, or staging
NEXT_PUBLIC_SUPABASE_URL="https://ftnuwrhhkcvcsiqqebtm.supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ0bnV3cmhoa2N2Y3NpcXFlYnRtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI1NzQ4MDMsImV4cCI6MjA3ODE1MDgwM30.yLj5pSgDHUbbD7jfEnURZh0kWBHb_zRoIWuWQoCXmC4"
NEXT_PUBLIC_BACKEND_URL="http://localhost:8000/api"
NEXT_PUBLIC_URL="http://localhost:3000"
NEXT_PUBLIC_GOOGLE_CLIENT_ID=""
NEXT_PUBLIC_POSTHOG_KEY=""
KORTIX_ADMIN_API_KEY=""
EDGE_CONFIG="https://edge-config.vercel.com/REDACTED?token=REDACTED"

ДЛЯ БЕКЕНДА

## Copy this file to .env and fill values.
## Required keys are marked REQUIRED. Others are optional.

# Environment Mode
# Valid values: local, staging, production
ENV_MODE=local

##### DATABASE (REQUIRED)
SUPABASE_URL=https://ftnuwrhhkcvcsiqqebtm.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ0bnV3cmhoa2N2Y3NpcXFlYnRtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI1NzQ4MDMsImV4cCI6MjA3ODE1MDgwM30.yLj5pSgDHUbbD7jfEnURZh0kWBHb_zRoIWuWQoCXmC4
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ0bnV3cmhoa2N2Y3NpcXFlYnRtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjU3NDgwMywiZXhwIjoyMDc4MTUwODAzfQ.lvQpCvckQy0GH2V8T0xMwMhzC85IKkVeShGnqiY12rM

##### REDIS
# Use "redis" when using docker compose, or "localhost" for fully local
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
# Set false for local/docker compose
REDIS_SSL=false

##### LLM PROVIDERS (At least one is functionally REQUIRED)
# Provide at least one of the following:
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GROQ_API_KEY=
OPENROUTER_API_KEY=
GEMINI_API_KEY=
XAI_API_KEY=

# AWS Bedrock (only if using Bedrock)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION_NAME=

# OpenAI-compatible
OPENAI_COMPATIBLE_API_KEY=OGYzZTJhM2UtNmYzNy00MjAzLTg0OWMtMWJlNjE3NzI4NTI2.d41d6d26ad8ef380779322401dad19f2
OPENAI_COMPATIBLE_API_BASE=https://foundation-models.api.cloud.ru/v1

##### DATA / SEARCH (REQUIRED)
RAPID_API_KEY=
TAVILY_API_KEY=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

##### WEB SCRAPE (REQUIRED)
FIRECRAWL_API_KEY=fc-5790a7a3bc204ce296306ddbc7671eee
# Default used if empty: https://api.firecrawl.dev
FIRECRAWL_URL=

##### AGENT SANDBOX (REQUIRED to use Daytona sandbox)
DAYTONA_API_KEY=dtn_1aa8ff012f9d329fbf2d7e5a70c968cb09fbb8d96cc225a9657a670beb252d5d
DAYTONA_SERVER_URL=https://app.daytona.io/api
DAYTONA_TARGET=us

##### SECURITY & WEBHOOKS (Recommended)
MCP_CREDENTIAL_ENCRYPTION_KEY=
TRIGGER_WEBHOOK_SECRET=

##### OBSERVABILITY (Optional)
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com

##### BILLING (Optional;)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_DEFAULT_PLAN_ID=
STRIPE_DEFAULT_TRIAL_DAYS=14

##### ADMIN
KORTIX_ADMIN_API_KEY=

##### INTEGRATIONS
COMPOSIO_API_KEY=
COMPOSIO_WEBHOOK_SECRET=
COMPOSIO_API_BASE=https://backend.composio.dev

##### GOOGLE INTEGRATIONS (Optional; for Google Slides upload)
# Google OAuth credentials for Google Slides integration
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/google/callback

ZENDESK_AUTH_CONFIG=""
EXA_API_KEY=""

CHUNKR_API_KEY=""
