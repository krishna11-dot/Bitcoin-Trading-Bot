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
    RAG system for finding similar historical market patterns.

    Uses ChromaDB for vector storage and sentence-transformers for embeddings.

    Example Usage:
        rag = RAGSystem()

        # Add historical pattern
        rag.add_market_pattern(
            date="2024-03-15",
            price=70000,
            rsi=45,
            fear_greed=32,
            narrative="Bitcoin consolidated near resistance with neutral RSI"
        )

        # Find similar patterns
        current = {
            'price': 98234,
            'rsi': 45,
            'fear_greed': 32,
            'narrative': 'BTC consolidating near $100K'
        }
        patterns = rag.find_similar_patterns(current, top_k=3)
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

    def add_market_pattern(
        self,
        date: str,
        price: float,
        rsi: float,
        fear_greed: int,
        narrative: str,
        additional_data: Dict = None
    ) -> bool:
        """
        Add a market pattern to the RAG database.

        Args:
            date: Date of pattern (e.g., "2024-03-15")
            price: BTC price at that time
            rsi: RSI value
            fear_greed: Fear & Greed index (0-100)
            narrative: Natural language description of market conditions
            additional_data: Optional dict of additional metadata

        Returns:
            True if added successfully

        Example:
            rag.add_market_pattern(
                date="2024-03-15",
                price=70000,
                rsi=45,
                fear_greed=32,
                narrative="Bitcoin broke $70K resistance with strong momentum and increasing volume"
            )
        """
        if not self.enabled:
            return False

        try:
            # Create document with natural language narrative
            document = f"""
Date: {date}
BTC Price: ${price:,.0f}
RSI: {rsi:.1f}
Fear & Greed: {fear_greed}

Market Narrative:
{narrative}
"""

            # Prepare metadata
            metadata = {
                "date": date,
                "price": float(price),
                "rsi": float(rsi),
                "fear_greed": int(fear_greed),
                "timestamp": datetime.now().isoformat()
            }

            # Add additional metadata if provided
            if additional_data:
                metadata.update(additional_data)

            # Generate unique ID
            pattern_id = f"pattern_{date}_{int(price)}"

            # Add to vector database
            self.collection.add(
                documents=[document],
                ids=[pattern_id],
                metadatas=[metadata]
            )

            return True

        except Exception as e:
            print(f"[RAG] Error adding pattern: {e}")
            return False

    def find_similar_patterns(
        self,
        current_conditions: Dict,
        top_k: int = 3,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """
        Find similar historical market patterns.

        Args:
            current_conditions: {
                'price': 98234,
                'rsi': 45,
                'fear_greed': 32,
                'narrative': 'BTC consolidating near $100K'
            }
            top_k: Number of similar patterns to return
            min_similarity: Minimum similarity score (0-1)

        Returns:
            List of similar patterns:
            [
                {
                    'narrative': "Full market narrative text",
                    'metadata': {'date': '2024-03-15', 'price': 70000, ...},
                    'similarity': 0.85
                },
                ...
            ]

        Example:
            current = {
                'price': 98234,
                'rsi': 45,
                'fear_greed': 32,
                'narrative': 'BTC consolidating near $100K with neutral RSI'
            }
            patterns = rag.find_similar_patterns(current, top_k=3)
        """
        if not self.enabled:
            return []

        try:
            # Create query from current conditions
            query = f"""
BTC Price: ${current_conditions['price']:,.0f}
RSI: {current_conditions['rsi']:.1f}
Fear & Greed: {current_conditions['fear_greed']}
Market Narrative: {current_conditions.get('narrative', 'Current market conditions')}
"""

            # Search for similar patterns
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )

            # Format results
            patterns = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i in range(len(results['documents'][0])):
                    # Calculate similarity from distance
                    # ChromaDB returns L2 distance, convert to similarity
                    distance = results['distances'][0][i]
                    similarity = 1 / (1 + distance)  # Convert distance to similarity

                    # Filter by minimum similarity
                    if similarity >= min_similarity:
                        patterns.append({
                            'narrative': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'similarity': similarity
                        })

            return patterns

        except Exception as e:
            print(f"[RAG] Error finding similar patterns: {e}")
            return []

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


def main():
    """
    Test RAG system with sample patterns.

    SUCCESS CRITERIA:
        - Creates vector database
        - Adds sample patterns successfully
        - Finds similar patterns with >0.7 similarity
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

    # Add sample patterns
    print("\nAdding sample historical patterns...")

    patterns_to_add = [
        {
            'date': '2024-03-15',
            'price': 70000,
            'rsi': 45,
            'fear_greed': 32,
            'narrative': 'Bitcoin consolidated near $70K resistance with neutral RSI and fear sentiment'
        },
        {
            'date': '2024-06-20',
            'price': 85000,
            'rsi': 52,
            'fear_greed': 40,
            'narrative': 'BTC pushed through $85K with moderate RSI and neutral market sentiment'
        },
        {
            'date': '2024-09-10',
            'price': 95000,
            'rsi': 48,
            'fear_greed': 35,
            'narrative': 'Bitcoin trading near $95K with balanced RSI and slight fear in market'
        }
    ]

    for pattern in patterns_to_add:
        success = rag.add_market_pattern(**pattern)
        if success:
            print(f"  [OK] Added pattern from {pattern['date']}")

    # Test pattern matching
    print("\n\nTesting pattern matching...")
    print("  Current conditions: BTC $98K, RSI 45, Fear & Greed 32")

    current = {
        'price': 98000,
        'rsi': 45,
        'fear_greed': 32,
        'narrative': 'Bitcoin consolidating near $98K with neutral RSI and fear sentiment'
    }

    similar_patterns = rag.find_similar_patterns(current, top_k=3)

    print(f"\n  Found {len(similar_patterns)} similar patterns:")
    for i, pattern in enumerate(similar_patterns, 1):
        print(f"\n  Pattern {i} (similarity: {pattern['similarity']:.2%}):")
        print(f"    Date: {pattern['metadata']['date']}")
        print(f"    Price: ${pattern['metadata']['price']:,.0f}")
        print(f"    RSI: {pattern['metadata']['rsi']:.1f}")
        print(f"    Fear & Greed: {pattern['metadata']['fear_greed']}")

    # Print summary
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print(f"Total patterns stored: {rag.get_pattern_count()}")
    print(f"Similar patterns found: {len(similar_patterns)}")

    if similar_patterns and similar_patterns[0]['similarity'] > 0.7:
        print("\n[OK] RAG system working correctly")
    else:
        print("\n[WARNING] Low similarity scores - may need more patterns")


if __name__ == "__main__":
    main()
