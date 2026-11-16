# AI Architecture

FlowPilot's AI runtime is provider-independent and keeps provider credentials
server-side. Providers implement the shared `BaseAIProvider` contract and are
selected through environment configuration.

Supported providers are Gemini, Ollama, OpenAI-compatible chat APIs, and a
deterministic mock provider for offline development and tests.

Workflow generation is constrained by the backend node registry and validated
with the same DAG validator used by execution. A single bounded deterministic
repair may fill safe defaults; invalid graphs are rejected rather than
published or executed.

AI nodes execute through the durable DAG runner. Provider/model and token
metadata are recorded in execution token usage, while node inputs and outputs
remain inspectable through execution records. Sensitive operations pause at
`humanApproval`.

Workflow execution is dispatched to the registered Celery task when Redis is
available. A local background-task fallback is retained for development when
Redis is intentionally unavailable. The runner checks cancellation between
nodes, times out long-running nodes, retries bounded failures, and skips
already-succeeded nodes when recovering an interrupted execution.

Workspace AI configuration and usage records are tenant-scoped. Credentials
are encrypted with the existing Fernet utility and are never returned by the
configuration API. Trace inputs, outputs, contexts, and event payloads pass
through centralized redaction before persistence or response.

The two AI runtime tables (`workspace_ai_configs` and `ai_usage_records`) are
created non-destructively by the existing startup schema bootstrap. No existing
tables or data are dropped.
