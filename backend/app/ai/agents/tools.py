"""Permission-aware, server-owned tool registry for agents."""

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from app.integrations.gmail.service import GmailService


class ToolContext(BaseModel):
    workspace_id: str
    permissions: set[str] = Field(default_factory=set)
    access_token: Optional[str] = None
    db: Any = None
    execution_id: Optional[str] = None
    is_approved: bool = False

    model_config = {"arbitrary_types_allowed": True}


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    required_permissions: frozenset[str]
    requires_approval: bool
    timeout_seconds: float
    handler: Callable[[Dict[str, Any], ToolContext], Awaitable[Dict[str, Any]]]


# Schemas
class TextInput(BaseModel):
    text: str


class TextOutput(BaseModel):
    text: str


class ClassificationInput(BaseModel):
    text: str
    categories: list[str] = Field(default_factory=list)


class ClassificationOutput(BaseModel):
    category: str
    confidence: float


class KnowledgeSearchInput(BaseModel):
    query: str
    knowledge_base_id: Optional[str] = None
    top_k: int = 5
    metadata_filter: Optional[Dict[str, Any]] = None


class KnowledgeSearchOutput(BaseModel):
    results: list[dict[str, Any]] = Field(default_factory=list)
    trace: dict[str, Any] = Field(default_factory=dict)


class GmailListInput(BaseModel):
    max_results: int = 5


class GmailListOutput(BaseModel):
    unread_count: int
    emails: list[dict[str, Any]] = Field(default_factory=list)


class GmailGetMessageInput(BaseModel):
    message_id: str


class GmailGetMessageOutput(BaseModel):
    id: str
    thread_id: Optional[str] = None
    sender: str
    subject: str
    snippet: str
    body: str
    received_at: str
    labels: list[str] = Field(default_factory=list)


class GmailSearchInput(BaseModel):
    query: str
    max_results: int = 10


class GmailSearchOutput(BaseModel):
    query: str
    count: int
    messages: list[dict[str, Any]] = Field(default_factory=list)


class GmailContentInput(BaseModel):
    message_id: str


class GmailContentOutput(BaseModel):
    id: str
    thread_id: Optional[str] = None
    headers: dict[str, str] = Field(default_factory=dict)
    snippet: str
    body: str


class GmailDraftInput(BaseModel):
    recipient: str
    subject: str
    body: str
    thread_id: Optional[str] = None


class GmailDraftOutput(BaseModel):
    id: Optional[str] = None
    status: str
    recipient: str
    subject: str
    thread_id: Optional[str] = None


class GmailSendInput(BaseModel):
    recipient: str
    subject: str
    body: str
    thread_id: Optional[str] = None


class GmailSendOutput(BaseModel):
    status: str
    recipient: str
    subject: str
    message_id: Optional[str] = None


