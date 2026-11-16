"""Natural-language Workflow Planner and Structured Graph Generator."""

import logging
from typing import Any, Dict, List
from pydantic import BaseModel

from app.ai.providers.factory import get_ai_provider
from app.engine.dag import DAG, DAGValidationError
from app.schemas.workflow import WorkflowGenerateResponse, WorkflowGraphSchema, WorkflowNodeSchema, WorkflowEdgeSchema

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are FlowPilot AI's Principal Workflow Architect.
Your role is to translate user natural language instructions into a strictly valid, directed acyclic graph (DAG) workflow.

Available Capability Registry:
- manualTrigger: Manual user button trigger
- scheduleTrigger: Cron or periodic schedule trigger
- gmailTrigger: Polls unread emails, fetches subject, sender, body, attachments
- aiAgent: Multi-agent logical reasoning, task execution, or drafting
- llmCompletion: Direct prompt completion
- textClassifier: Tagging categories (e.g. Urgent, Normal, Spam)
- dataExtractor: JSON and entity extraction
- condition: Branching logic (if/else)
- transform: Data mapping and templating
- httpIntegration: Outbound webhook or REST API request
- humanApproval: Pauses execution until approved by an authenticated user
- delay: Waits for specified duration
- notification: Internal or Slack/email alerts
- output: Final outcome or terminal action

Rules:
1. Always start with a Trigger node (e.g., manualTrigger, gmailTrigger).
2. For sensitive external actions (sending emails, modifying records), ALWAYS precede with a 'humanApproval' node!
3. Never create loops or cyclical dependencies.
4. Ensure every node has a clear, sensible label and configuration.
"""


class WorkflowPlanner:
    """Orchestrates LLM planning to produce executable workflow graphs."""

    def __init__(self, provider_name: str = None):
        self.provider = get_ai_provider(provider_name)

    async def generate_workflow(self, user_prompt: str) -> WorkflowGenerateResponse:
        """Analyze user prompt, plan workflow, generate structured graph, and validate DAG."""
        logger.info(f"Generating workflow plan for prompt: '{user_prompt}'")

        data = await self.provider.complete_structured(
            prompt=f"Design an end-to-end autonomous workflow for this requirement:\n'{user_prompt}'",
            schema=WorkflowGenerateResponse,
            system_prompt=SYSTEM_PROMPT,
        )

        response = WorkflowGenerateResponse(**data)

        # Validate generated graph structure
        raw_nodes = [n.model_dump() for n in response.graph.nodes]
        raw_edges = [e.model_dump() for e in response.graph.edges]
        dag = DAG(raw_nodes, raw_edges)
        is_valid, errors, warnings = dag.validate()

        if not is_valid:
            logger.warning(f"Generated workflow had validation issues: {errors}. Running automatic graph repair.")
            # Auto-repair fallback: ensure valid linear execution
            response = self._repair_graph(response)

        return response

    def _repair_graph(self, response: WorkflowGenerateResponse) -> WorkflowGenerateResponse:
        """Perform one bounded, deterministic repair before returning a graph."""
        defaults = {
            "scheduletrigger": {"cron": "0 9 * * *"},
            "llmcompletion": {"prompt": "Process the upstream context."},
            "transform": {"mapping": {}},
            "httpintegration": {"url": "https://example.invalid", "method": "POST"},
        }
        for node in response.graph.nodes:
            node_type = node.type.lower()
            for key, value in defaults.get(node_type, {}).items():
                node.config.setdefault(key, value)

        if not any(n.type.lower().endswith("trigger") for n in response.graph.nodes):
            trigger = WorkflowNodeSchema(
                id="trigger-start",
                type="manualTrigger",
                label="Manual Start Trigger",
                position={"x": 50.0, "y": 150.0},
                config={},
            )
            response.graph.nodes.insert(0, trigger)
            if response.graph.nodes[1:]:
                first_target = response.graph.nodes[1].id
                response.graph.edges.insert(0, WorkflowEdgeSchema(id="edge-start", source="trigger-start", target=first_target))

        dag = DAG(
            [node.model_dump() for node in response.graph.nodes],
            [edge.model_dump() for edge in response.graph.edges],
        )
        valid, errors, _ = dag.validate()
        if not valid:
            raise ValueError(f"Generated workflow failed validation after bounded repair: {'; '.join(errors)}")
        return response
