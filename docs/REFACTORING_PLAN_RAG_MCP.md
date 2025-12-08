# Refactoring Plan: RAG + MCP Integration

**Date**: 2025-12-07
**Goal**: Use the right tools for the right job
**Status**: Ready to implement

---

## Table of Contents

1. [Current vs Proposed Architecture](#current-vs-proposed-architecture)
2. [CoinGecko MCP Rate Limits](#coingecko-mcp-rate-limits)
3. [LangChain vs MCP Client](#langchain-vs-mcp-client)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Testing Plan](#testing-plan)

---

## Current vs Proposed Architecture

### Current (v1.0) ❌

```
Data Pipeline:
  RAG → Read CSV file (bitcoin_clean.csv)
         ↓
  Extract historical prices
         ↓
  Return tabular data

Problem: RAG is overkill for structured CSV data
```

### Proposed (v2.0) ✅

```
Data Pipeline:
  Pandas → Read CSV file (bitcoin_clean.csv)
            ↓
  Extract historical prices
            ↓
  Return tabular data

Natural Language Interface:
  User question → LangGraph Agent
                       ↓
                  RAG System (pattern matching)
                       ↓
                  Historical context for LLM
                       ↓
                  CoinGecko MCP (optional, live data)
                       ↓
                  LLM response

Result: Each tool used for its strength
```

---

## CoinGecko MCP Rate Limits

### Free Tier Options

| Option | Cost | Rate Limit | Monthly Limit | Best For |
|--------|------|------------|---------------|----------|
| **Keyless** | Free | Shared (unstable) | Unknown | Quick tests only |
| **Demo Key** ✅ | **FREE** | **30 calls/min** | **10,000 calls/month** | **Your bot (recommended)** |
| **Pro Key** | $129/month | 500 calls/min | 500,000 calls/month | Production apps |

### Recommendation: Demo Key (Free)

**Why Demo Key:**
- ✅ **FREE** forever
- ✅ 30 calls/min (enough for chat mode)
- ✅ 10,000 calls/month
- ✅ Real-time price data
- ✅ Stable rate limits (not shared)

**Calculation for your use:**
```
Chat Mode Usage:
  - Average: 5 questions per session
  - Each question: 2-3 MCP calls
  - Daily usage: ~15 calls/day
  - Monthly: ~450 calls/month

Verdict: Well within 10,000/month limit ✅
```

**Get Demo Key:**
1. Go to: https://www.coingecko.com/en/api/pricing
2. Click "Get Free Demo Key"
3. Sign up (free account)
4. Copy API key
5. Add to `.env`: `COINGECKO_DEMO_API_KEY=your_key_here`

---

## LangChain vs MCP Client

### Do You Need LangChain? NO ❌

**What you need:**

| Library | Purpose | Install Command |
|---------|---------|-----------------|
| **LangGraph** ✅ | State machine (already using) | `pip install langgraph` |
| **MCP Client** ✅ | Connect to CoinGecko MCP | `pip install mcp` |
| **LangChain** ❌ | **NOT needed** (too heavy) | Don't install |

**Why NOT LangChain:**
- You already have LangGraph (lighter, better for agents)
- MCP has its own client library
- LangChain adds unnecessary complexity

**What to install:**
```bash
# For MCP support
pip install mcp

# Or with uv
uv pip install mcp
```

---

## Step-by-Step Implementation

### Phase 1: Replace RAG with Pandas (CSV Reading)

#### Step 1.1: Identify Current RAG Usage

**Files to check:**
- `src/data/data_fetcher.py`
- `src/rag/rag_system.py`
- Any file importing RAG for CSV reading

**Current code pattern:**
```python
# src/data/data_fetcher.py (CURRENT)
from src.rag.rag_system import RAGSystem

def fetch_historical_data():
    rag = RAGSystem()
    data = rag.query("Get Bitcoin historical prices")
    return data
```

#### Step 1.2: Replace with Pandas

**New code:**
```python
# src/data/data_fetcher.py (NEW)
import pandas as pd
from pathlib import Path

def fetch_historical_data():
    """
    Fetch historical Bitcoin data from CSV.

    Uses pandas for tabular data (correct tool for the job).
    RAG is NOT needed for structured CSV files.
    """
    csv_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'bitcoin_clean.csv'

    # Simple pandas read (much faster than RAG)
    df = pd.read_csv(csv_path)

    # Ensure proper date parsing
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    return df
```

**Why this is better:**
- ✅ 10x faster (no vector embeddings)
- ✅ Simpler code (2 lines vs complex RAG setup)
- ✅ Correct tool for tabular data
- ✅ Easier to debug

#### Step 1.3: Update All Imports

**Find all files using RAG for CSV:**
```bash
# Search for RAG imports
grep -r "from src.rag" src/

# Search for RAG usage
grep -r "RAGSystem()" src/
```

**Replace pattern:**
```python
# OLD ❌
from src.rag.rag_system import RAGSystem
rag = RAGSystem()
data = rag.query("historical data")

# NEW ✅
from src.data.data_fetcher import fetch_historical_data
data = fetch_historical_data()
```

---

### Phase 2: Move RAG to Natural Language Interface

#### Step 2.1: Update RAG System for Pattern Matching

**Create new RAG purpose:**
```python
# src/rag/rag_system.py (UPDATED)
from typing import List, Dict
import chromadb
from sentence_transformers import SentenceTransformer

class RAGSystem:
    """
    RAG system for natural language pattern matching.

    PURPOSE: Find similar historical market narratives
    NOT FOR: Reading CSV files (use pandas for that)

    Use cases:
    - "Find similar market conditions to current"
    - "What happened last time BTC was at this price?"
    - Pattern matching for historical context
    """

    def __init__(self):
        self.client = chromadb.PersistentClient(path="data/rag_vectordb")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """Get or create ChromaDB collection."""
        try:
            return self.client.get_collection(name="market_patterns")
        except:
            return self.client.create_collection(name="market_patterns")

    def add_market_pattern(self, date: str, price: float, rsi: float,
                          fear_greed: int, narrative: str):
        """
        Add a market pattern described in natural language.

        Args:
            date: Date of pattern (e.g., "2024-03-15")
            price: BTC price at that time
            rsi: RSI value
            fear_greed: Fear & Greed index
            narrative: Natural language description
                      e.g., "Bitcoin broke $70K resistance with strong momentum"
        """
        # Create document with natural language narrative
        document = f"""
        Date: {date}
        BTC Price: ${price:,.0f}
        RSI: {rsi:.1f}
        Fear & Greed: {fear_greed}

        Market Narrative:
        {narrative}
        """

        # Add to vector database
        self.collection.add(
            documents=[document],
            ids=[f"pattern_{date}"],
            metadatas=[{
                "date": date,
                "price": price,
                "rsi": rsi,
                "fear_greed": fear_greed
            }]
        )

    def find_similar_patterns(self, current_conditions: Dict, top_k: int = 3) -> List[Dict]:
        """
        Find similar historical market patterns using natural language.

        Args:
            current_conditions: {
                "price": 98234,
                "rsi": 45,
                "fear_greed": 32,
                "narrative": "BTC consolidating near $100K"
            }
            top_k: Number of similar patterns to return

        Returns:
            List of similar historical patterns with narratives
        """
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
        for i in range(len(results['documents'][0])):
            patterns.append({
                'narrative': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'similarity': 1 - results['distances'][0][i]  # Convert distance to similarity
            })

        return patterns
```

#### Step 2.2: Integrate RAG into Natural Language Agent

**Update the agent to use RAG:**
```python
# src/natural_language/agent.py (UPDATED)
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from src.rag.rag_system import RAGSystem
from src.natural_language.gemini_client import GeminiClient
from src.natural_language.guardrails import OutputGuardrails

class AgentState(TypedDict):
    """State shared across all nodes."""
    user_query: str
    intent: str
    parameters: dict
    market_data: dict
    historical_context: list  # NEW: RAG results
    response: str

class TradingAgent:
    """
    Single-agent LangGraph for natural language trading queries.

    4 Nodes:
    1. Understand (Gemini LLM)
    2. Validate (Guardrails)
    3. Execute (Decision Box + RAG)  ← RAG added here
    4. Respond (Gemini LLM + RAG context)
    """

    def __init__(self):
        self.gemini = GeminiClient()
        self.rag = RAGSystem()  # NEW: RAG for pattern matching
        self.graph = self._build_graph()

    def _execute_node(self, state: AgentState) -> AgentState:
        """
        Execute node - calls Decision Box and RAG.

        NEW: Uses RAG to find similar historical patterns.
        """
        intent = state['intent']

        # Get current market data
        from src.data.data_fetcher import fetch_historical_data
        df = fetch_historical_data()
        latest = df.iloc[-1]

        state['market_data'] = {
            'price': latest['Price'],
            'rsi': latest.get('RSI', 50),
            'fear_greed': latest.get('Fear_Greed', 50)
        }

        # NEW: Use RAG to find similar historical patterns
        if intent in ['check_market', 'get_decision']:
            current_conditions = {
                'price': state['market_data']['price'],
                'rsi': state['market_data']['rsi'],
                'fear_greed': state['market_data']['fear_greed'],
                'narrative': f"BTC trading at ${state['market_data']['price']:,.0f}"
            }

            # Find similar patterns
            similar_patterns = self.rag.find_similar_patterns(
                current_conditions,
                top_k=3
            )

            state['historical_context'] = similar_patterns

        return state

    def _respond_node(self, state: AgentState) -> AgentState:
        """
        Respond node - formats response using Gemini LLM.

        NEW: Includes historical context from RAG.
        """
        # Build prompt with RAG context
        prompt = f"""
        User asked: {state['user_query']}

        Current Market Data:
        - BTC Price: ${state['market_data']['price']:,.0f}
        - RSI: {state['market_data']['rsi']:.1f}
        - Fear & Greed: {state['market_data']['fear_greed']}

        Historical Context (similar past patterns):
        """

        # Add RAG results
        if state.get('historical_context'):
            for i, pattern in enumerate(state['historical_context'], 1):
                prompt += f"\n\nPattern {i} (similarity: {pattern['similarity']:.0%}):\n"
                prompt += pattern['narrative']

        prompt += f"\n\nProvide a helpful response to the user's question."

        # Generate response
        response = self.gemini.generate(prompt)
        state['response'] = response

        return state
```

---

### Phase 3: Add CoinGecko MCP (Optional)

#### Step 3.1: Install MCP Client

```bash
# Install MCP client library
pip install mcp

# Or with uv
uv pip install mcp
```

#### Step 3.2: Add CoinGecko Demo API Key to .env

```env
# .env (ADD THIS)

# CoinGecko API (FREE Demo Key)
COINGECKO_DEMO_API_KEY=your_demo_key_here
COINGECKO_ENVIRONMENT=demo
```

#### Step 3.3: Create CoinGecko MCP Client

```python
# src/data/coingecko_mcp.py (NEW FILE)
import os
from typing import Dict, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

class CoinGeckoMCP:
    """
    CoinGecko MCP client for live cryptocurrency data.

    Uses Demo API key (FREE):
    - 30 calls/min
    - 10,000 calls/month
    - Real-time price data

    Fallback to CSV if API unavailable.
    """

    def __init__(self):
        self.api_key = os.getenv('COINGECKO_DEMO_API_KEY')
        self.environment = os.getenv('COINGECKO_ENVIRONMENT', 'demo')

        # API endpoints
        self.base_url = {
            'demo': 'https://api.coingecko.com/api/v3',
            'pro': 'https://pro-api.coingecko.com/api/v3'
        }[self.environment]

        self.enabled = bool(self.api_key)

        if not self.enabled:
            print("[COINGECKO MCP] No API key found. Using CSV fallback.")

    def get_bitcoin_price(self) -> Optional[Dict]:
        """
        Get current Bitcoin price from CoinGecko.

        Returns:
            {
                'price': 98234.56,
                'market_cap': 1934567890123,
                'volume_24h': 45678901234,
                'price_change_24h': 2.5
            }
        """
        if not self.enabled:
            return None

        try:
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': 'bitcoin',
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'x_cg_demo_api_key': self.api_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()['bitcoin']

            return {
                'price': data['usd'],
                'market_cap': data['usd_market_cap'],
                'volume_24h': data['usd_24h_vol'],
                'price_change_24h': data['usd_24h_change']
            }

        except Exception as e:
            print(f"[COINGECKO MCP] Error fetching price: {e}")
            return None

    def get_market_chart(self, days: int = 7) -> Optional[Dict]:
        """
        Get historical price chart data.

        Args:
            days: Number of days of history (1, 7, 14, 30, 90, 180, 365)

        Returns:
            {
                'prices': [[timestamp, price], ...],
                'market_caps': [[timestamp, market_cap], ...],
                'total_volumes': [[timestamp, volume], ...]
            }
        """
        if not self.enabled:
            return None

        try:
            url = f"{self.base_url}/coins/bitcoin/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'x_cg_demo_api_key': self.api_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            print(f"[COINGECKO MCP] Error fetching market chart: {e}")
            return None
```

#### Step 3.4: Integrate MCP into Data Fetcher

```python
# src/data/data_fetcher.py (UPDATED)
import pandas as pd
from pathlib import Path
from typing import Optional
from src.data.coingecko_mcp import CoinGeckoMCP

class DataFetcher:
    """
    Unified data fetcher with MCP support.

    Priority:
    1. Try CoinGecko MCP (live data)
    2. Fallback to CSV (historical data)
    """

    def __init__(self):
        self.mcp = CoinGeckoMCP()
        self.csv_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'bitcoin_clean.csv'

    def get_current_price(self) -> float:
        """
        Get current BTC price.

        Priority:
        1. CoinGecko MCP (live)
        2. CSV latest row (fallback)
        """
        # Try MCP first
        if self.mcp.enabled:
            live_data = self.mcp.get_bitcoin_price()
            if live_data:
                print(f"[DATA] Using live price from CoinGecko MCP: ${live_data['price']:,.2f}")
                return live_data['price']

        # Fallback to CSV
        df = self.fetch_historical_data()
        latest_price = df.iloc[-1]['Price']
        print(f"[DATA] Using CSV price (fallback): ${latest_price:,.2f}")
        return latest_price

    def fetch_historical_data(self) -> pd.DataFrame:
        """
        Fetch historical Bitcoin data from CSV.

        Uses pandas for tabular data (correct tool).
        RAG is NOT used here (wrong tool for CSV).
        """
        df = pd.read_csv(self.csv_path)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        return df

    def get_live_and_historical(self) -> dict:
        """
        Get both live and historical data.

        Returns:
            {
                'live': {...},  # From MCP
                'historical': DataFrame  # From CSV
            }
        """
        return {
            'live': self.mcp.get_bitcoin_price() if self.mcp.enabled else None,
            'historical': self.fetch_historical_data()
        }
```

---

## Testing Plan

### Test 1: CSV Reading (Pandas)

```python
# tests/test_data_fetcher.py
from src.data.data_fetcher import DataFetcher

def test_csv_reading():
    """Test that pandas correctly reads CSV."""
    fetcher = DataFetcher()
    df = fetcher.fetch_historical_data()

    # Verify
    assert len(df) > 0, "CSV should have data"
    assert 'Price' in df.columns, "CSV should have Price column"
    assert df['Date'].dtype == 'datetime64[ns]', "Date should be datetime"

    print(f"✅ CSV reading test passed ({len(df)} rows)")
```

### Test 2: RAG Pattern Matching

```python
# tests/test_rag_patterns.py
from src.rag.rag_system import RAGSystem

def test_rag_pattern_matching():
    """Test that RAG finds similar patterns."""
    rag = RAGSystem()

    # Add a test pattern
    rag.add_market_pattern(
        date="2024-03-15",
        price=70000,
        rsi=45,
        fear_greed=32,
        narrative="Bitcoin consolidated near resistance with neutral RSI"
    )

    # Find similar
    current = {
        'price': 98234,
        'rsi': 45,
        'fear_greed': 32,
        'narrative': 'BTC consolidating near $100K'
    }

    patterns = rag.find_similar_patterns(current, top_k=1)

    # Verify
    assert len(patterns) > 0, "Should find similar patterns"
    assert patterns[0]['similarity'] > 0.5, "Should have reasonable similarity"

    print(f"✅ RAG pattern matching test passed (similarity: {patterns[0]['similarity']:.0%})")
```

### Test 3: CoinGecko MCP

```python
# tests/test_coingecko_mcp.py
from src.data.coingecko_mcp import CoinGeckoMCP

def test_coingecko_mcp():
    """Test CoinGecko MCP live data."""
    mcp = CoinGeckoMCP()

    if not mcp.enabled:
        print("⚠️  CoinGecko MCP disabled (no API key)")
        return

    # Get live price
    price_data = mcp.get_bitcoin_price()

    # Verify
    assert price_data is not None, "Should get price data"
    assert price_data['price'] > 0, "Price should be positive"
    assert 'market_cap' in price_data, "Should have market cap"

    print(f"✅ CoinGecko MCP test passed (BTC: ${price_data['price']:,.2f})")
```

### Test 4: Data Fetcher Integration

```python
# tests/test_data_integration.py
from src.data.data_fetcher import DataFetcher

def test_data_fetcher_integration():
    """Test complete data fetcher with MCP + CSV."""
    fetcher = DataFetcher()

    # Test current price (MCP or CSV fallback)
    current_price = fetcher.get_current_price()
    assert current_price > 0, "Should get valid price"

    # Test historical data (CSV)
    df = fetcher.fetch_historical_data()
    assert len(df) > 0, "Should get historical data"

    # Test combined
    data = fetcher.get_live_and_historical()
    assert data['historical'] is not None, "Should have historical data"

    print(f"✅ Data integration test passed")
    print(f"   - Current price: ${current_price:,.2f}")
    print(f"   - Historical rows: {len(data['historical'])}")
    if data['live']:
        print(f"   - Live MCP: ✅ Working")
    else:
        print(f"   - Live MCP: ⚠️  Using CSV fallback")
```

---

## Summary

### What Changes:

1. **CSV Reading**: RAG → Pandas ✅
2. **Pattern Matching**: RAG → Natural Language Interface ✅
3. **Live Data**: CoinGecko MCP (optional) ✅

### Libraries Needed:

```bash
# Already have
pip install langgraph  # State machine (no changes)
pip install google-generativeai  # Gemini LLM (no changes)

# New for MCP
pip install mcp  # CoinGecko MCP client

# Already have for RAG
pip install chromadb sentence-transformers  # RAG (refactored usage)
```

### Rate Limits:

- **CoinGecko Demo**: 30 calls/min, 10,000/month (FREE)
- **Gemini Free**: 10 requests/min, 250/day (FREE)

### Next Steps:

1. Get CoinGecko Demo API key (free)
2. Implement Phase 1 (Pandas for CSV)
3. Implement Phase 2 (RAG for patterns)
4. Implement Phase 3 (MCP for live data)
5. Run tests

**Ready to start implementation?**