# Handlers
async def transform_text(payload: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
    return {"text": payload["text"].strip()}


async def classify_text(payload: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
    text = payload["text"].lower()
    categories = payload.get("categories", [])
    category = categories[0] if categories else "Uncategorized"
    if "urgent" in text and "Urgent" in categories:
        category = "Urgent"
    return {"category": category, "confidence": 0.9 if category == "Urgent" else 0.5}


async def retrieve_knowledge(payload: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
    """Retrieve workspace-scoped knowledge chunks using vector similarity."""
    from app.ai.rag.service import RAGService
    from app.core import database

    query = payload.get("query", "")
    kb_id = payload.get("knowledge_base_id")
    top_k = payload.get("top_k", 5)
    meta_filter = payload.get("metadata_filter")

    rag = RAGService()
    if context.db:
        return await rag.search_workspace(
            db=context.db,
            workspace_id=context.workspace_id,
            query=query,
            knowledge_base_id=kb_id,
            top_k=top_k,
            metadata_filter=meta_filter,
        )
    else:
        async with database.AsyncSessionLocal() as session:
            return await rag.search_workspace(
                db=session,
                workspace_id=context.workspace_id,
                query=query,
                knowledge_base_id=kb_id,
                top_k=top_k,
                metadata_filter=meta_filter,
            )


async def gmail_list_unread(payload: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
    service = GmailService(access_token=context.access_token)
    emails = await service.fetch_unread_messages(max_results=payload.get("max_results", 5))
    return {"unread_count": len(emails), "emails": emails}


async def gmail_get_message(payload: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
    service = GmailService(access_token=context.access_token)
    return await service.get_message_details(payload["message_id"])


async def gmail_search(payload: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
    service = GmailService(access_token=context.access_token)
    msgs = await service.search_emails(payload["query"], max_results=payload.get("max_results", 10))
    return {"query": payload["query"], "count": len(msgs), "messages": msgs}


async def gmail_get_content(payload: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
    service = GmailService(access_token=context.access_token)
    return await service.get_message_content(payload["message_id"])


async def gmail_create_draft(payload: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
    service = GmailService(access_token=context.access_token)
    res = await service.create_draft(
        recipient=payload["recipient"],
        subject=payload["subject"],
        body=payload["body"],
        thread_id=payload.get("thread_id"),
    )
    return {
        "id": res.get("id", res.get("draft_id")),
        "status": "DRAFT_CREATED",
        "recipient": payload["recipient"],
        "subject": payload["subject"],
        "thread_id": payload.get("thread_id"),
    }


async def gmail_send_email(payload: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
    if not context.is_approved:
        raise PermissionError("Tool 'gmail.send_email' requires explicit human approval before execution")

    service = GmailService(access_token=context.access_token)
    res = await service.send_email(
        recipient=payload["recipient"],
        subject=payload["subject"],
        body=payload["body"],
        thread_id=payload.get("thread_id"),
    )
    return {
        "status": "SENT",
        "recipient": payload["recipient"],
        "subject": payload["subject"],
        "message_id": res.get("id", res.get("message_id")),
    }


# Registry
TOOL_REGISTRY: Dict[str, ToolDefinition] = {
    "text.transform": ToolDefinition(
        "text.transform", "Normalize text", TextInput, TextOutput, frozenset(), False, 10, transform_text
    ),
    "text.classify": ToolDefinition(
        "text.classify", "Classify text into allowed categories", ClassificationInput,
        ClassificationOutput, frozenset(), False, 30, classify_text
    ),
    "knowledge.retrieve": ToolDefinition(
        "knowledge.retrieve", "Retrieve authorized workspace knowledge", KnowledgeSearchInput,
        KnowledgeSearchOutput, frozenset({"knowledge:read"}), False, 30, retrieve_knowledge
    ),
    "gmail.list_unread": ToolDefinition(
        "gmail.list_unread", "List unread emails from authorized Gmail inbox", GmailListInput,
        GmailListOutput, frozenset({"gmail:read"}), False, 30, gmail_list_unread
    ),
    "gmail.get_message": ToolDefinition(
        "gmail.get_message", "Retrieve email message metadata and snippet", GmailGetMessageInput,
        GmailGetMessageOutput, frozenset({"gmail:read"}), False, 30, gmail_get_message
    ),
    "gmail.search": ToolDefinition(
        "gmail.search", "Search emails using Gmail queries", GmailSearchInput,
        GmailSearchOutput, frozenset({"gmail:read"}), False, 30, gmail_search
    ),
    "gmail.get_content": ToolDefinition(
        "gmail.get_content", "Retrieve full decoded content and headers of an email", GmailContentInput,
        GmailContentOutput, frozenset({"gmail:read"}), False, 30, gmail_get_content
    ),
    "gmail.create_draft": ToolDefinition(
        "gmail.create_draft", "Create an email draft in Gmail", GmailDraftInput,
        GmailDraftOutput, frozenset({"gmail:draft"}), False, 30, gmail_create_draft
    ),
    "gmail.send_email": ToolDefinition(
        "gmail.send_email", "Send an email (requires human approval)", GmailSendInput,
        GmailSendOutput, frozenset({"gmail:send"}), True, 30, gmail_send_email
    ),
}


def get_tool(name: str) -> ToolDefinition:
    try:
        return TOOL_REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"Unknown agent tool '{name}'") from exc


async def invoke_tool(name: str, payload: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
    definition = get_tool(name)
    if not definition.required_permissions.issubset(context.permissions):
        raise PermissionError(f"Missing permissions for tool '{name}'")
    if definition.requires_approval and not context.is_approved:
        raise PermissionError(f"Tool '{name}' requires explicit human approval before execution")
    validated = definition.input_schema.model_validate(payload)
    result = await definition.handler(validated.model_dump(), context)
    return definition.output_schema.model_validate(result).model_dump()
