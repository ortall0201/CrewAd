import os
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class StyleRAGIndex:
    """Simple RAG system for style guidance using ChromaDB"""
    
    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or "./backend/src/rag/index_db"
        self.collection = None
        self._initialized = False
        
    def initialize(self):
        """Initialize ChromaDB collection"""
        if self._initialized:
            return
            
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Create client with persistent storage
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="style_guidance",
                metadata={"description": "Style guidance for ad copywriting"}
            )
            
            self._initialized = True
            logger.info(f"RAG index initialized at {self.persist_directory}")
            
        except ImportError:
            logger.warning("ChromaDB not available, RAG features disabled")
            self._initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize RAG index: {e}")
            self._initialized = False
    
    def add_documents(self, documents: List[Dict[str, str]]):
        """Add documents to the index"""
        if not self._initialized:
            self.initialize()
            
        if not self._initialized or not self.collection:
            logger.warning("RAG index not available")
            return False
            
        try:
            # Prepare data for ChromaDB
            ids = []
            texts = []
            metadatas = []
            
            for i, doc in enumerate(documents):
                doc_id = doc.get('id', f"doc_{i}")
                text = doc.get('content', '')
                metadata = {
                    'title': doc.get('title', ''),
                    'category': doc.get('category', 'general'),
                    'tone': doc.get('tone', ''),
                    'source': doc.get('source', 'manual')
                }
                
                ids.append(doc_id)
                texts.append(text)
                metadatas.append(metadata)
            
            # Add to collection
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
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
    
    # Initialize the index
    _rag_index.initialize()
    
    # Check if we already have documents
    info = _rag_index.get_collection_info()
    if info.get("document_count", 0) > 0:
        logger.info(f"RAG system already has {info['document_count']} documents")
        return
    
    # Add seed documents
    seed_docs = get_seed_documents()
    if seed_docs:
        success = _rag_index.add_documents(seed_docs)
        if success:
            logger.info(f"Added {len(seed_docs)} seed documents to RAG system")
        else:
            logger.warning("Failed to add seed documents")
    else:
        logger.info("No seed documents to add")

def fetch_style_hints(prompt: str) -> str:
    """Fetch style hints based on prompt - main interface for agents"""
    try:
        results = _rag_index.search(prompt, n_results=2)
        if results:
            return "\n\n".join(results)
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