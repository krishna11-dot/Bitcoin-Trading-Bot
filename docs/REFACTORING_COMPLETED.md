# Refactoring Completed: RAG + MCP Integration

**Date**: 2025-12-07
**Status**: Complete

---

## Summary

Successfully refactored the Bitcoin trading bot to use the right tools for the right jobs:

1. Pandas for CSV reading (correct tool for tabular data)
2. RAG for natural language pattern matching (correct tool for context)
3. CoinGecko MCP for live cryptocurrency data (optional live data source)

---

## What Changed

### 1. RAG System (NEW)

**File**: `src/rag/rag_system.py`

**Purpose**:
- Natural language pattern matching for historical market conditions
- Provides historical context to LLM in natural language interface
- NOT for reading CSV files (wrong tool)

**Usage**:
```python
from src.rag.rag_system import RAGSystem

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
```

**Dependencies**:
```bash
pip install chromadb sentence-transformers
```

**When RAG is Correct**:
- Finding similar historical market narratives
- Providing context for LLM responses
- Pattern matching across natural language descriptions

**When RAG is Wrong**:
- Reading CSV files (use pandas)
- Extracting tabular data (use SQL/pandas)
- Any task better suited for simpler tools

---

### 2. CoinGecko MCP Client (NEW)

**File**: `src/data_pipeline/coingecko_mcp.py`

**Purpose**:
- Fetch live Bitcoin price from CoinGecko API
- Alternative to historical CSV data
- Optional feature for natural language interface

**Rate Limits**:
- Demo API (FREE): 30 calls/min, 10,000 calls/month
- Pro API (Paid): 500 calls/min, 500,000 calls/month

**Usage**:
```python
from src.data_pipeline.coingecko_mcp import CoinGeckoMCP

mcp = CoinGeckoMCP()

# Get live BTC price
price_data = mcp.get_bitcoin_price()
if price_data:
    print(f"BTC: ${price_data['price']:,.2f}")

# Get market chart
chart = mcp.get_market_chart(days=7)
```

**When MCP is Used**:
- Natural language interface (chat mode) for live prices
- Real-time market queries
- Current price checks

**When MCP is NOT Used**:
- Backtesting (always uses CSV for consistency)
- Bulk historical data (use CSV)
- High-frequency queries (respect rate limits)

---

### 3. Unified Data Fetcher (NEW)

**File**: `src/data_pipeline/unified_data_fetcher.py`

**Purpose**:
- Intelligently fetch data from best available source
- Priority: Try CoinGecko MCP, fall back to CSV
- Seamless source switching

**Usage**:
```python
from src.data_pipeline.unified_data_fetcher import UnifiedDataFetcher

# Normal mode (tries MCP, falls back to CSV)
fetcher = UnifiedDataFetcher(force_csv=False)

# Get current price
price, source = fetcher.get_current_price()
print(f"BTC: ${price:,.2f} (source: {source})")

# Get both live and historical
data = fetcher.get_combined_data()

# Backtest mode (only CSV)
fetcher_backtest = UnifiedDataFetcher(force_csv=True)
```

**Data Source Priority**:
1. CoinGecko MCP (live data) - if available and not forced to CSV
2. CSV (historical data) - fallback or backtest mode

---

### 4. Natural Language Agent (UPDATED)

**File**: `src/natural_language/agent.py`

**Changes**:
- Added RAG system for pattern matching
- Integrated unified data fetcher (MCP + CSV)
- Updated `_check_market()` method
- Added `rag_context` to agent state

**What Was Added**:
```python
# Initialize RAG system
self.rag = RAGSystem()

# Initialize unified data fetcher
self.data_fetcher = UnifiedDataFetcher(force_csv=False)
```

**New Behavior**:
- Tries to fetch live price from CoinGecko MCP
- Falls back to CSV if MCP unavailable
- Uses RAG to find similar historical patterns
- Provides richer context to LLM for better responses

**Backward Compatibility**:
- Still works without MCP (uses CSV only)
- Still works without RAG (pattern matching disabled)
- No breaking changes to existing functionality

