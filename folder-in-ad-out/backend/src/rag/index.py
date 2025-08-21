import os
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Use environment variable or default path
DB_PATH = os.getenv("VECTOR_STORE", "./src/rag/index_db")

def get_collection(name="brand_style"):
    """Get or create ChromaDB collection with 0.5.x API"""
    try:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        
        # Create client with modern API
        client = chromadb.PersistentClient(path=DB_PATH)
        
        # Create embedding function
        embedding_function = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get or create collection
        collection = client.get_or_create_collection(
            name=name,
            embedding_function=embedding_function
        )
        
        return collection
        
    except ImportError:
        logger.warning("ChromaDB not available, RAG features disabled")
        return None
    except Exception as e:
        logger.error(f"ChromaDB initialization failed: {e}")
        return None

def upsert_docs(docs: List[Dict]):
    """Upsert documents to ChromaDB collection"""
    try:
        collection = get_collection()
        if collection is None:
            logger.warning("ChromaDB not available, skipping document upsert")
            return
            
        collection.upsert(
            ids=[doc["id"] for doc in docs],
            documents=[doc["text"] for doc in docs],
            metadatas=[doc.get("metadata", {}) for doc in docs]
        )
        
        logger.info(f"Upserted {len(docs)} documents to ChromaDB")
        
    except Exception as e:
        logger.error(f"Document upsert failed: {e}")

def search(query: str, k: int = 3) -> str:
    """Search documents and return concatenated results"""
    try:
        collection = get_collection()
        if collection is None:
            logger.warning("ChromaDB not available for search")
            return ""
            
        results = collection.query(
            query_texts=[query],
            n_results=k
        )
        
        # Extract documents from results
        documents = results.get("documents", [[]])[0]
        
        if not documents:
            logger.info(f"No documents found for query: {query}")
            return ""
            
        # Join results with separator
        combined = "\n\n".join(documents)
        logger.info(f"Found {len(documents)} documents for query")
        
        return combined
        
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        return ""

def initialize_knowledge_base():
    """Initialize RAG knowledge base with default documents"""
    try:
        # Load documents from the documents directory
        docs_dir = Path(__file__).parent / "documents"
        if not docs_dir.exists():
            logger.info("No documents directory found, skipping RAG initialization")
            return
            
        documents = []
        for file_path in docs_dir.glob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                documents.append({
                    "id": file_path.stem,
                    "text": content,
                    "metadata": {
                        "source": str(file_path),
                        "type": "knowledge_base"
                    }
                })
            except Exception as e:
                logger.error(f"Failed to read {file_path}: {e}")
        
        if documents:
            upsert_docs(documents)
            logger.info(f"Initialized knowledge base with {len(documents)} documents")
        else:
            logger.info("No documents found to initialize knowledge base")
            
    except Exception as e:
        logger.error(f"Knowledge base initialization failed: {e}")

def get_brand_context(query: str) -> str:
    """Get brand context for script generation (optional RAG)"""
    try:
        context = search(query, k=2)
        if context:
            return f"Brand guidelines:\n{context}\n\n"
        return ""
    except Exception:
        # Gracefully handle RAG failures
        return ""

class StyleRAGIndex:
    """Legacy compatibility class - use module functions instead"""
    
    def __init__(self, persist_directory: str = None):
        logger.warning("StyleRAGIndex is deprecated, use module functions instead")
        self._initialized = False
        self.persist_directory = persist_directory or DB_PATH
        self.collection = None
    
    def initialize(self):
        """Initialize the RAG index"""
        try:
            self.collection = get_collection("style_guidance")
            self._initialized = (self.collection is not None)
            if self._initialized:
                logger.info("StyleRAGIndex initialized successfully")
            else:
                logger.warning("StyleRAGIndex initialization failed - ChromaDB not available")
        except Exception as e:
            logger.error(f"StyleRAGIndex initialization failed: {e}")
            self._initialized = False
    
    def add_documents(self, documents: List[Dict[str, str]]):
        """Add documents to the index"""
        if not self._initialized:
            self.initialize()
            
        if not self._initialized or not self.collection:
            logger.warning("RAG index not available")
            return False
            
        try:
            # Convert legacy format to new format
            docs = []
            for i, doc in enumerate(documents):
                doc_id = doc.get('id', f"doc_{i}")
                text = doc.get('content', '')
                metadata = {
                    'title': doc.get('title', ''),
                    'category': doc.get('category', 'general'),
                    'tone': doc.get('tone', ''),
                    'source': doc.get('source', 'manual')
                }
                
                docs.append({
                    'id': doc_id,
                    'text': text,
                    'metadata': metadata
                })
            
            # Use modern API
            upsert_docs(docs)
            logger.info(f"Added {len(documents)} documents to RAG index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to RAG index: {e}")
            return False
    
    def search(self, query: str, n_results: int = 3) -> List[str]:
        """Search for relevant style guidance"""
        if not self._initialized:
            self.initialize()
            
        if not self._initialized or not self.collection:
            logger.warning("RAG index not available for search")
            return []
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Extract document texts
            documents = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            
            # Combine text with context
            formatted_results = []
            for doc, meta in zip(documents, metadatas):
                context = f"[{meta.get('category', 'general')}] {doc}"
                formatted_results.append(context)
            
            logger.debug(f"Found {len(formatted_results)} relevant documents for query: '{query[:50]}...'")
            return formatted_results
            
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return []
    
    def get_collection_info(self) -> Dict:
        """Get information about the collection"""
        if not self._initialized:
            self.initialize()
            
        if not self._initialized or not self.collection:
            return {"error": "RAG index not available"}
        
        try:
            count = self.collection.count()
            return {
                "document_count": count,
                "collection_name": "style_guidance",
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"error": str(e)}

