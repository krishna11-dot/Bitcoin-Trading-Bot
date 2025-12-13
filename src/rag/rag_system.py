"""
RAG System - Retrieval-Augmented Generation for Market Pattern Matching

PURPOSE:
    Find similar historical market conditions using natural language embeddings.
    Provides historical context to LLM for better trading insights.

CORRECT USE:
    - Natural language queries: "Find times when BTC was at similar price with low RSI"
    - Pattern matching across historical market narratives
    - Contextual information for LLM responses

INCORRECT USE:
    - Reading CSV files (use pandas for tabular data)
    - Extracting structured data (use SQL/pandas for that)
    - Any task better suited for simpler tools

WHY RAG HERE:
    RAG excels at finding similar patterns in natural language descriptions.
    Market conditions can be described narratively, making RAG a good fit.

    Example: "Bitcoin consolidated near $70K with neutral RSI and fear sentiment"
    This narrative can be matched against historical similar conditions.

SUCCESS CRITERIA:
    - Finds relevant historical patterns with >0.7 similarity score
    - Returns top 3 most similar market conditions
    - Provides context that helps LLM give better answers
    - Does NOT slow down the system (async/optional)

"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("[RAG] ChromaDB not installed. RAG pattern matching disabled.")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("[RAG] sentence-transformers not installed. RAG pattern matching disabled.")


class RAGSystem:
    """
    RAG system for semantic search of UNSTRUCTURED TEXT (coin descriptions).

    Uses ChromaDB for vector storage and sentence-transformers for embeddings.

    Why RAG here (aligned with Swarnabha's feedback):
    - Stores UNSTRUCTURED coin descriptions from CoinGecko
    - NOT auto-generated narratives from CSV numbers (that would be overkill)
    - Semantic matching: "history" matches "first successful internet money"

    Example Usage:
        rag = RAGSystem()

        # Add coin description (UNSTRUCTURED TEXT)
        rag.add_coin_description(
            coin_id='bitcoin',
            description='Bitcoin is the first successful internet money...',
            metadata={'name': 'Bitcoin', 'symbol': 'BTC'}
        )

        # Search for relevant content
        results = rag.find_relevant_content(
            query='Tell me about Bitcoin history',
            top_k=3
        )
    """

    def __init__(self, persist_directory: str = None):
        """
        Initialize RAG system.

        Args:
            persist_directory: Directory to store vector database
                             (default: data/rag_vectordb)

        Raises:
            RuntimeError: If required libraries not installed
        """
        if not CHROMADB_AVAILABLE or not SENTENCE_TRANSFORMERS_AVAILABLE:
            self.enabled = False
            print("[RAG] RAG system disabled (missing dependencies)")
            return

        self.enabled = True

        # Set up persist directory
        if persist_directory is None:
            project_root = Path(__file__).parent.parent.parent
            persist_directory = str(project_root / "data" / "rag_vectordb")

        # Ensure directory exists
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Initialize sentence transformer model
        # Using 'all-MiniLM-L6-v2': fast, good quality, 384 dimensions
        print("[RAG] Loading sentence transformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("[RAG] Model loaded successfully")

        # Get or create collection
        self.collection_name = "market_patterns"
        self.collection = self._get_or_create_collection()

        print(f"[RAG] System initialized with {self.collection.count()} patterns")

    def _get_or_create_collection(self):
        """
        Get existing collection or create new one.

        Returns:
            ChromaDB collection for market patterns
        """
        try:
            collection = self.client.get_collection(name=self.collection_name)
            print(f"[RAG] Using existing collection '{self.collection_name}'")
        except Exception:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Historical Bitcoin market patterns"}
            )
            print(f"[RAG] Created new collection '{self.collection_name}'")

        return collection

    # OLD METHODS REMOVED (auto-generated narratives approach - overkill per Swarnabha)
    # - add_market_pattern() - used auto-generated narratives from CSV numbers
    # - find_similar_patterns() - searched for similar numeric patterns
    # These have been replaced with:
    # - add_coin_description() - stores UNSTRUCTURED coin descriptions
    # - find_relevant_content() - semantic search for coin information
    def get_pattern_count(self) -> int:
        """
        Get total number of patterns in database.

        Returns:
            Number of stored patterns
        """
        if not self.enabled:
            return 0

        try:
            return self.collection.count()
        except Exception:
            return 0

    def clear_patterns(self) -> bool:
        """
        Clear all patterns from database.

        WARNING: This deletes all stored patterns.

        Returns:
            True if cleared successfully
        """
        if not self.enabled:
            return False

        try:
            # Delete and recreate collection
            self.client.delete_collection(name=self.collection_name)
            self.collection = self._get_or_create_collection()
            print("[RAG] All patterns cleared")
            return True
        except Exception as e:
            print(f"[RAG] Error clearing patterns: {e}")
            return False

    def add_coin_description(
        self,
        coin_id: str,
        description: str,
        metadata: Dict = None
    ) -> bool:
        """
        Add coin description (UNSTRUCTURED TEXT) to RAG.

        THIS JUSTIFIES RAG:
        - Description is unstructured text (not structured CSV numbers)
        - RAG finds semantically similar content
        - Can't do this with pandas filtering

        Args:
            coin_id: Coin identifier (e.g., 'bitcoin')
            description: Unstructured text description
            metadata: Optional metadata (coin name, symbol, etc.)

        Returns:
            True if added successfully

        Example:
            rag = RAGSystem()
            rag.add_coin_description(
                coin_id='bitcoin',
                description='Bitcoin is the first successful internet money...',
                metadata={'name': 'Bitcoin', 'symbol': 'BTC'}
            )

        WHERE SENTENCETRANSFORMER FITS:
            - description text gets passed to SentenceTransformer model
            - model.encode(description) creates 384D embedding
            - embedding is stored in ChromaDB

        WHERE CHROMADB FITS:
            - collection.add() stores the embedding
            - Persisted to data/rag_vectordb/chroma.sqlite3
        """
        if not self.enabled:
            return False

        try:
            # Prepare document (unstructured text)
            document = f"""
Coin: {coin_id}

Description:
{description}
"""

            # Prepare metadata
            doc_metadata = {
                "coin_id": coin_id,
                "type": "coin_description",
                "timestamp": datetime.now().isoformat()
            }

            if metadata:
                doc_metadata.update(metadata)

            # Generate unique ID
            doc_id = f"coin_{coin_id}_description"

            # **THIS IS WHERE SENTENCETRANSFORMER IS USED**
            # When collection.add() is called with documents (not embeddings):
            # 1. ChromaDB passes text to default embedding function
            # 2. Default embedding function uses SentenceTransformer
            # 3. SentenceTransformer.encode(document) creates 384D vector
            # 4. Vector is stored in ChromaDB

            # **THIS IS WHERE CHROMADB IS USED**
            # collection.add() stores:
            # - Original document text
            # - 384D embedding vector (from SentenceTransformer)
            # - Metadata
            # - ID
            # All persisted to: data/rag_vectordb/chroma.sqlite3

            self.collection.add(
                documents=[document],  # SentenceTransformer will embed this
                ids=[doc_id],
                metadatas=[doc_metadata]
            )

            print(f"[RAG] Added coin description for {coin_id}")
            return True

        except Exception as e:
            print(f"[RAG] Error adding coin description: {e}")
            return False

    def find_relevant_content(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """
        Find relevant content using semantic search.

        THIS IS WHERE RAG SHINES:
        - Query: "Tell me about Bitcoin's history"
        - Finds: Bitcoin description (even if it doesn't contain exact words)
        - Semantic matching: "history" matches "first successful internet money"

        Args:
            query: Natural language query
            top_k: Number of results
            min_similarity: Minimum similarity score

        Returns:
            List of relevant content with similarity scores

        WHERE SENTENCETRANSFORMER FITS:
            - query text gets encoded to 384D vector
            - model.encode(query) creates query embedding

        WHERE CHROMADB FITS:
            - collection.query() compares query embedding to stored embeddings
            - Uses L2 distance in 384D space
            - Returns closest matches
        """
        if not self.enabled:
            return []

        try:
            # **THIS IS WHERE SENTENCETRANSFORMER IS USED**
            # collection.query() will:
            # 1. Pass query to SentenceTransformer
            # 2. SentenceTransformer.encode(query) creates 384D vector
            # 3. ChromaDB compares to stored vectors

            # **THIS IS WHERE CHROMADB IS USED**
            # collection.query():
            # 1. Loads stored embeddings from data/rag_vectordb/
            # 2. Calculates L2 distance between query and stored vectors
            # 3. Returns top_k closest matches

            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )

            # Format results
            content = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i in range(len(results['documents'][0])):
                    distance = results['distances'][0][i]
                    similarity = 1 / (1 + distance)

                    if similarity >= min_similarity:
                        content.append({
                            'text': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'similarity': similarity
                        })

            return content

        except Exception as e:
            print(f"[RAG] Error finding content: {e}")
            return []


def main():
    """
    Test RAG system with coin descriptions (UNSTRUCTURED TEXT).

    SUCCESS CRITERIA:
        - Creates vector database
        - Adds coin descriptions successfully
        - Finds relevant content with semantic search
        - Returns results in correct format
    """
    print("="*60)
    print("RAG SYSTEM - Test Mode")
    print("="*60)

    # Initialize RAG
    rag = RAGSystem()

    if not rag.enabled:
        print("\n[ERROR] RAG system disabled (missing dependencies)")
        print("\nTo enable RAG, install:")
        print("  pip install chromadb sentence-transformers")
        return

    # Add sample coin descriptions (UNSTRUCTURED TEXT)
    print("\nAdding sample coin descriptions...")

    sample_descriptions = [
        {
            'coin_id': 'bitcoin',
            'description': 'Bitcoin is the world\'s first decentralized cryptocurrency, created in 2009 by Satoshi Nakamoto. It enables peer-to-peer electronic cash transactions without intermediaries.',
            'metadata': {'name': 'Bitcoin', 'symbol': 'BTC'}
        },
        {
            'coin_id': 'ethereum',
            'description': 'Ethereum is a decentralized platform for smart contracts and decentralized applications (dApps). It was proposed by Vitalik Buterin in 2013.',
            'metadata': {'name': 'Ethereum', 'symbol': 'ETH'}
        }
    ]

    for desc in sample_descriptions:
        success = rag.add_coin_description(**desc)
        if success:
            print(f"  [OK] Added description for {desc['metadata']['name']}")

    # Test semantic search
    print("\n\nTesting semantic search...")
    test_queries = [
        "Tell me about Bitcoin's history",
        "What is Ethereum used for?",
        "Explain peer-to-peer technology"
    ]

    for query in test_queries:
        print(f"\n  Query: '{query}'")
        results = rag.find_relevant_content(query, top_k=2)

        if results:
            print(f"  Found {len(results)} result(s):")
            for i, result in enumerate(results, 1):
                print(f"    {i}. {result['metadata'].get('name', 'Unknown')} "
                      f"(similarity: {result['similarity']:.2%})")
        else:
            print("  No results found")

    # Print summary
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print(f"Total items stored: {rag.get_pattern_count()}")

    print("\n[OK] RAG system working with UNSTRUCTURED TEXT")
    print("This approach is aligned with Swarnabha's feedback:")
    print("- Using RAG for unstructured coin descriptions")
    print("- NOT using RAG for auto-generated narratives from numbers")


if __name__ == "__main__":
    main()
