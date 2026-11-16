"""Retrieval-Augmented Generation (RAG) Service: chunking, indexing, and similarity search."""

import io
import logging
import math
import time
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.ai.providers.factory import get_ai_provider
from app.database.models import KnowledgeBase, Document, DocumentChunk

logger = logging.getLogger(__name__)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class RAGService:
    """End-to-end RAG parsing, chunking, embedding, and vector retrieval."""

    def __init__(self, provider_name: Optional[str] = None):
        self.provider = get_ai_provider(provider_name)

    @classmethod
    def extract_text_from_file(cls, filename: str, content_bytes: bytes) -> str:
        """Extract plain text from PDF, DOCX, or plain text bytes."""
        fn = filename.lower()
        if fn.endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content_bytes))
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
            return text
        elif fn.endswith(".docx"):
            from docx import Document as DocxDoc
            doc = DocxDoc(io.BytesIO(content_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        else:
            # UTF-8 plain text fallback
            return content_bytes.decode("utf-8", errors="replace")

    @classmethod
    def chunk_text(cls, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i : i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
            i += chunk_size - overlap
        return chunks if chunks else [text]

    async def index_document(
        self,
        db: AsyncSession,
        document_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Generate embeddings and index document chunks."""
        chunks = self.chunk_text(text)
        logger.info(f"Indexing document {document_id} into {len(chunks)} chunks.")

        meta = dict(metadata or {})
        for idx, chunk_content in enumerate(chunks):
            embedding = await self.provider.get_embedding(chunk_content)
            chunk_meta = dict(meta)
            chunk_meta["char_length"] = len(chunk_content)
            chunk_meta["word_count"] = len(chunk_content.split())
            chunk_rec = DocumentChunk(
                document_id=document_id,
                chunk_index=idx,
                content=chunk_content,
                embedding_json=embedding,
                metadata_json=chunk_meta,
            )
            db.add(chunk_rec)

        await db.commit()
        return len(chunks)

    async def search_workspace(
        self,
        db: AsyncSession,
        workspace_id: str,
        query: str,
        knowledge_base_id: Optional[str] = None,
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Workspace-isolated vector similarity search across documents."""
        start_time = time.perf_counter()

        # Handle empty query gracefully
        if not query or not query.strip():
            return {
                "results": [],
                "trace": {
                    "query": query,
                    "workspace_id": workspace_id,
                    "chunks_evaluated": 0,
                    "returned_count": 0,
                    "duration_ms": 0,
                },
            }

        query_vector = await self.provider.get_embedding(query)

        # Enforce workspace isolation by joining KnowledgeBase
        stmt = (
            select(DocumentChunk, Document.filename, KnowledgeBase.id.label("kb_id"), KnowledgeBase.name.label("kb_name"))
            .join(Document, DocumentChunk.document_id == Document.id)
            .join(KnowledgeBase, Document.knowledge_base_id == KnowledgeBase.id)
            .where(KnowledgeBase.workspace_id == workspace_id)
        )
        if knowledge_base_id:
            stmt = stmt.where(KnowledgeBase.id == knowledge_base_id)

        res = await db.execute(stmt)
        rows = res.all()

        scored = []
        for chunk, filename, kb_id, kb_name in rows:
            chunk_meta = chunk.metadata_json or {}
            # Apply metadata filter if specified
            if metadata_filter:
                match = True
                for k, v in metadata_filter.items():
                    if chunk_meta.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            emb = chunk.embedding_json or []
            score = cosine_similarity(query_vector, emb)
            scored.append({
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "filename": filename,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "similarity_score": round(score, 4),
                "metadata": chunk_meta,
                "source": {
                    "document_id": chunk.document_id,
                    "filename": filename,
                    "chunk_index": chunk.chunk_index,
                    "knowledge_base_id": kb_id,
                    "knowledge_base_name": kb_name,
                },
            })

        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        results = scored[: max(1, top_k)]
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        trace = {
            "query": query,
            "workspace_id": workspace_id,
            "knowledge_base_id": knowledge_base_id,
            "chunks_evaluated": len(rows),
            "matched_count": len(scored),
            "top_k": top_k,
            "duration_ms": elapsed_ms,
        }

        return {"results": results, "trace": trace}

    async def search_similar(
        self,
        db: AsyncSession,
        knowledge_base_id: str,
        query: str,
        top_k: int = 3,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve most relevant chunks in a specific knowledge base using vector cosine similarity."""
        # Find workspace_id from knowledge_base
        kb_res = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id))
        kb = kb_res.scalars().first()
        workspace_id = kb.workspace_id if kb else ""

        search_res = await self.search_workspace(
            db=db,
            workspace_id=workspace_id,
            query=query,
            knowledge_base_id=knowledge_base_id,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )
        return search_res["results"]