# Global instance
_rag_index = StyleRAGIndex()

def initialize_rag_system():
    """Initialize the RAG system with seed documents"""
    logger.info("Initializing RAG system...")
    
    try:
        # Check if we already have documents using modern API
        collection = get_collection("brand_style")
        if collection is None:
            logger.warning("ChromaDB not available, RAG system not initialized")
            return
            
        existing_count = collection.count()
        if existing_count > 0:
            logger.info(f"RAG system already has {existing_count} documents")
            return
        
        # Add seed documents using modern API
        seed_docs = get_seed_documents()
        if seed_docs:
            # Convert to modern format
            docs = []
            for doc in seed_docs:
                docs.append({
                    'id': doc['id'],
                    'text': doc['content'],
                    'metadata': {
                        'title': doc.get('title', ''),
                        'category': doc.get('category', 'general'),
                        'tone': doc.get('tone', ''),
                        'source': doc.get('source', 'builtin')
                    }
                })
            
            upsert_docs(docs)
            logger.info(f"Added {len(seed_docs)} seed documents to RAG system")
        else:
            logger.info("No seed documents to add")
            
    except Exception as e:
        logger.error(f"RAG system initialization failed: {e}")

def fetch_style_hints(prompt: str) -> str:
    """Fetch style hints based on prompt - main interface for agents"""
    try:
        # Use modern search API
        results_text = search(prompt, k=2)
        if results_text:
            return results_text
        else:
            return ""
    except Exception as e:
        logger.error(f"Error fetching style hints: {e}")
        return ""

def get_seed_documents() -> List[Dict[str, str]]:
    """Create seed documents for the RAG system"""
    
    # Check if documents directory exists and load from files
    docs_dir = Path(__file__).parent / "documents"
    documents = []
    
    # Load from files if they exist
    if docs_dir.exists():
        for file_path in docs_dir.glob("*.md"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract title from filename
                title = file_path.stem.replace('_', ' ').title()
                
                documents.append({
                    'id': f"file_{file_path.stem}",
                    'title': title,
                    'content': content,
                    'category': 'style_guide',
                    'source': 'file'
                })
                
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
    
    # Add built-in seed documents if no files found
    if not documents:
        documents = [
            {
                'id': 'confident_tone',
                'title': 'Confident Tone Guidelines',
                'content': """
Confident tone characteristics:
- Use strong, declarative statements
- Avoid hedging language (maybe, might, could)
- Focus on benefits and outcomes
- Use active voice
- Include social proof and authority
- End with clear calls-to-action

Examples:
- "Transform your business today" vs "This might help your business"
- "Proven results in 30 days" vs "Could see results eventually"
- "Join thousands of satisfied customers" vs "Some people like our product"
""",
                'category': 'tone',
                'tone': 'confident',
                'source': 'builtin'
            },
            {
                'id': 'friendly_tone',
                'title': 'Friendly Tone Guidelines',
                'content': """
Friendly tone characteristics:
- Use conversational language
- Include personal pronouns (you, we, our)
- Ask rhetorical questions
- Use inclusive language
- Add warmth with appropriate emoji or casual phrases
- Focus on helping and supporting

Examples:
- "We're here to help you succeed"
- "Have you ever wondered how to..."
- "Let's solve this together"
- "You deserve the best"
""",
                'category': 'tone',
                'tone': 'friendly',
                'source': 'builtin'
            },
            {
                'id': 'professional_tone',
                'title': 'Professional Tone Guidelines',
                'content': """
Professional tone characteristics:
- Use industry-specific terminology appropriately
- Maintain formal but accessible language
- Focus on expertise and credibility
- Include facts, figures, and data
- Use structured, logical flow
- Emphasize quality and reliability

Examples:
- "Industry-leading solutions"
- "Backed by 20 years of experience"
- "Proven methodology"
- "Enterprise-grade security"
""",
                'category': 'tone',
                'tone': 'professional',
                'source': 'builtin'
            },
            {
                'id': 'short_form_structure',
                'title': 'Short-Form Ad Structure',
                'content': """
Effective short-form ad structure (15-30 seconds):
1. Hook: Grab attention immediately
2. Problem: Identify pain point quickly
3. Solution: Present your offer clearly
4. Benefit: Show the transformation
5. CTA: Clear, specific next step

Best practices:
- First 3 seconds are crucial
- One main message only
- Use visual-first storytelling
- End with urgent CTA
- Test multiple hooks
""",
                'category': 'structure',
                'source': 'builtin'
            },
            {
                'id': 'brand_safety',
                'title': 'Brand Safety Guidelines',
                'content': """
Brand-safe content guidelines:
- Avoid controversial topics
- Use inclusive, respectful language
- Fact-check all claims
- Include appropriate disclaimers
- Respect copyright and trademarks
- Follow platform guidelines
- Consider diverse audiences

Red flags to avoid:
- Unrealistic promises
- Discriminatory language
- Misleading comparisons
- Violation of platform policies
- Cultural insensitivity
""",
                'category': 'safety',
                'source': 'builtin'
            }
        ]
    
    logger.info(f"Generated {len(documents)} seed documents")
    return documents