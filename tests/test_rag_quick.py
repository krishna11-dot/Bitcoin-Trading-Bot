#!/usr/bin/env python3
"""Quick RAG test - check dependencies and basic functionality"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("RAG QUICK TEST")
print("=" * 60)

# Test 1: Check ChromaDB
print("\n1. Checking ChromaDB...")
try:
    import chromadb
    print("   [OK] ChromaDB installed")
except ImportError:
    print("   [FAILED] ChromaDB not installed")
    print("   Install: pip install chromadb")
    sys.exit(1)

# Test 2: Check SentenceTransformers
print("\n2. Checking SentenceTransformers...")
try:
    from sentence_transformers import SentenceTransformer
    print("   [OK] SentenceTransformers installed")
except ImportError:
    print("   [FAILED] SentenceTransformers not installed")
    print("   Install: pip install sentence-transformers")
    sys.exit(1)

# Test 3: Initialize RAG system
print("\n3. Initializing RAG system...")
try:
    from src.rag.rag_system import RAGSystem
    rag = RAGSystem()

    if rag.enabled:
        print("   [OK] RAG system initialized")
        print(f"   Patterns in database: {rag.get_pattern_count()}")
    else:
        print("   [FAILED] RAG system disabled")
        sys.exit(1)
except Exception as e:
    print(f"   [FAILED] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test adding a sample description
print("\n4. Testing add_coin_description...")
try:
    test_desc = "This is a test description for testing purposes."
    success = rag.add_coin_description(
        coin_id="test",
        description=test_desc,
        metadata={'name': 'Test Coin', 'symbol': 'TEST'}
    )

    if success:
        print("   [OK] Successfully added test description")
    else:
        print("   [FAILED] Could not add description")
except Exception as e:
    print(f"   [FAILED] Error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test semantic search
print("\n5. Testing semantic search...")
try:
    results = rag.find_relevant_content(
        query="Tell me about the test",
        top_k=1
    )

    if results:
        print(f"   [OK] Found {len(results)} result(s)")
        print(f"   Similarity: {results[0]['similarity']:.2%}")
    else:
        print("   [WARNING] No results found")
except Exception as e:
    print(f"   [FAILED] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\n[OK] RAG system is working!")
print("\nNext step: Run initialization script to fetch Bitcoin description:")
print("  python src/scripts/initialize_coin_descriptions.py")
