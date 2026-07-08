# Deploy Sustainable Catalyst Workbench FastAPI Backend on Render

This backend powers the advanced calculators, graph generation, model registry, and AI assistant for the WordPress Workbench plugin.

## Recommended deployment path

Use Render connected to the GitHub repository:

`Content-Catalyst-LLC/sustainable-catalyst-workbench`

Render can deploy this repo using the included `render.yaml` Blueprint or by manually creating a Web Service.

## Manual Render settings

Create a new **Web Service** from the GitHub repo and use:

- **Root Directory:** `backend`
- **Runtime:** Python 3
- **Build Command:** `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command:** `./start.sh`
- **Health Check Path:** `/health`

## Environment variables

Set these in Render:

```text
SC_WORKBENCH_ENVIRONMENT=production
SC_WORKBENCH_AI_PROVIDER=openai
OPENAI_API_KEY=<your OpenAI key>
SC_WORKBENCH_OPENAI_MODEL=gpt-4.1-mini
SC_WORKBENCH_MAX_OUTPUT_TOKENS=1000
SC_WORKBENCH_TEMPERATURE=0.2
SC_WORKBENCH_ALLOW_WORDPRESS_PROVIDER_KEY=true
SC_WORKBENCH_SCOPE_GATE=true
SC_WORKBENCH_CORS_ORIGINS=https://sustainablecatalyst.com
SC_WORKBENCH_BACKEND_KEY=<optional shared secret>
```

If you set `SC_WORKBENCH_BACKEND_KEY`, paste the same value into:

`WordPress Admin → SC Workbench → Settings → API Key`

For first deployment, leave `SC_WORKBENCH_BACKEND_KEY` blank until health checks pass.

## Test URLs

Replace `<backend-url>` with your Render URL.

```bash
curl https://<backend-url>/health
curl https://<backend-url>/ai/status
curl https://<backend-url>/tools | head
```

Expected health output:

```json
{"ok":true,"status":"healthy","version":"0.7.2"}
```

## Configure WordPress

Go to:

`WordPress Admin → SC Workbench → Settings`

Set:

```text
Backend URL: https://<backend-url>
API Key: same as SC_WORKBENCH_BACKEND_KEY, or blank if none
Enable AI panels: Enabled
Enable scope gate: Enabled
Debug mode: Disabled
```

Then click **Test Backend + AI**.

## Notes

- `127.0.0.1:8088` is local-only and will not work from the live Sustainable Catalyst WordPress server.
- Keep `OPENAI_API_KEY` only in Render environment variables or a server-side `.env`, not in GitHub.
- The WordPress-managed OpenAI key option still works if `SC_WORKBENCH_ALLOW_WORDPRESS_PROVIDER_KEY=true`, but server-side environment variables are preferred for production.


## v0.7.3 Gemini/DeepSeek route

For the free-first path, set the Render service to:

```text
SC_WORKBENCH_AI_PROVIDER=gemini
GEMINI_API_KEY=<your Gemini API key>
SC_WORKBENCH_GEMINI_MODEL=gemini-3.5-flash
```

To switch to DeepSeek later:

```text
SC_WORKBENCH_AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=<your DeepSeek API key>
SC_WORKBENCH_DEEPSEEK_MODEL=deepseek-v4-flash
```

Keep OpenAI optional:

```text
SC_WORKBENCH_AI_PROVIDER=openai
OPENAI_API_KEY=<your OpenAI API key>
```