---

### 5. Environment Variables (UPDATED)

**Files**:
- `.env.example`
- `.env.template`

**Added**:
```env
# CoinGecko API for live cryptocurrency data (optional)
COINGECKO_DEMO_API_KEY=your_coingecko_demo_api_key_here
COINGECKO_ENVIRONMENT=demo
```

**How to Get API Key**:
1. Visit: https://www.coingecko.com/en/api/pricing
2. Click "Get Free Demo Key"
3. Sign up (free account)
4. Copy Demo API key
5. Add to `.env` file

---

## What Did NOT Change

### 1. Data Loader (UNCHANGED)

**File**: `src/data_pipeline/data_loader.py`

**Status**: No changes needed

**Why**:
- Already uses pandas correctly for CSV reading
- No misuse of RAG for CSV files
- Works perfectly as is

### 2. Backtest Engine (UNCHANGED)

**File**: `src/backtesting/backtest_engine.py`

**Status**: No changes needed

**Why**:
- Always uses CSV data (correct for backtesting)
- `enable_rag=False` already set
- Historical consistency maintained
- No impact from MCP integration

### 3. Decision Box (UNCHANGED)

**File**: `src/decision_box/trading_logic.py`

**Status**: No changes needed

**Why**:
- Trading logic unaffected
- Still receives data the same way
- No modifications to strategies

### 4. Modules 1-3 (UNCHANGED)

**Files**:
- `src/modules/module1_technical.py`
- `src/modules/module2_sentiment.py`
- `src/modules/module3_prediction.py`

**Status**: No changes needed

**Why**:
- Technical indicators calculated same way
- Sentiment analysis unchanged
- ML predictions unchanged
- All receive pandas DataFrames as before

---

## Architecture Changes

### Before (v1.0):
```
Natural Language Interface
    |
    v
Data Loader (pandas reads CSV)
    |
    v
Historical Data Only
```

### After (v2.0):
```
Natural Language Interface
    |
    +-- RAG System (pattern matching)
    |
    +-- Unified Data Fetcher
            |
            +-- Try CoinGecko MCP (live data)
            |
            +-- Fall back to CSV (historical data)
    |
    v
Historical Data + Live Data (optional)
```

**Backtest Mode (Unchanged)**:
```
Backtest Engine
    |
    v
Data Loader (pandas reads CSV)
    |
    v
Historical Data Only (CSV)
```

---

## File Structure

### New Files Created:
```
src/rag/
    __init__.py                  # RAG package
    rag_system.py                # RAG implementation

src/data_pipeline/
    coingecko_mcp.py             # CoinGecko MCP client
    unified_data_fetcher.py      # Unified data fetcher
```

### Updated Files:
```
src/natural_language/
    agent.py                     # Integrated RAG + unified fetcher

.env.example                     # Added CoinGecko API keys
.env.template                    # Added CoinGecko API keys
```

### Unchanged Files:
```
src/data_pipeline/
    data_loader.py               # NO CHANGES (already correct)

src/backtesting/
    backtest_engine.py           # NO CHANGES (works as is)

src/decision_box/
    trading_logic.py             # NO CHANGES (unaffected)

src/modules/
    module1_technical.py         # NO CHANGES (same logic)
    module2_sentiment.py         # NO CHANGES (same logic)
    module3_prediction.py        # NO CHANGES (same logic)
```

---

## Testing Checklist

### Test 1: RAG System
```bash
python src/rag/rag_system.py
```

**Expected**:
- Creates vector database
- Adds sample patterns
- Finds similar patterns with >0.7 similarity
- Returns results in correct format

### Test 2: CoinGecko MCP Client
```bash
python src/data_pipeline/coingecko_mcp.py
```

**Expected**:
- Connects to CoinGecko API
- Fetches Bitcoin price
- Returns data in correct format
- Respects rate limits

### Test 3: Unified Data Fetcher
```bash
python src/data_pipeline/unified_data_fetcher.py
```

**Expected**:
- Tries MCP, falls back to CSV
- Returns valid data from available source
- Clear logging of data sources
- Backtest mode forces CSV only

