"""Deterministic AI Provider for automated tests and offline development."""

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.ai.providers.base import BaseAIProvider, AICompletionResponse

logger = logging.getLogger(__name__)


def generate_dynamic_mock_workflow(prompt: str) -> Dict[str, Any]:
    """Dynamically synthesize a tailored, valid DAG workflow based on user prompt intent."""
    p_lower = prompt.lower()

    if any(k in p_lower for k in ["backup", "s3", "archive", "storage", "database backup"]):
        return {
            "name": "Automated Database Backup & S3 Archival Pipeline",
            "description": "Periodically snapshots databases, encrypts archive dumps, and uploads them to secure S3 bucket with retention auditing.",
            "explanation": "A resilient infrastructure maintenance pipeline configured to snapshot target database clusters, compress and encrypt dumps, verify checksum integrity, and dispatch backup alerts.",
            "suggested_integrations": ["AWS_S3", "SLACK"],
            "graph": {
                "nodes": [
                    {
                        "id": "node-1",
                        "type": "scheduleTrigger",
                        "label": "Schedule: Daily Midnight Backup",
                        "position": {"x": 100.0, "y": 180.0},
                        "config": {"cron": "0 0 * * *"},
                    },
                    {
                        "id": "node-2",
                        "type": "transform",
                        "label": "DB Cluster Snapshot & Encryption",
                        "position": {"x": 420.0, "y": 180.0},
                        "config": {"encryption": "AES-256", "format": "tar.gz"},
                    },
                    {
                        "id": "node-3",
                        "type": "output",
                        "label": "S3 Sync: Upload to Encrypted Bucket",
                        "position": {"x": 740.0, "y": 180.0},
                        "config": {"bucket": "flowpilot-backups-prod", "region": "us-east-1"},
                    },
                    {
                        "id": "node-4",
                        "type": "notification",
                        "label": "DevOps Alert: Confirm Backup Success",
                        "position": {"x": 1060.0, "y": 180.0},
                        "config": {"channel": "#infra-ops"},
                    },
                ],
                "edges": [
                    {"id": "e1-2", "source": "node-1", "target": "node-2"},
                    {"id": "e2-3", "source": "node-2", "target": "node-3"},
                    {"id": "e3-4", "source": "node-3", "target": "node-4"},
                ],
            },
        }

    if any(k in p_lower for k in ["slack", "ticket", "webhook", "support", "inquiry", "inquiries", "sentiment", "discord", "helpdesk"]):
        return {
            "name": "Customer Inquiries & Slack Alert Pipeline",
            "description": "Ingests customer tickets via webhook, classifies sentiment and priority with AI, drafts resolution, and alerts the support team on Slack after lead review.",
            "explanation": "This workflow listens for inbound customer inquiry webhooks, uses the AI Analyst to classify sentiment and detect high urgency, drafts an automated response, pauses for team lead approval on critical cases, and dispatches the alert to Slack.",
            "suggested_integrations": ["SLACK", "WEBHOOK"],
            "graph": {
                "nodes": [
                    {
                        "id": "node-1",
                        "type": "webhookTrigger",
                        "label": "HTTP Webhook: Ingest Inquiry",
                        "position": {"x": 100.0, "y": 180.0},
                        "config": {"method": "POST", "path": "/webhooks/inquiries"},
                    },
                    {
                        "id": "node-2",
                        "type": "textClassifier",
                        "label": "AI Analyst: Sentiment & Urgency",
                        "position": {"x": 420.0, "y": 180.0},
                        "config": {"categories": ["Urgent", "High Priority", "Normal", "Feedback"]},
                    },
                    {
                        "id": "node-3",
                        "type": "aiAgent",
                        "label": "AI Resolver: Draft Triage & Solution",
                        "position": {"x": 740.0, "y": 180.0},
                        "config": {"role": "Customer Support Engineer", "tone": "Empathetic and Actionable"},
                    },
                    {
                        "id": "node-4",
                        "type": "humanApproval",
                        "label": "Lead Approval: Verify High-Priority Action",
                        "position": {"x": 1060.0, "y": 180.0},
                        "config": {"action": "DISPATCH_SLACK_NOTIFICATION", "timeout_hours": 12},
                    },
                    {
                        "id": "node-5",
                        "type": "notification",
                        "label": "Slack: Broadcast Alert to #incidents",
                        "position": {"x": 1380.0, "y": 180.0},
                        "config": {"channel": "#customer-incidents"},
                    },
                ],
                "edges": [
                    {"id": "e1-2", "source": "node-1", "target": "node-2"},
                    {"id": "e2-3", "source": "node-2", "target": "node-3"},
                    {"id": "e3-4", "source": "node-3", "target": "node-4"},
                    {"id": "e4-5", "source": "node-4", "target": "node-5"},
                ],
            },
        }

    if any(k in p_lower for k in ["invoice", "invoices", "financial", "rag", "pdf", "document", "documents", "finance", "accounting", "billing", "expenses"]):
        return {
            "name": "Automated Invoice Audit & RAG Reconciliation",
            "description": "Retrieves invoice documents, extracts financial line items via RAG vector search, verifies contract compliance, and logs to accounting.",
            "explanation": "A scheduled accounting pipeline that extracts line items from invoices, queries the Knowledge Base vector index for rate verification, requests managerial payment authorization, and syncs approved records to accounting.",
            "suggested_integrations": ["GMAIL", "KNOWLEDGE_BASE"],
            "graph": {
                "nodes": [
                    {
                        "id": "node-1",
                        "type": "scheduleTrigger",
                        "label": "Schedule: Daily Invoice Poll",
                        "position": {"x": 100.0, "y": 180.0},
                        "config": {"cron": "0 8 * * *"},
                    },
                    {
                        "id": "node-2",
                        "type": "dataExtractor",
                        "label": "PDF & Table Data Extractor",
                        "position": {"x": 420.0, "y": 180.0},
                        "config": {"fields": ["vendor", "amount", "due_date", "invoice_id"]},
                    },
                    {
                        "id": "node-3",
                        "type": "aiAgent",
                        "label": "RAG Auditor: Rate Compliance Check",
                        "position": {"x": 740.0, "y": 180.0},
                        "config": {"knowledge_base": "Vendor Contracts", "similarity_threshold": 0.82},
                    },
                    {
                        "id": "node-4",
                        "type": "humanApproval",
                        "label": "Finance Signoff: Authorize Payment",
                        "position": {"x": 1060.0, "y": 180.0},
                        "config": {"action": "APPROVE_INVOICE_PAYMENT", "timeout_hours": 48},
                    },
                    {
                        "id": "node-5",
                        "type": "output",
                        "label": "Accounting Sync: Export to Ledger",
                        "position": {"x": 1380.0, "y": 180.0},
                        "config": {"destination": "Accounting ERP"},
                    },
                ],
                "edges": [
                    {"id": "e1-2", "source": "node-1", "target": "node-2"},
                    {"id": "e2-3", "source": "node-2", "target": "node-3"},
                    {"id": "e3-4", "source": "node-3", "target": "node-4"},
                    {"id": "e4-5", "source": "node-4", "target": "node-5"},
                ],
            },
        }

    if any(k in p_lower for k in ["github", "git", "pr", "pull request", "code", "commit", "deploy", "security", "vulnerability", "ci/cd", "devops"]):
        return {
            "name": "Autonomous GitHub PR & Security Compliance Review",
            "description": "Monitors GitHub repository events, analyzes pull request diffs for security vulnerabilities, and publishes review feedback upon engineer signoff.",
            "explanation": "Triggered by pull request webhooks, this pipeline inspects code changes, performs automated static security analysis, requests senior engineer approval, and submits automated review comments to GitHub.",
            "suggested_integrations": ["GITHUB"],
            "graph": {
                "nodes": [
                    {
                        "id": "node-1",
                        "type": "webhookTrigger",
                        "label": "GitHub Webhook: Pull Request Event",
                        "position": {"x": 100.0, "y": 180.0},
                        "config": {"events": ["pull_request.opened", "pull_request.synchronize"]},
                    },
                    {
                        "id": "node-2",
                        "type": "dataExtractor",
                        "label": "Code Diff & Patch Extractor",
                        "position": {"x": 420.0, "y": 180.0},
                        "config": {"max_lines": 500},
                    },
                    {
                        "id": "node-3",
                        "type": "aiAgent",
                        "label": "DevSecOps Scanner: OWASP Vulnerability Audit",
                        "position": {"x": 740.0, "y": 180.0},
                        "config": {"checks": ["OWASP Top 10", "Secret Leaks", "Code Quality"]},
                    },
                    {
                        "id": "node-4",
                        "type": "humanApproval",
                        "label": "Staff Engineer Review: Signoff Security Gate",
                        "position": {"x": 1060.0, "y": 180.0},
                        "config": {"action": "MERGE_GATE_PASS", "timeout_hours": 24},
                    },
                    {
                        "id": "node-5",
                        "type": "output",
                        "label": "GitHub API: Submit PR Review Comments",
                        "position": {"x": 1380.0, "y": 180.0},
                        "config": {"event": "COMMENT"},
                    },
                ],
                "edges": [
                    {"id": "e1-2", "source": "node-1", "target": "node-2"},
                    {"id": "e2-3", "source": "node-2", "target": "node-3"},
                    {"id": "e3-4", "source": "node-3", "target": "node-4"},
                    {"id": "e4-5", "source": "node-4", "target": "node-5"},
                ],
            },
        }

    if any(k in p_lower for k in ["marketing", "lead", "leads", "social", "twitter", "linkedin", "campaign", "outreach"]):
        return {
            "name": "Autonomous Lead Enrichment & Outreach Pipeline",
            "description": "Enriches incoming prospective leads, crafts personalized outreach copy based on company profile, and stages emails for marketing approval.",
            "explanation": "Captures prospective lead data, enriches corporate profiles using AI agents, drafts customized value propositions, and requires marketing signoff before dispatch.",
            "suggested_integrations": ["GMAIL", "SLACK"],
            "graph": {
                "nodes": [
                    {
                        "id": "node-1",
                        "type": "manualTrigger",
                        "label": "Manual Trigger: Ingest Lead Batch",
                        "position": {"x": 100.0, "y": 180.0},
                        "config": {},
                    },
                    {
                        "id": "node-2",
                        "type": "dataExtractor",
                        "label": "Lead Profile & Firmographic Extractor",
                        "position": {"x": 420.0, "y": 180.0},
                        "config": {"fields": ["company", "role", "interests"]},
                    },
                    {
                        "id": "node-3",
                        "type": "aiAgent",
                        "label": "AI Copywriter: Draft Personalized Pitch",
                        "position": {"x": 740.0, "y": 180.0},
                        "config": {"tone": "Friendly, professional", "model": "gemini-1.5-pro"},
                    },
                    {
                        "id": "node-4",
                        "type": "humanApproval",
                        "label": "Marketing Review: Approve Outreach Copy",
                        "position": {"x": 1060.0, "y": 180.0},
                        "config": {"action": "DISPATCH_CAMPAIGN"},
                    },
                    {
                        "id": "node-5",
                        "type": "output",
                        "label": "Dispatch Outreach: Send Email Batch",
                        "position": {"x": 1380.0, "y": 180.0},
                        "config": {"destination": "Gmail API"},
                    },
                ],
                "edges": [
                    {"id": "e1-2", "source": "node-1", "target": "node-2"},
                    {"id": "e2-3", "source": "node-2", "target": "node-3"},
                    {"id": "e3-4", "source": "node-3", "target": "node-4"},
                    {"id": "e4-5", "source": "node-4", "target": "node-5"},
                ],
            },
        }

    # Clean custom title from prompt words
    words = [w.capitalize() for w in prompt.replace(".", " ").replace(",", " ").replace("-", " ").split() if len(w) > 3 and w.lower() not in ["with", "from", "that", "this", "every", "your", "before", "after", "into"]]
    custom_title = " ".join(words[:4]) if words else "Autonomous Task"
    if not custom_title.startswith("Autonomous"):
        custom_title = f"Autonomous {custom_title}"
    if not custom_title.endswith("Workflow") and not custom_title.endswith("Pipeline"):
        custom_title = f"{custom_title} Pipeline"

    return {
        "name": custom_title,
        "description": f"Automated pipeline tailored to objective: {prompt.strip()}",
        "explanation": f"This tailored DAG workflow was architected for: '{prompt.strip()}'. It provisions a primary event trigger, processes data through specialized AI reasoning nodes, pauses at a human-in-the-loop approval gate for safety, and concludes with an automated action dispatch.",
        "suggested_integrations": ["GMAIL", "SLACK"],
        "graph": {
            "nodes": [
                {
                    "id": "node-1",
                    "type": "scheduleTrigger" if "schedule" in p_lower or "daily" in p_lower or "every" in p_lower else "manualTrigger",
                    "label": f"{custom_title}: Event Trigger",
                    "position": {"x": 100.0, "y": 180.0},
                    "config": {},
                },
                {
                    "id": "node-2",
                    "type": "textClassifier" if "classify" in p_lower or "filter" in p_lower else "dataExtractor",
                    "label": "AI Analyst: Context Extraction & Triage",
                    "position": {"x": 420.0, "y": 180.0},
                    "config": {"prompt": prompt},
                },
                {
                    "id": "node-3",
                    "type": "aiAgent",
                    "label": "AI Executive Agent: Logic & Generation",
                    "position": {"x": 740.0, "y": 180.0},
                    "config": {"objective": prompt},
                },
                {
                    "id": "node-4",
                    "type": "humanApproval",
                    "label": "Human Gate: Review & Authorize",
                    "position": {"x": 1060.0, "y": 180.0},
                    "config": {"action": "AUTHORIZE_WORKFLOW_EXECUTION", "timeout_hours": 24},
                },
                {
                    "id": "node-5",
                    "type": "output",
                    "label": "Terminal Action: Dispatch Output",
                    "position": {"x": 1380.0, "y": 180.0},
                    "config": {"status": "SUCCESS"},
                },
            ],
            "edges": [
                {"id": "e1-2", "source": "node-1", "target": "node-2"},
                {"id": "e2-3", "source": "node-2", "target": "node-3"},
                {"id": "e3-4", "source": "node-3", "target": "node-4"},
                {"id": "e4-5", "source": "node-4", "target": "node-5"},
            ],
        },
    }


