# RAG with Coin Descriptions - Step-by-Step Implementation

## Purpose
Justify RAG usage by storing UNSTRUCTURED text (coin descriptions) instead of auto-generated narratives from numbers.

This aligns with Swarnabha's feedback: "RAG is for unstructured text like news articles, not CSV numbers."

---

## The Flow: Where SentenceTransformer and ChromaDB Fit

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. FETCH UNSTRUCTURED TEXT                                      │
│                                                                  │
│  CoinGecko API                                                   │
│  GET /api/v3/coins/bitcoin                                       │
│       ↓                                                          │
│  {                                                               │
│    "description": {                                              │
│      "en": "Bitcoin is the first successful internet money..."   │
│    }                                                             │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. SENTENCE TRANSFORMER (Embedding Creation)                    │
│                                                                  │
│  text = "Bitcoin is the first successful internet money..."     │
│       ↓                                                          │
│  SentenceTransformer('all-MiniLM-L6-v2')                        │
│  model.encode(text)                                              │
│       ↓                                                          │
│  embedding = [0.12, -0.45, 0.78, ..., 0.33]  # 384 dimensions   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. CHROMADB (Vector Storage)                                    │
│                                                                  │
│  collection.add(                                                 │
│      documents=[text],              # Original text              │
│      embeddings=[embedding],        # 384D vector from step 2   │
│      ids=["bitcoin_description"],   # Unique ID                 │
│      metadatas=[{"coin": "bitcoin"}] # Metadata                 │
│  )                                                               │
│       ↓                                                          │
│  STORED IN: data/rag_vectordb/chroma.sqlite3                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. USER QUERY (Semantic Search)                                 │
│                                                                  │
│  query = "Tell me about Bitcoin's history and purpose"          │
│       ↓                                                          │
│  SentenceTransformer.encode(query)                              │
│       ↓                                                          │
│  query_embedding = [0.15, -0.42, 0.81, ..., 0.35]  # 384D      │
│       ↓                                                          │
│  collection.query(                                               │
│      query_embeddings=[query_embedding],                         │
│      n_results=3                                                 │
│  )                                                               │
│       ↓                                                          │
│  ChromaDB finds closest vectors using L2 distance               │
│       ↓                                                          │
│  Returns: "Bitcoin is the first successful internet money..."   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. LLM AUGMENTATION                                             │
│                                                                  │
│  LLM receives:                                                   │
│    - User query: "Tell me about Bitcoin's history"              │
│    - Retrieved context: "Bitcoin is the first successful..."    │
│       ↓                                                          │
│  LLM generates answer using retrieved context                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Implementation

### STEP 1: Update CoinGecko Client

Add method to fetch coin descriptions (UNSTRUCTURED TEXT).

**File**: `src/data_pipeline/coingecko_mcp.py`

**Add this method** (around line 300):

```python
def get_coin_description(self, coin_id: str = 'bitcoin') -> Optional[str]:
    """
    Get coin description (UNSTRUCTURED TEXT for RAG).

    This is UNSTRUCTURED text - perfect for RAG!
    Unlike price/volume (structured numbers).

    Args:
        coin_id: Coin identifier (e.g., 'bitcoin', 'ethereum')

    Returns:
        String description or None

    Example:
        mcp = CoinGeckoMCP()
        desc = mcp.get_coin_description('bitcoin')
        # Returns: "Bitcoin is the first successful internet money..."
    """
    if not self.enabled:
        return None

    try:
        self._wait_for_rate_limit()

        url = f"{self.base_url}/coins/{coin_id}"
        params = {
            'localization': 'false',  # Only English
            'tickers': 'false',       # Don't need ticker data
            'market_data': 'false',   # Don't need price data
            'community_data': 'false',
            'developer_data': 'false',
            'sparkline': 'false',
            'x_cg_demo_api_key': self.api_key
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()

        # Extract UNSTRUCTURED description text
        description = data.get('description', {}).get('en', '')

        return description if description else None

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("[COINGECKO] Rate limit exceeded")
        else:
            print(f"[COINGECKO] HTTP error: {e}")
        return None

    except Exception as e:
        print(f"[COINGECKO] Error fetching description: {e}")
        return None
```

**WHERE SENTENCETRANSFORMER FITS**: Not here! CoinGecko client just fetches raw text. SentenceTransformer comes next.

---

### STEP 2: Update RAG System

Add method to store coin descriptions.

**File**: `src/rag/rag_system.py`

**Add this method** (around line 338):

```python
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
```

---

### STEP 3: Create Initialization Script

Script to fetch and store coin descriptions once.

**File**: `src/scripts/initialize_coin_descriptions.py` (NEW FILE)

```python
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
```

---

### STEP 4: Update Agent to Use Coin Descriptions

**File**: `src/natural_language/agent.py`

**Update check_market method** (around line 450):

```python
def check_market(self, state):
    """Check current market conditions."""
    print("[AGENT] Checking market...")

    try:
        summary = self.data_fetcher.get_market_summary()

        # Get technical indicators
        rsi = summary.get('rsi', 50)
        fear_greed = summary.get('fear_greed_index', "N/A")

        # **NEW: Use RAG to find relevant coin descriptions**
        # This justifies RAG by using UNSTRUCTURED TEXT
        query = f"What is Bitcoin? Tell me about its history and purpose."

        relevant_content = self.rag.find_relevant_content(
            query=query,
            top_k=1,
            min_similarity=0.5
        )

        # Build context with coin description if available
        context = f"""
Current Market Summary:
- Price: ${summary['current_price']:,.2f}
- RSI: {rsi:.1f}
- Fear & Greed: {fear_greed}
"""

        if relevant_content:
            context += f"\n\nBitcoin Context:\n{relevant_content[0]['text']}\n"

        # Generate response with LLM
        prompt = f"""
You are a Bitcoin trading assistant.

{context}

Provide a brief market overview.
"""

        response = self.llm.invoke(prompt)

        # ... rest of method
```

---

## How This Justifies RAG

### ❌ BEFORE (Overkill):
```python
# Auto-generated narrative from numbers
narrative = f"Bitcoin trading at ${price} with RSI {rsi}"

# RAG retrieves similar numbers - could just use pandas:
# df[(df['price'] > 95000) & (df['rsi'] > 40)]
```

### ✅ AFTER (Justified):
```python
# UNSTRUCTURED TEXT from CoinGecko
description = "Bitcoin is the first successful internet money based on peer-to-peer technology..."

# RAG retrieves semantically similar content:
# Query: "Tell me about Bitcoin's history"
# Matches: "first successful internet money" (semantic match)
# Can't do this with pandas!
```

---

## Interview Talking Points

**Question**: "Why did you use RAG in your project?"

**Answer**:
> "Initially, I was using RAG for structured CSV data, but my mentor pointed out that was overkill - simple pandas filtering would work better. I refactored to use RAG for coin descriptions from CoinGecko, which are unstructured text. This is a better fit because RAG can semantically match concepts like 'history' to 'first successful internet money', which you can't do with numeric filtering."

**Question**: "Where do SentenceTransformer and ChromaDB fit in your RAG system?"

**Answer**:
> "When I fetch coin descriptions from CoinGecko API, they're just strings. SentenceTransformer converts them to 384-dimensional embeddings using the all-MiniLM-L6-v2 model. ChromaDB stores these embeddings in a vector database at data/rag_vectordb/. When a user asks a question, SentenceTransformer embeds the query, ChromaDB finds the closest vectors using L2 distance, and returns relevant descriptions."

---

## File Locations

**SentenceTransformer Usage**:
- `src/rag/rag_system.py:118` - Model loaded: `SentenceTransformer('all-MiniLM-L6-v2')`
- Automatically used by ChromaDB when calling `collection.add()` or `collection.query()`

**ChromaDB Usage**:
- `src/rag/rag_system.py:110-113` - Client initialized: `chromadb.PersistentClient()`
- `src/rag/rag_system.py:210-214` - Storing: `collection.add()`
- `src/rag/rag_system.py:274-276` - Querying: `collection.query()`
- **Storage location**: `data/rag_vectordb/chroma.sqlite3`

**Data Flow**:
```
CoinGecko API → coingecko_mcp.py (fetch text)
                       ↓
          rag_system.py (add_coin_description)
                       ↓
          SentenceTransformer.encode() [384D vector]
                       ↓
          ChromaDB.add() [store in data/rag_vectordb/]
                       ↓
          User query → SentenceTransformer.encode()
                       ↓
          ChromaDB.query() [L2 distance search]
                       ↓
          Return relevant descriptions
```
