# RAG and MCP Integration Explained

**Purpose**: Understand how RAG (Retrieval-Augmented Generation) and MCP (Model Context Protocol) work together to provide intelligent, live market analysis.

**Success Criteria**:
- Clear understanding of RAG purpose and when to use it
- Clear understanding of MCP purpose and when to use it
- Know the difference between live data (MCP) and historical data (CSV)
- Understand the data flow in chat mode vs backtesting mode

---

## What is RAG (Retrieval-Augmented Generation)?

### Simple Definition
RAG finds similar historical market patterns based on natural language descriptions, helping the LLM provide better context-aware responses.

### Purpose
- Find historical patterns similar to current market conditions
- Provide context to LLM for better trading insights
- Pattern matching across natural language narratives

### What RAG is NOT
- NOT for reading CSV files (use pandas)
- NOT for structured data queries (use SQL/pandas)
- NOT for live data fetching (use MCP)

### Example

**Input**:
```python
current_market = {
    'price': 98234,
    'rsi': 45,
    'fear_greed': 32,
    'narrative': 'BTC consolidating near $100K'
}
```

**RAG Output**:
```python
[
    {
        'date': '2024-09-10',
        'price': 95000,
        'rsi': 48,
        'fear_greed': 35,
        'narrative': 'Bitcoin near ATH with neutral RSI',
        'similarity': 0.81
    },
    # ... more similar patterns
]
```

### When RAG is Used
- Natural language interface (chat mode)
- Finding historical precedents for current conditions
- Providing context for LLM responses

### Implementation

**File**: `src/rag/rag_system.py`

**Technology**:
- ChromaDB: Vector database
- Sentence Transformers: Text embeddings (all-MiniLM-L6-v2)
- Cosine similarity: Pattern matching

**Success Criteria**:
- Similarity score > 0.5 (50% match)
- Top 3 most similar patterns returned
- Fast retrieval (< 100ms)

---

## What is MCP (Model Context Protocol)?

### Simple Definition
MCP fetches LIVE Bitcoin price and market data from CoinGecko API, providing real-time information to the natural language interface.

### Purpose
- Get current Bitcoin price (live, not historical)
- Fetch market cap, volume, 24h price change
- Alternative to stale CSV data for current queries

### What MCP is NOT
- NOT for backtesting (backtesting always uses CSV)
- NOT for bulk historical data (use CSV)
- NOT for high-frequency trading (rate limits: 30 calls/min)

### Example

**Input**: User asks "what's today's Bitcoin price?"

**MCP Output**:
```python
{
    'price': 89249.00,
    'market_cap': 1781234567890,
    'volume_24h': 45678901234,
    'price_change_24h': -0.47,
    'timestamp': '2025-12-07T17:52:00',
    'source': 'mcp'
}
```

### When MCP is Used
- Natural language interface (chat mode) for current prices
- Real-time market queries ("what's the price today?")
- When user explicitly asks for "live" or "current" data

### When MCP is NOT Used
- Backtesting (always CSV for consistency)
- Historical data queries ("what was the price last month?")
- When user is offline or API unavailable (graceful CSV fallback)

### Implementation

**File**: `src/data_pipeline/coingecko_mcp.py`

**Technology**:
- CoinGecko API (Demo tier - FREE)
- Rate limits: 30 calls/min, 10,000 calls/month
- Automatic rate limiting and retry logic

**Success Criteria**:
- Fetches live price successfully
- Returns None gracefully on failure (triggers CSV fallback)
- Respects rate limits (no 429 errors)
- Response time < 2 seconds

---

## How RAG and MCP Work Together

### Chat Mode Data Flow

```
User asks: "What's today's Bitcoin market like?"
    |
    v
Natural Language Agent
    |
    +-- [1] MCP: Fetch LIVE price
    |        |
    |        +-- Try CoinGecko API
    |        +-- If success: Live price $89,249 (Dec 7, 2025)
    |        +-- If fail: Fallback to CSV (Nov 23, 2025)
    |
    +-- [2] CSV: Load historical data for indicators
    |        |
    |        +-- Calculate RSI, MACD, ATR from historical data
    |        +-- Get last 2685 rows (2018-07-19 to 2025-11-23)
    |
    +-- [3] RAG: Find similar historical patterns
    |        |
    |        +-- Current: price=$89,249, RSI=29.2, fear_greed=32
    |        +-- Query: "BTC near $89K with oversold RSI"
    |        +-- Results: 3 similar patterns from 2024
    |
    v
Combine all data:
    - Live price: $89,249 (MCP)
    - Date: Dec 7, 2025 (from MCP timestamp)
    - RSI: 29.2 (from CSV historical calculation)
    - Similar patterns: 2024-09-10, 2024-06-20, 2024-03-15 (RAG)
    |
    v
LLM Response with rich context
```

