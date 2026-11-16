# Agent tool registry

The server-owned registry is in `backend/app/ai/agents/tools.py`. Every tool
declares its input and output Pydantic schemas, permissions, timeout, approval
requirement, and handler.

Current safe tools:

- `text.transform`
- `text.classify`
- `knowledge.retrieve`

Unknown tools are rejected. Required permissions are checked against the
workspace-scoped execution context before invocation. Gmail tools are not
registered unless OAuth and scope validation are implemented; no Gmail
production capability is claimed by this milestone.

Authenticated API:

- `GET /api/v1/agents/tools`
- `POST /api/v1/agents/plan`
- `POST /api/v1/agents/run`
- `GET /api/v1/agents/runs/{execution_id}`
