# Local app with TAMUS-hosted Claude Opus 4.6

The website and database can stay on your computer while explicit tutor discussions call a remote TAMUS model. `AI_PROVIDER=cloud` describes where inference runs, not where the website is hosted. No public deployment, domain, or direct Anthropic/OpenAI account is required when your TAMUS key authorizes the chosen model. Training, grading and worked solutions remain deterministic and work without inference.

## Obtain the exact endpoint and model ID

The owner-provided documentation is https://docs.tamus.ai/docs/prod/api-tool/create-and-test-api-key . It required Cloudflare Access sign-in during implementation, so the exact TAMUS endpoint, model ID and deployed output-cap behavior have **not** been independently verified. Do not substitute the browser chat URL, guess a gateway model prefix, or use a direct Anthropic key with a TAMUS endpoint.

Sign into that page in your own browser. Copy its non-secret API prefix and the model ID for **Claude Opus 4.6**. A provider may use a different ID from Anthropic's direct `claude-opus-4-6`. Our adapter appends `/chat/completions` to `AI_BASE_URL`; if the documentation's complete request URL ends in `/api/chat/completions`, the base must end in `/api`. Use whatever exact prefix your TAMUS documentation shows, not that example by assumption.

You can discover the model ID locally without sending a prompt or disclosing the key in chat:

```bash
backend/.venv/bin/python scripts/list_ai_models.py --base-url https://YOUR-EXACT-API-PREFIX
```

This prompts for the API key with hidden input, sends only `GET <base>/models`, lists IDs/names matching `opus`, and neither saves nor prints the key. To list all returned models, add `--filter ""`. A model-list error does not prove chat is unsupported; use the provider's documented model ID when model discovery is unavailable. No model-list request or live inference has been made with real credentials during implementation.

Alternatively, run `make ai-models` to be prompted for both the non-secret base URL and the hidden key.

## Private configuration

Copy `.env.example` to `.env` only if `.env` does not already exist, then edit the ignored `.env` file locally. Do not paste a key into chat or frontend code.

```dotenv
APP_ENV=development
PUBLIC_ORIGIN=http://localhost:5173
COOKIE_SECURE=false
AI_PROVIDER=cloud
AI_ENABLED=false
AI_BASE_URL=https://YOUR-EXACT-API-PREFIX
AI_MODEL=YOUR-EXACT-CLAUDE-OPUS-4-6-ID
AI_API_KEY=YOUR-TAMUS-KEY
AI_CAP_VERIFIED=false
AI_MAX_INPUT_TOKENS=6000
AI_MAX_OUTPUT_TOKENS=1500
```

Keep inference disabled until the documented endpoint is compatible with Bearer-authenticated, non-streaming Chat Completions and actually enforces the requested `max_tokens` cap with conservative input bounds. Once verified, change `AI_CAP_VERIFIED=true` and `AI_ENABLED=true`. This flag is an operator attestation, not an automatic certification. Restart `make dev` after `.env` changes; the development file watcher does not guarantee reloading environment files. Request/token quotas remain in force and do not constitute a guaranteed dollar cap.

## Approve your local browser once

The current app keeps the same approval boundary for local use:

1. Run `make admin` and create your owner login through its private password prompt.
2. Start/restart `make dev`, open `/admin/login`, and sign in.
3. Issue a single-use invitation in Admin. Redeem it under Settings → AI access in the browser profile you use for practice.
4. Submit a practice answer and choose Discuss this problem. Only pressing Send makes an inference request.

A successful model-list request does not verify a generated answer or cap semantics. Those need a separately authorized, bounded live test using your credential. Never use the synthetic browser-test server as the real app.

Sources: [TAMU Developer AI](https://www.it.tamu.edu.prod.sites-it.cloud.tamu.edu/ai/tools/developer-ai.html), [Anthropic's Opus 4.6 announcement](https://www.anthropic.com/news/claude-opus-4-6), and [Open WebUI API reference](https://docs.openwebui.com/reference/api-endpoints/). TAMU links to Open WebUI documentation, but this does not by itself establish the exact TAMUS deployment version or model configuration.