class MockAIProvider(BaseAIProvider):
    """Deterministic local AI provider returning intelligent mock responses without network."""

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AICompletionResponse:
        logger.info(f"MockAIProvider generating completion for: {prompt[:80]}...")
        if "classify" in prompt.lower():
            content = "Classification: URGENT. Category: Client Request. Confidence: 0.94"
        elif "summarize" in prompt.lower() or "summary" in prompt.lower():
            content = "Summary: Sender requested a status update on Q4 cloud migration deliverables with urgent priority."
        elif "reply" in prompt.lower() or "draft" in prompt.lower():
            content = "Hello, thank you for checking in. The deliverables are on track for completion by Friday."
        else:
            content = f"FlowPilot AI processed objective: {prompt[:100]}"

        return AICompletionResponse(
            content=content,
            prompt_tokens=len(prompt) // 4,
            completion_tokens=len(content) // 4,
            total_tokens=(len(prompt) + len(content)) // 4,
            model="flowpilot-mock-deterministic-v1",
            provider="mock",
        )

    async def complete_structured(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        logger.info(f"MockAIProvider generating structured schema output for: {schema.__name__}")
        schema_name = schema.__name__

        if "Workflow" in schema_name or "Generate" in schema_name:
            return generate_dynamic_mock_workflow(prompt)

        # Generic default mock conforming to schema
        mock_data: Dict[str, Any] = {}
        for field_name, field_info in schema.model_fields.items():
            field_type = str(field_info.annotation)
            if "str" in field_type:
                mock_data[field_name] = f"Mock {field_name}"
            elif "int" in field_type:
                mock_data[field_name] = 1
            elif "float" in field_type:
                mock_data[field_name] = 0.95
            elif "bool" in field_type:
                mock_data[field_name] = True
            elif "list" in field_type or "List" in field_type:
                mock_data[field_name] = []
            elif "dict" in field_type or "Dict" in field_type:
                mock_data[field_name] = {}
            else:
                mock_data[field_name] = None
        return mock_data

    async def get_embedding(self, text: str) -> List[float]:
        # Generate deterministic 384-dimensional vector from SHA256 of text
        hasher = hashlib.sha256(text.encode("utf-8")).digest()
        vector = [(b / 255.0) * 2.0 - 1.0 for b in hasher]
        # Pad to 384 dimensions
        while len(vector) < 384:
            vector.extend(vector[: min(384 - len(vector), len(vector))])
        return vector[:384]
