# Ollama for AttendVortex (production)

Runs Ollama behind a Caddy reverse proxy with HTTPS and a bearer-token
check so only the AttendVortex backend (which sends `OLLAMA_API_KEY`)
can use it.

## Requirements

- A small VPS (any provider) with at least 4 GB RAM and Docker + Docker Compose.
- A domain name whose DNS A record points at the VPS IP.

## Model sizing (CPU-only)

| RAM on VPS | Recommended model            |
| ---------- | ---------------------------- |
| 4 GB       | `qwen3:4b` or `llama3.2:3b`  |
| 8 GB       | `llama3` (8B, Q4, slower)    |

Llama 3.2 1B/3B run comfortably on 4 GB. Do not try to run a model that
needs more RAM than the box has.

## Quickstart

1. Copy the env file and fill it in:
   ```bash
   cp .env.example .env
   # edit .env: set LLM_DOMAIN to your domain, OLLAMA_API_TOKEN to a long random string
   ```
2. Start the stack:
   ```bash
   docker compose up -d
   ```
3. Pull the model you chose:
   ```bash
   docker compose exec ollama ollama pull llama3
   ```
4. Verify from the VPS itself:
   ```bash
   curl -s -H "Authorization: Bearer $OLLAMA_API_TOKEN" https://llm.example.com/api/tags
   # expect JSON listing the pulled model
   curl -s https://llm.example.com/api/tags
   # expect HTTP 401 without the token
   ```
5. Verify from your Windows machine (Ollama is now public; only reachable
   with the token above).

## Render backend environment variables

Set these on the Render backend service and redeploy:

```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=https://llm.example.com
OLLAMA_MODEL=llama3
OLLAMA_API_KEY=<same token as OLLAMA_API_TOKEN>
```

## Verify end to end

```bash
curl https://<render-domain>/api/v1/ai/status
# expect: {"available": true, ..., "message": "LLM service is reachable"}
```

The Caddy reverse proxy requires a bearer token on every request; the
backend sends it automatically whenever `OLLAMA_API_KEY` is set.