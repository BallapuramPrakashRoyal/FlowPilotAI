# AI workflow generator

The generator accepts natural-language workflow requirements and returns a
Pydantic-validated graph. It can only use node types registered by the
backend. The graph is validated before it is returned and is never
automatically published or executed.

Users can review the generated graph, open it in Workflow Studio, edit it, and
explicitly save or publish it. Sensitive actions such as email sending remain
behind the human approval node.

Provider failures are surfaced to the API caller; credentials and provider
configuration are never returned to the browser.

Generated workflows execute asynchronously through Celery when configured.
The execution inspector reads persisted nodes and events, including available
provider/model/token metadata. Cost is shown only when workspace pricing has
been explicitly configured.
