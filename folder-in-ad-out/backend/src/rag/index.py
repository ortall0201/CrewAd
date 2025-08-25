# backend/src/rag/index.py
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Storage location: default under backend/src/rag/index_db
# You can override with env: VECTOR_STORE="C:/path/to/dir"
# -------------------------------------------------------------------
_DEFAULT_DIR = Path(__file__).resolve().parent / "index_db"
DB_DIR: Path = Path(os.getenv("VECTOR_STORE", _DEFAULT_DIR)).resolve()
DB_DIR.mkdir(parents=True, exist_ok=True)  # ensure folder exists

# Singletons (lazy-initialized)
_client = None
_embedding_fn = None


def _get_client():
    """Lazy, cached chroma PersistentClient."""
    global _client
    if _client is not None:
        return _client
    try:
        import chromadb
        _client = chromadb.PersistentClient(path=str(DB_DIR))
        logger.info(f"Chroma PersistentClient initialized at: {DB_DIR}")
    except Exception as e:
        logger.warning(f"ChromaDB not available (RAG disabled): {e}")
        _client = None
    return _client


def _get_embedding_fn():
    """Lazy, cached sentence-transformer embedding function."""
    global _embedding_fn
    if _embedding_fn is not None:
        return _embedding_fn
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        _embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    except Exception as e:
        logger.warning(f"Embedding function unavailable: {e}")
        _embedding_fn = None
    return _embedding_fn


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------
def get_collection(name: str = "brand_style"):
    """
    Get or create a ChromaDB collection (0.5.x API).
    Returns None if Chroma is unavailable so callers can degrade gracefully.
    """
    client = _get_client()
    if client is None:
        return None

    emb = _get_embedding_fn()
    try:
        # In 0.5.x you can pass embedding_function when creating/getting collection
        coll = client.get_or_create_collection(name=name, embedding_function=emb)
        return coll
    except Exception as e:
        logger.error(f"Chroma get_or_create_collection failed: {e}")
        return None


def upsert_docs(docs: List[Dict]) -> None:
    """Upsert a list of {'id','text','metadata'} documents."""
    if not docs:
        return
    coll = get_collection()
    if coll is None:
        logger.warning("ChromaDB unavailable, skipping upsert")
        return
    try:
        ids = [str(doc["id"]) for doc in docs]
        documents = [str(doc.get("text", "")) for doc in docs]
        metadatas = [dict(doc.get("metadata", {})) for doc in docs]
        coll.upsert(ids=ids, documents=documents, metadatas=metadatas)
        logger.info(f"Upserted {len(ids)} docs into Chroma collection '{coll.name}'")
    except Exception as e:
        logger.error(f"Document upsert failed: {e}")


def search(query: str, k: int = 3) -> str:
    """Return '\n\n'-joined top-k documents for a query, or '' if none."""
    coll = get_collection()
    if coll is None:
        logger.warning("ChromaDB unavailable for search")
        return ""
    try:
        res = coll.query(query_texts=[query], n_results=max(1, k))
        # 0.5.x returns lists-of-lists
        docs = (res.get("documents") or [[]])[0]
        if not docs:
            logger.info(f"No RAG results for query: {query!r}")
            return ""
        return "\n\n".join(map(str, docs))
    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        return ""


