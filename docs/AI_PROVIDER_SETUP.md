# AI provider setup

Provider credentials are read only by the backend.

```env
DEFAULT_AI_PROVIDER=gemini
GEMINI_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
AI_REQUEST_TIMEOUT_SECONDS=60
AI_MAX_RETRIES=2
```

Pricing is intentionally opt-in. If workspace pricing is configured, use a
model-keyed object such as:

```json
{
  "model-name": {
    "prompt_per_1k": 0.001,
    "completion_per_1k": 0.002
  }
}
```

Without configured pricing, usage is recorded in tokens and estimated cost is
left `null`.

Use `DEFAULT_AI_PROVIDER=mock` for offline development and automated tests.
The mock provider must not be treated as a production AI provider. The
frontend never receives these values.

Authenticated provider endpoints:

- `GET /api/v1/ai/providers`
- `GET /api/v1/ai/providers/{provider_name}/health`
