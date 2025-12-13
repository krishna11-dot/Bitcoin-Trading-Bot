#!/usr/bin/env python3
"""
Initialize RAG with Coin Descriptions

PURPOSE:
    Fetch coin descriptions from CoinGecko and store in RAG system.
    This justifies RAG by using UNSTRUCTURED TEXT (not CSV numbers).

RUN ONCE:
    python src/scripts/initialize_coin_descriptions.py

SUCCESS CRITERIA:
    - Fetches descriptions for Bitcoin (and optionally other coins)
    - Stores in ChromaDB with SentenceTransformer embeddings
    - RAG system can semantically search descriptions
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_pipeline.coingecko_mcp import CoinGeckoMCP
from src.rag.rag_system import RAGSystem


def initialize_coin_descriptions():
    """
    Fetch and store coin descriptions in RAG.

    FLOW:
    1. CoinGecko API → Unstructured text
    2. SentenceTransformer → 384D embedding
    3. ChromaDB → Vector storage
    """
    print("=" * 60)
    print("INITIALIZING COIN DESCRIPTIONS IN RAG")
    print("=" * 60)

    # Initialize clients
    print("\nInitializing CoinGecko client...")
    coingecko = CoinGeckoMCP()

    print("Initializing RAG system...")
    rag = RAGSystem()

    if not coingecko.enabled:
        print("\n[ERROR] CoinGecko API disabled (no API key)")
        print("Set COINGECKO_DEMO_API_KEY in .env file")
        return

    if not rag.enabled:
        print("\n[ERROR] RAG system disabled (missing dependencies)")
        print("Install: pip install chromadb sentence-transformers")
        return

    # Coins to fetch
    coins = [
        {'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'BTC'},
        # Optionally add more coins:
        # {'id': 'ethereum', 'name': 'Ethereum', 'symbol': 'ETH'},
    ]

    # Fetch and store descriptions
    print(f"\nFetching descriptions for {len(coins)} coin(s)...\n")

    for coin in coins:
        print(f"Processing {coin['name']} ({coin['symbol']})...")

        # STEP 1: Fetch unstructured text from CoinGecko
        description = coingecko.get_coin_description(coin['id'])

        if description:
            # STEP 2 & 3: Pass to RAG
            # - SentenceTransformer creates 384D embedding
            # - ChromaDB stores embedding + text

            success = rag.add_coin_description(
                coin_id=coin['id'],
                description=description,
                metadata={
                    'name': coin['name'],
                    'symbol': coin['symbol']
                }
            )

            if success:
                print(f"  [OK] {coin['name']} description stored")
                print(f"  Preview: {description[:100]}...")
            else:
                print(f"  [FAILED] Could not store {coin['name']}")
        else:
            print(f"  [FAILED] Could not fetch description for {coin['name']}")

        print()

    # Print summary
    print("=" * 60)
    print("INITIALIZATION COMPLETE")
    print("=" * 60)
    print(f"Total items in RAG: {rag.get_pattern_count()}")

    # Test semantic search
    print("\nTesting semantic search...")
    query = "Tell me about Bitcoin's history and purpose"
    print(f"Query: '{query}'")

    results = rag.find_relevant_content(query, top_k=1)

    if results:
        print(f"\n[OK] Found {len(results)} result(s)")
        print(f"Similarity: {results[0]['similarity']:.2%}")
        print(f"Text preview: {results[0]['text'][:200]}...")
    else:
        print("[WARNING] No results found")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    initialize_coin_descriptions()