def initialize_knowledge_base() -> None:
    """
    Optional bootstrap: load any markdown files from src/rag/documents/*.md
    and upsert them into the collection.
    """
    try:
        docs_dir = Path(__file__).resolve().parent / "documents"
        if not docs_dir.exists():
            logger.info("No documents directory found, skipping RAG bootstrap")
            return

        docs: List[Dict] = []
        for p in docs_dir.glob("*.md"):
            try:
                content = p.read_text(encoding="utf-8")
                docs.append(
                    {
                        "id": p.stem,
                        "text": content,
                        "metadata": {
                            "source": str(p),
                            "type": "knowledge_base",
                            "title": p.stem.replace("_", " ").title(),
                        },
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to read {p}: {e}")

        if docs:
            upsert_docs(docs)
            logger.info(f"Initialized knowledge base with {len(docs)} documents")
        else:
            logger.info("No markdown documents found for RAG bootstrap")
    except Exception as e:
        logger.error(f"Knowledge base initialization failed: {e}")


def get_brand_context(query: str) -> str:
    """Small helper to prefix RAG context for prompting (safe if empty)."""
    ctx = search(query, k=2)
    return f"Brand guidelines:\n{ctx}\n\n" if ctx else ""


# -------------------------------------------------------------------
# Legacy adapter (kept for compatibility)
# -------------------------------------------------------------------
class StyleRAGIndex:
    """
    Legacy compatibility class — prefer the module functions above.
    """

    def __init__(self, persist_directory: Optional[str] = None):
        logger.warning("StyleRAGIndex is deprecated; use module-level helpers instead")
        self.persist_directory = persist_directory or str(DB_DIR)
        self.collection = None
        self._initialized = False

    def initialize(self):
        self.collection = get_collection("style_guidance")
        self._initialized = self.collection is not None
        if self._initialized:
            logger.info("StyleRAGIndex initialized")
        else:
            logger.warning("StyleRAGIndex init failed (Chroma unavailable)")

    def add_documents(self, documents: List[Dict[str, str]]) -> bool:
        if not self._initialized:
            self.initialize()
        if not self._initialized or not self.collection:
            logger.warning("RAG index not available")
            return False

        try:
            docs = []
            for i, doc in enumerate(documents):
                docs.append(
                    {
                        "id": doc.get("id", f"doc_{i}"),
                        "text": doc.get("content", ""),
                        "metadata": {
                            "title": doc.get("title", ""),
                            "category": doc.get("category", "general"),
                            "tone": doc.get("tone", ""),
                            "source": doc.get("source", "manual"),
                        },
                    }
                )
            upsert_docs(docs)
            logger.info(f"Added {len(documents)} docs to legacy RAG index")
            return True
        except Exception as e:
            logger.error(f"Legacy add_documents failed: {e}")
            return False

    def search(self, query: str, n_results: int = 3) -> List[str]:
        if not self._initialized:
            self.initialize()
        if not self._initialized or not self.collection:
            logger.warning("RAG index not available for search")
            return []
        try:
            res = self.collection.query(query_texts=[query], n_results=max(1, n_results))
            docs = (res.get("documents") or [[]])[0]
            metas = (res.get("metadatas") or [[]])[0]
            results: List[str] = []
            for d, m in zip(docs, metas):
                cat = (m or {}).get("category", "general")
                results.append(f"[{cat}] {d}")
            return results
        except Exception as e:
            logger.error(f"Legacy search failed: {e}")
            return []

    def get_collection_info(self) -> Dict:
        if not self._initialized:
            self.initialize()
        if not self._initialized or not self.collection:
            return {"error": "RAG index not available"}
        try:
            return {
                "document_count": self.collection.count(),
                "collection_name": self.collection.name,
                "persist_directory": self.persist_directory,
            }
        except Exception as e:
            return {"error": str(e)}


# -------------------------------------------------------------------
# Optional seed loading
# -------------------------------------------------------------------
def get_seed_documents() -> List[Dict[str, str]]:
    """Built-in seed docs (used by initialize_rag_system)."""
    docs_dir = Path(__file__).resolve().parent / "documents"
    docs: List[Dict[str, str]] = []

    # Load .md files if present
    if docs_dir.exists():
        for p in docs_dir.glob("*.md"):
            try:
                content = p.read_text(encoding="utf-8")
                docs.append(
                    {
                        "id": f"file_{p.stem}",
                        "title": p.stem.replace("_", " ").title(),
                        "content": content,
                        "category": "style_guide",
                        "source": "file",
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to load {p}: {e}")

    # Built-in defaults if no files
    if not docs:
        docs = [
            {
                "id": "confident_tone",
                "title": "Confident Tone Guidelines",
                "content": """Confident tone characteristics:
- Use strong, declarative statements
- Avoid hedging language
- Focus on benefits and outcomes
- Use active voice
- Include social proof and authority
- Clear calls-to-action""",
                "category": "tone",
                "tone": "confident",
                "source": "builtin",
            },
            {
                "id": "friendly_tone",
                "title": "Friendly Tone Guidelines",
                "content": """Friendly tone characteristics:
- Conversational language, inclusive pronouns
- Warmth and helpfulness
- Light rhetorical questions
- Supportive, positive phrasing""",
                "category": "tone",
                "tone": "friendly",
                "source": "builtin",
            },
            {
                "id": "professional_tone",
                "title": "Professional Tone Guidelines",
                "content": """Professional tone characteristics:
- Formal but accessible language
- Facts, figures, expertise
- Structured, logical flow
- Emphasize quality and reliability""",
                "category": "tone",
                "tone": "professional",
                "source": "builtin",
            },
            {
                "id": "short_form_structure",
                "title": "Short-Form Ad Structure",
                "content": """Effective short-form ad (15–30s):
1. Hook
2. Problem
3. Solution
4. Benefit
5. CTA""",
                "category": "structure",
                "source": "builtin",
            },
            {
                "id": "brand_safety",
                "title": "Brand Safety Guidelines",
                "content": """Brand-safe practices:
- Avoid controversy, respect copyrights
- Fact-check claims, add disclaimers
- Follow platform policies
- Inclusive language & diverse audiences""",
                "category": "safety",
                "source": "builtin",
            },
        ]

    logger.info(f"Generated {len(docs)} seed documents")
    return docs


def initialize_rag_system() -> None:
    """Initialize collection with seed docs only if empty."""
    coll = get_collection("brand_style")
    if coll is None:
        logger.warning("Chroma unavailable; RAG system not initialized")
        return
    try:
        if coll.count() > 0:
            logger.info(f"RAG collection '{coll.name}' already has documents")
            return
        seeds = get_seed_documents()
        if seeds:
            upsert_docs(
                [
                    {
                        "id": d["id"],
                        "text": d["content"],
                        "metadata": {
                            "title": d.get("title", ""),
                            "category": d.get("category", "general"),
                            "tone": d.get("tone", ""),
                            "source": d.get("source", "builtin"),
                        },
                    }
                    for d in seeds
                ]
            )
            logger.info(f"Seeded RAG with {len(seeds)} documents")
    except Exception as e:
        logger.error(f"RAG initialization failed: {e}")


def fetch_style_hints(prompt: str) -> str:
    """Primary helper for agents to retrieve style hints (safe to call)."""
    try:
        return search(prompt, k=2)
    except Exception as e:
        logger.error(f"fetch_style_hints error: {e}")
        return ""