### Test 4: Natural Language Interface
```bash
python main.py --mode chat
```

**Expected**:
- Uses unified data fetcher
- Finds similar patterns with RAG (if enabled)
- Provides richer responses with historical context
- Falls back gracefully if MCP/RAG unavailable

### Test 5: Backtest Engine (Regression Test)
```bash
python main.py --mode backtest --months 1
```

**Expected**:
- Works exactly as before
- Uses CSV data only (not MCP)
- Same metrics and results
- No errors or warnings

---

## Dependencies

### New Dependencies Added:
```bash
# For RAG system
pip install chromadb sentence-transformers

# For MCP client (no new dependencies, uses requests)
# requests is already installed
```

### Optional Dependencies:
- `chromadb`: For RAG pattern matching (gracefully disabled if not installed)
- `sentence-transformers`: For text embeddings (gracefully disabled if not installed)

### Installation:
```bash
# Install all dependencies
pip install -r requirements.txt

# Or with uv
uv pip install -r requirements.txt
```

---

## Migration Guide

### For Existing Users:

1. Pull latest code from GitHub
2. Install new dependencies:
   ```bash
   pip install chromadb sentence-transformers
   ```
3. Get CoinGecko Demo API key (optional):
   - Visit: https://www.coingecko.com/en/api/pricing
   - Get free Demo key
   - Add to `.env`: `COINGECKO_DEMO_API_KEY=your_key`
4. Run tests to verify everything works
5. Use chat mode to try new features

### No Breaking Changes:
- Existing functionality unchanged
- Backtest results same as before
- RAG and MCP are optional enhancements
- System works without them (graceful degradation)

---

## Key Insights (From Mentor)

### On RAG Usage:
> "RAG should not be used to extract tabular data. Use SQL or PySpark for tabular data."

**What we did**:
- Use pandas for CSV (tabular data) - Correct
- Use RAG for natural language pattern matching - Correct
- RAG provides context, not primary data source

### On Tool Selection:
> "RAG is powerful. But if you use it for places where its complexity is not used, then it might actually be like using LLM instead of traditional ML where ML would be better."

**What we did**:
- Simple CSV reading: pandas (simple tool)
- Natural language patterns: RAG (complex tool, justified)
- Live data fetching: MCP client (right tool)

---

## Summary

### What Works Now:

1. CSV Reading: Pandas (already correct)
2. Natural Language Patterns: RAG (newly added)
3. Live Data: CoinGecko MCP (newly added)
4. Backtesting: Unchanged, works as before

### Benefits:

- Right tool for each job
- Better LLM responses with RAG context
- Optional live data via MCP
- No breaking changes
- Graceful degradation if dependencies unavailable

### Next Steps:

1. Test all components
2. Use chat mode to experience improvements
3. Optionally enable CoinGecko MCP for live data
4. Add more historical patterns to RAG over time

---

**Refactoring Status**: Complete + CRITICAL BUGS FIXED (2025-12-07)
**Backward Compatibility**: Maintained
**Breaking Changes**: None
**New Features**: RAG pattern matching, CoinGecko MCP integration

---

## CRITICAL BUG FIXES (2025-12-07)

### Bug 1: Date Confusion in Chat Interface ✅ FIXED

**Problem**: Agent used CSV date (Nov 23, 2025) instead of current date (Dec 7, 2025), causing LLM to think "today" was in the past.

**Fix**: [agent.py:484-505](../src/natural_language/agent.py#L484-L505) now uses `datetime.now().date()` when MCP is active.

**Impact**: Chat interface now correctly shows today's date and live prices!

### Bug 2: Unclear Logging ✅ FIXED

**Problem**: MCP success messages were generic, users couldn't tell if MCP was working.

**Fix**: [unified_data_fetcher.py](../src/data_pipeline/unified_data_fetcher.py) now shows clear `[MCP] ✓` messages.

**Impact**: Users can now see when live data is being used!

See [MCP_FIX_APPLIED.md](MCP_FIX_APPLIED.md) for complete details.

---