### Backtesting Mode Data Flow

```
Backtest Engine
    |
    v
Data Loader (CSV ONLY)
    |
    +-- NO MCP (live data would skew backtesting)
    +-- NO RAG (pattern matching not needed for historical simulation)
    |
    v
Historical data: 2018-07-19 to 2025-11-23
    |
    v
Simulate trades using ONLY historical prices
```

---

## Key Differences

| Aspect | Chat Mode | Backtest Mode |
|--------|-----------|---------------|
| **Data Source** | MCP (live) + CSV (history) | CSV only |
| **RAG Enabled** | Yes (pattern matching) | No |
| **Current Date** | Today (Dec 7, 2025) | Historical dates |
| **Price Source** | Live from API | Historical from CSV |
| **Purpose** | Real-time insights | Strategy validation |

---

## Configuration

### Environment Variables

```env
# CoinGecko API for MCP (optional but recommended)
COINGECKO_DEMO_API_KEY=your_api_key_here
COINGECKO_ENVIRONMENT=demo

# RAG Configuration
RAG_CONFIDENCE_THRESHOLD=0.70  # Minimum similarity for pattern match
```

### How to Get CoinGecko API Key (FREE)

1. Visit: https://www.coingecko.com/en/api/pricing
2. Click "Get Free Demo Key"
3. Sign up (no credit card required)
4. Copy your Demo API key
5. Add to `.env` file

**Demo Tier Limits** (FREE forever):
- 30 calls per minute
- 10,000 calls per month
- Stable (not shared with other users)

---

## Testing

### Test RAG System

```bash
python src/rag/rag_system.py
```

**Expected Output**:
```
[RAG] System initialized with 3 patterns
[OK] Found similar patterns:
  - 2024-09-10: 81% match
  - 2024-06-20: 80% match
  - 2024-03-15: 75% match
```

### Test MCP Integration

```bash
python src/data_pipeline/coingecko_mcp.py
```

**Expected Output**:
```
[COINGECKO] Using Demo API (free tier)
[OK] Bitcoin price: $89,249.00
[OK] 24h Change: -0.47%
```

### Test RAG + MCP Together

```bash
python tests/test_mcp_rag_integration.py
```

**Expected Output**:
```
[MCP] LIVE Bitcoin price: $89,249.00 (as of 2025-12-07 17:52)
[RAG] Found 3 similar patterns
SUCCESS: Agent is using MCP live data with correct date!
```

---

## Troubleshooting

### Issue: MCP not working

**Symptoms**:
- Bot shows "predicted" prices instead of live prices
- Date shows Nov 23, 2025 instead of Dec 7, 2025
- No `[MCP] LIVE Bitcoin price:` message

**Solutions**:
1. Check API key in `.env` file
2. Verify internet connection
3. Check rate limits (30 calls/min)
4. Run `python src/data_pipeline/coingecko_mcp.py` to test directly

### Issue: RAG not finding patterns

**Symptoms**:
- No historical patterns shown in chat responses
- Empty `rag_patterns` list

**Solutions**:
1. Check ChromaDB is installed: `pip install chromadb`
2. Check sentence-transformers: `pip install sentence-transformers`
3. Run `python src/rag/rag_system.py` to test directly
4. Add more patterns to vector database

### Issue: CSV fallback always used

**Symptoms**:
- `[DATA] Loaded historical data...` message
- Price source shows 'csv' instead of 'mcp'

**Expected Behavior**:
This is normal when:
- MCP API is temporarily unavailable
- Rate limit exceeded
- No internet connection
- API key not configured

Graceful fallback ensures bot always works!

---

## Summary

**RAG**: Finds similar historical patterns (natural language matching)
**MCP**: Fetches live current price (real-time data)
**Together**: Provide intelligent, context-aware market analysis

**In Chat Mode**:
- MCP gives you TODAY's price
- RAG gives you historical context
- CSV gives you technical indicators

**In Backtest Mode**:
- Only CSV (no MCP, no RAG)
- Historical consistency
- Strategy validation

Both systems work independently but complement each other perfectly for natural language market analysis.
