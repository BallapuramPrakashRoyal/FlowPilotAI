"""Knowledge Base & RAG API endpoints: document uploads, chunking, and similarity query."""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.dependencies import get_current_workspace
from app.database.models import Workspace, KnowledgeBase, Document, DocumentChunk
from app.ai.rag.service import RAGService

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Base & RAG"])


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: Optional[str] = None
    document_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class QueryRAGRequest(BaseModel):
    knowledge_base_id: str
    query: str
    top_k: Optional[int] = 3


@router.get("/", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.workspace_id == workspace.id)
    )
    kbs = res.scalars().all()
    out = []
    for kb in kbs:
        doc_count_res = await db.execute(
            select(Document).where(Document.knowledge_base_id == kb.id)
        )
        count = len(doc_count_res.scalars().all())
        out.append(KnowledgeBaseResponse(
            id=kb.id,
            workspace_id=kb.workspace_id,
            name=kb.name,
            description=kb.description,
            document_count=count,
        ))
    return out


@router.post("/", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    kb = KnowledgeBase(
        workspace_id=workspace.id,
        name=payload.name,
        description=payload.description,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return KnowledgeBaseResponse(
        id=kb.id,
        workspace_id=kb.workspace_id,
        name=kb.name,
        description=kb.description,
        document_count=0,
    )


@router.post("/upload")
async def upload_document(
    knowledge_base_id: str = Form(...),
    file: UploadFile = File(...),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    # Verify knowledge base belongs to workspace
    kb_res = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id, KnowledgeBase.workspace_id == workspace.id)
    )
    kb = kb_res.scalars().first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    content_bytes = await file.read()
    rag_service = RAGService()
    extracted_text = rag_service.extract_text_from_file(file.filename, content_bytes)

    doc = Document(
        knowledge_base_id=kb.id,
        filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=len(content_bytes),
        status="INDEXING",
    )
    db.add(doc)
    await db.flush()

    chunk_count = await rag_service.index_document(db, doc.id, extracted_text)
    doc.chunk_count = chunk_count
    doc.status = "INDEXED"
    await db.commit()

    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "chunks_indexed": chunk_count,
        "status": "INDEXED",
    }


@router.post("/query")
async def query_rag(
    payload: QueryRAGRequest,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    rag_service = RAGService()
    kb_res = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == payload.knowledge_base_id,
            KnowledgeBase.workspace_id == workspace.id,
        )
    )
    if not kb_res.scalars().first():
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    results = await rag_service.search_similar(
        db=db,
        knowledge_base_id=payload.knowledge_base_id,
        query=payload.query,
        top_k=payload.top_k or 3,
    )
    return {"query": payload.query, "citations": results}
