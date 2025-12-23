# BTC Intelligent Trader

A sophisticated Bitcoin trading bot that uses machine learning, technical indicators, and multiple trading strategies to execute automated trades on Binance.

---

## 1. PROBLEM - Why Did We Build This?

**The Challenge:**
- Manual Bitcoin trading requires 24/7 monitoring of price movements
- Emotional decision-making leads to poor trade timing (buying high, selling low)
- Missing profitable opportunities during sleep or work hours
- Difficulty combining multiple signals (technical indicators, sentiment, ML predictions)
- High risk without proper stop-loss and risk management

**The Need:**
An automated trading system that:
- Monitors Bitcoin 24/7 without human intervention
- Makes data-driven decisions free from emotions
- Combines technical analysis, sentiment, and ML predictions intelligently
- Executes trades automatically with proper risk management
- Runs reliably as a background service (local or cloud)

---

## 2. SOLUTION - What Does It Do?

An intelligent Bitcoin trading bot that:
- **Trades automatically** using DCA (Dollar Cost Averaging) and Swing Trading strategies
- **Predicts price direction** using Hybrid Linear Regression + RandomForest ML model (7-day forecasts)
- **Analyzes market conditions** with technical indicators (RSI, MACD, ATR, SMA)
- **Reads market sentiment** using Fear & Greed Index
- **Manages risk automatically** with stop-loss, take-profit, and position sizing
- **Runs 24/7** as a Windows Service (local) or cloud deployment
- **Notifies you** via Telegram and Gmail for every trade
- **Learns from history** using RAG (Retrieval-Augmented Generation) for pattern matching
- **Tracks business metrics** (Portfolio Value, Total Return, Win Rate) and technical metrics (ML accuracy, signal quality) in real-time

---

## 3. RESULT - Did It Work?

### Business Metrics (What Matters)

**Backtest Performance (Example - Run `python main.py --mode backtest` for your actual metrics):**
```
Initial Capital:      $10,000
Final Portfolio:      Varies based on market period
Total Return:         Target >15% (backtest to verify)
Buy & Hold Return:    Baseline comparison
Strategy Advantage:   Goal: Beat buy-and-hold

Win Rate:             Target >55% (profitable trades)
Avg Trade Return:     Measured per trade
Total Trades:         Depends on signal frequency
Sharpe Ratio:         Target >1.0 (risk-adjusted return)
Max Drawdown:         Target <25% (worst peak-to-valley loss)
```

**To See Your Actual Results:**
```bash
python main.py --mode backtest
```
This will run a 6-month backtest and display real business and technical metrics.

**Live Trading Performance (Binance Testnet - Paper Trading):**
```
Status:               DEPLOYED & RUNNING
Portfolio Value:      $104,400.67
Total Return:         +0.00% (just started)
Trades Executed:      1 trade
Signal Execution:     100.0% (all signals executed successfully)
Uptime:               24/7 via Windows Service (NSSM)
```

**Success Criteria (Targets):**
- Total Return >15%
- Sharpe Ratio >1.0 (risk-adjusted return)
- Max Drawdown <25% (maximum loss from peak)
- Win Rate >55% (more wins than losses)
- Beat Buy-and-Hold (better than passive holding)

Run backtest to verify these criteria are met for your chosen time period.

### Technical Metrics (Why It Works)

**Model Performance (Measured in Backtest):**
```
ML Direction Accuracy:    Target >65% (predicts UP/DOWN correctly)
ML Price Error (RMSE):    Measured in $ (average prediction error)
RSI Signal Win Rate:      Target >60% (RSI <30 = good buy signal)
MACD Signal Win Rate:     Target >55% (MACD crossover accuracy)
F&G Correlation:          Measured 0-1 (sentiment tracks returns)
```

**Strategy Performance (Measured in Backtest):**
```
DCA Strategy Win Rate:        Target >60% (small consistent buys)
Swing Strategy Win Rate:      Target >50% (larger opportunistic trades)
Stop-Loss Strategy:           Limits losses (protection, not profit)
```

**Key Insight - Why This Works:**
The bot aims to beat buy-and-hold by:
1. **Timing entries better** - Buys during dips (RSI <30) instead of random times
2. **Avoiding bad timing** - Skips buying during extreme market fear (F&G <40)
3. **Taking profits** - Exits during overheated markets (RSI >70)
4. **Protecting capital** - Stops losses early (ATR-based stop-loss at -2x ATR)

Business impact = Better entry timing + Profit-taking + Loss protection = More profit per trade

---

## 4. HOW IT WORKS - System Architecture

The bot uses a modular architecture with 3 core modules feeding into a central Decision Box, plus an optional Natural Language Interface layer:

```
                    NATURAL LANGUAGE INTERFACE (Optional)
                          (Chat Mode Only)

    User Question ("What's the BTC price?")
                         ↓
                  ┌──────────────────────────────┐
                  │   LANGGRAPH AGENT (4 Nodes)  │
                  │                              │
                  │  1. Understand (Gemini LLM)  │
                  │  2. Validate (Guardrails)    │ ← Hard-coded safety
                  │  3. Execute (Decision Box)   │
                  │  4. Respond (Gemini LLM)     │
                  └──────────────────────────────┘
                         ↓
    Natural Language Answer

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                    CORE TRADING SYSTEM

                         DATA PIPELINE
            (CSV Historical Data via Pandas + CoinGecko HTTP API)

  • Loads historical BTC data from CSV using Pandas (core trading)
  • Fetches live prices via CoinGecko HTTP API (chat mode)
  • RAG pattern matching for natural language queries (chat mode only)
  • Manages rate limiting and API calls

  NOTE: We use direct HTTP API calls (requests.get()), NOT
  Model Context Protocol (MCP). Reasons: simpler debugging, no protocol
  overhead, direct control over requests.


                                 ↓


         ↓                       ↓                       ↓

    MODULE 1             MODULE 2             MODULE 3
   TECHNICAL            SENTIMENT            PREDICTION
   INDICATORS           ANALYSIS                (ML)

 • RSI                • Fear & Greed       • Linear Reg +
 • MACD                 Index                RandomForest
 • ATR                • Market             • 5 features
 • SMA 50/200           sentiment            (16 aggregated)
                      • Confidence         • 7-day window
                        multiplier         • Direction
                                             (UP/DOWN)
                                           • Confidence




                                ↓

                        DECISION BOX
                       (Trading Logic)

                     • DCA Strategy
                     • Swing Strategy
                     • Stop-Loss Logic
                     • Take-Profit Logic
                     • Risk Management
                     • Position Sizing


                                ↓

                        EXECUTION
                      (Binance Executor)

                     • Place buy/sell
                       orders
                     • Manage positions
                     • Track portfolio

                                ↓

                   NOTIFICATIONS & LOGGING

                  • Telegram Bot (real-time alerts)
                  • Gmail (email notifications)
                  • Google Sheets (trade logging)

```

### How It Works:

#### Core Trading Flow (Modes: backtest, live)

1. **Data Pipeline** fetches BTC data from multiple sources:
   - **Binance API**: Real-time trading data (live mode)
   - **CoinGecko HTTP API**: Optional live prices for chat mode (FREE Demo tier: 30 calls/min)
   - **CSV Historical Data**: Backtesting and technical indicators
   - **RAG System**: Historical pattern matching for natural language context

   **Data Source Selection**:
   - Chat mode: CoinGecko API (live) → CSV fallback
   - Backtest mode: CSV only (no API calls for historical consistency)

   **Why HTTP API Instead of MCP (Model Context Protocol)?**
   - **Simpler debugging**: Direct `requests.get()` calls - easy to inspect with print statements
   - **No protocol overhead**: No need for MCP server/client setup
   - **Direct control**: Full control over request headers, params, error handling
   - **Easier to understand**: Standard REST API pattern familiar to all developers
   - **Note**: The file is named `coingecko_mcp.py` but it's just an HTTP API client, NOT using MCP protocol

   **RAG Usage Note**: Used for natural language pattern matching (e.g., "similar market conditions"), NOT for extracting tabular data.
   For tabular data, use SQL or Pandas (simpler, more efficient). RAG is powerful but should be used where its complexity is justified.

2. **Module 1** calculates technical indicators (RSI, MACD, ATR, SMA 50/200)

3. **Module 2** analyzes market sentiment using Fear & Greed Index

4. **Module 3** uses Hybrid Linear Regression + RandomForest ML model with 5 non-redundant features to predict price direction and confidence
   - Linear Regression: Captures linear trends and extrapolates beyond training data
   - RandomForest: Learns non-linear patterns and deviations from trend
   - 5 base features → 16 aggregated features (48% reduction from v1.0's 31 features)
   - Features: Linear trend (1), Linear residual (1), volatility (1), volume (1), intraday range (1)
   - Predicts 7 days ahead using 7-day rolling window
   - Note: ML is ONE signal - Decision Box combines ML + technical indicators + sentiment for reliability

**How Modules Combine for Profit:**

The Decision Box combines all three modules to make profitable trading decisions:

Example BUY Signal:
- Module 3 (ML): UP prediction (70% confidence)
- Module 1 (RSI): 28 (oversold - good entry)
- Module 2 (Fear & Greed): 35 (fear - buy opportunity)
→ Decision: BUY - Lower cost basis = Higher profit potential

Example SELL Signal:
- Module 3 (ML): DOWN prediction (65% confidence)
- Module 1 (RSI): 72 (overbought - exit signal)
- Module 1 (MACD): Bearish divergence
→ Decision: SELL - Take profit before correction

Why combine them?
- ML predicts DIRECTION (where price is going)
- Technical Indicators provide TIMING (when to enter/exit)
- Together: Buy at the RIGHT TIME in the RIGHT DIRECTION = Profit

See [docs/WHY_LINEAR_REGRESSION_RANDOMFOREST.md - How ML + Technical Indicators Work Together for Profit](docs/WHY_LINEAR_REGRESSION_RANDOMFOREST.md#how-ml--technical-indicators-work-together-for-profit) for detailed explanation.

5. **Decision Box** combines all signals to make trading decisions (DCA, Swing, Stop-Loss, Take-Profit)

6. **Execution** executes trades on Binance Testnet

7. **Notifications** sends alerts via Telegram, Gmail, and logs to Google Sheets

#### Natural Language Interface (Mode: chat)

**Tool Orchestration Architecture - How LLMs Take Actions**

This system implements the 4-step tool orchestration pattern that allows an LLM to go beyond conversation and actually execute actions in the digital world.

**The Core Problem (Why Tool Orchestration Exists):**
```
LLMs alone are "probabilistic maps of language" as  they learn how words and ideas
relate to one another. But that only gets you so far:

  User: "What is 233 divided by 7?"
  LLM alone: "33.14" (WRONG - it's guessing based on patterns, not computing)
  LLM + Calculator tool: "33.2857..." (CORRECT - actual computation)

The same applies to trading:
  User: "What's the BTC price?"
  LLM alone: "$95,000" (WRONG - hallucinating from training data)
  LLM + CoinGecko API tool: "$87,042" (CORRECT - live data from API)
```

**The 4-Step Tool Orchestration Flow:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: DETECT TOOL NEEDED (Understand Node - Gemini LLM)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ PURPOSE: Recognize that user's request requires external action              │
│                                                                              │
│ HOW: LLM is trained (via few-shot prompting) to detect semantic cues:       │
│      "price" → check_market, "news" → query_news, "buy" → get_decision      │
│                                                                              │
│ Input:  "What's today's news sentiment?"                                    │
│ Output: {"intent": "query_news", "parameters": {}, "confidence": 0.95}      │
│                                                                              │
│ WHY LLM HERE? Natural language is AMBIGUOUS:                                │
│   - "bullish news" could mean: news about bulls, positive market sentiment  │
│   - LLM understands CONTEXT and extracts the correct meaning                │
│                                                                              │
│ FILE: src/natural_language/agent.py:_understand_query() (line 266)          │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: GENERATE STRUCTURED FUNCTION CALL (Validate Node - Guardrails)       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ PURPOSE: Validate intent against a "function registry" of allowed actions    │
│                                                                              │
│ THE FUNCTION REGISTRY (Hard-coded, not LLM):                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ VALID_INTENTS = {                                                       │ │
│ │     "check_market",      # Get BTC price, RSI, MACD                     │ │
│ │     "check_portfolio",   # Show holdings, balance                       │ │
│ │     "run_trade",         # Execute trading cycle                        │ │
│ │     "get_decision",      # Get recommendation without executing         │ │
│ │     "analyze_backtest",  # Review past performance                      │ │
│ │     "query_news",        # Search CryptoPanic news via RAG              │ │
│ │     "help"               # General help                                 │ │
│ │ }                                                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ WHY HARD-CODED GUARDRAILS? (Mentor's Guidance)                              │
│ "You cannot rely on prompts to control output. You MUST hard-code           │
│  validation to ensure the output is limited to what you want."              │
│                                                                              │
│ EXAMPLE - Without Guardrails:                                               │
│   LLM might hallucinate: {"intent": "delete_all_data"}                      │
│   System executes dangerous action                                          │
│                                                                              │
│ EXAMPLE - With Guardrails:                                                  │
│   LLM outputs: {"intent": "delete_all_data"}                                │
│   Guardrails: "delete_all_data" not in VALID_INTENTS → Rejected → "help"    │
│                                                                              │
│ PARAMETER VALIDATION (For query_news):                                      │
│   LLM extracts: sentiment = "today's" (WRONG - not a valid sentiment)       │
│   Guardrails: "today's" not in {bullish, bearish, neutral} → Set to None    │
│                                                                              │
│ FILE: src/natural_language/guardrails.py (lines 67-75, 106-111)             │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: EXECUTE IN ISOLATION (Execute Node - Python Code, NO LLM)            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ PURPOSE: Call the actual tool/API with deterministic execution              │
│                                                                              │
│ WHY NO LLM? Execution must be DETERMINISTIC, not probabilistic:             │
│   - LLM computing "233/7": guesses "33.14" (pattern matching)               │
│   - Calculator computing "233/7": returns 33.2857... (actual math)          │
│                                                                              │
│ TOOLS AVAILABLE (based on validated intent):                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Intent          │ Tool Called             │ Data Source                 │ │
│ │─────────────────┼─────────────────────────┼─────────────────────────────│ │
│ │ check_market    │ _check_market()         │ CoinGecko API + CSV         │ │
│ │ query_news      │ _query_news()           │ CryptoPanic → RAG/ChromaDB  │ │
│ │ analyze_backtest│ _analyze_backtest()     │ backtest_results.json       │ │
│ │ get_decision    │ _get_decision()         │ Decision Box logic          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ EXAMPLE - query_news execution:                                             │
│   1. RAG.query_news("Bitcoin market news", sentiment_filter=None)           │
│   2. ChromaDB performs vector similarity search (L2 distance)               │
│   3. Returns: [{title: "JPMorgan...", sentiment: "neutral", sim: 48%}]      │
│                                                                              │
│ KEY INSIGHT: This step has NO LLM involvement - pure Python/API calls       │
│              No hallucination possible - deterministic results              │
│                                                                              │
│ FILE: src/natural_language/agent.py:_execute_tool() (line 341)              │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: RE-INSERT RESULT (Respond Node - Gemini LLM)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ PURPOSE: Format tool results as natural language for the user               │
│          This is called "return injection" - feeding results back to LLM    │
│                                                                              │
│ Input (from Step 3):                                                        │
│   {                                                                         │
│     "query": "Bitcoin market news",                                         │
│     "results": [                                                            │
│       {"title": "JPMorgan launches tokenized fund", "sentiment": "neutral"},│
│       {"title": "BlackRock ETF filing", "sentiment": "neutral"}             │
│     ],                                                                      │
│     "total_indexed_chunks": 3                                               │
│   }                                                                         │
│                                                                              │
│ Prompt to LLM:                                                              │
│   "TODAY'S DATE: 2025-12-19                                                 │
│    User asked: 'What's today's news sentiment?'                             │
│    System returned: {tool_result}                                           │
│    Format this as a natural, friendly response."                            │
│                                                                              │
│ Output (to user):                                                           │
│   "Here's today's news sentiment:                                           │
│    - JPMorgan launches first-ever tokenized money market fund (Neutral)     │
│    - BlackRock Files for Ethereum Staking ETF (Neutral)                     │
│    All news articles today have neutral sentiment."                         │
│                                                                              │
│ WHY LLM HERE AGAIN?                                                         │
│   - Raw tool output is structured data (JSON)                               │
│   - Users want natural language, not JSON dumps                             │
│   - LLM excels at formatting and explanation                                │
│                                                                              │
│ FILE: src/natural_language/agent.py:_format_response() (line 372)           │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Summary - Where LLM is Used vs NOT Used:**

| Step | LLM Used? | Why |
|------|-----------|-----|
| 1. Understand | YES | Parse ambiguous natural language |
| 2. Validate | NO | Hard-coded guardrails prevent hallucination |
| 3. Execute | NO | Deterministic API/database calls |
| 4. Respond | YES | Format results as natural language |

**Data Sources (5 total):**

```
User Question: "What's today's Bitcoin price and news?"
       ↓
3. Execute Node → Fetches data from FIVE sources:
       ├─→ CoinGecko HTTP API: Live BTC price ($87,042 as of Dec 19, 2025)
       ├─→ CSV Historical Data: Technical indicators (RSI, MACD, ATR)
       ├─→ CryptoPanic News API: Fetches news articles (100 req/month free tier)
       ├─→ RAG System (ChromaDB): Semantic search of indexed news
       └─→ Backtesting Results: Strategy performance, trade history, metrics
       ↓
       Combines all sources into structured data
       ↓
4. Respond Node (Gemini LLM) → Formats as natural language:
   "BTC is $87,042 (live from CoinGecko API). RSI is 29.2 (oversold).
    Today's news sentiment is neutral: JPMorgan launched tokenized fund,
    BlackRock filed for ETF."
```

**Data Source Details:**

1. **CoinGecko HTTP API** (NOT MCP Protocol): Live price via direct HTTP requests
   - Used for: Current BTC price in chat mode
   - Fallback: CSV if API unavailable
   - NOT used in backtest mode (historical consistency)
   - **Technical Details**:
     - Implementation: Direct `requests.get()` calls in [coingecko_mcp.py](src/data_pipeline/coingecko_mcp.py)
     - Endpoint: `https://api.coingecko.com/api/v3/simple/price`
     - Authentication: Demo API key (free tier)
     - Rate limit: 30 calls/min
   - **Why NOT using Anthropic's MCP?**
     - MCP = Model Context Protocol (server/client architecture for LLM tool access)
     - We don't need that complexity - simple HTTP calls work fine
     - Easier debugging: `print(response.json())` vs MCP protocol inspection
     - No server setup required: Just `pip install requests`
     - Direct control: Custom headers, retries, timeout handling

2. **CSV Historical Data**: 2018-2025 Bitcoin price history
   - Used for: Technical indicators (RSI, MACD, ATR)
   - Always loaded in background
   - Primary source for backtesting

3. **RAG System (TWO Data Sources)**:

   The RAG (Retrieval-Augmented Generation) system uses ChromaDB to store and search **unstructured text** that can't be queried with SQL or Pandas. We have **TWO** data sources:

   | RAG Source | Data Type | Example Query | Status |
   |------------|-----------|---------------|--------|
   | Coin Descriptions (CoinGecko) | Crypto explanations | "What is Bitcoin?" | Optional |
   | **News Articles (CryptoPanic)** | Real-time news with sentiment | "What's the latest news?" | **Active** |

   **Why RAG Instead of Pandas?**

   ```
   PANDAS (Structured Data):
   df[df['price'] > 90000]  # ✅ Works - exact value match
   df[df['description'].contains('history')]  # ❌ Only keyword match, no semantics

   RAG (Unstructured Text):
   rag.query("Tell me about Bitcoin's history")
   # ✅ Finds: "first successful internet money" (semantic match!)
   # RAG understands "history" relates to "first" and "origins"
   ```

   **The Technology Stack:**

   ```
   TEXT INPUT (news article or coin description)
       ↓
   SentenceTransformer (all-MiniLM-L6-v2)
   - Converts text → 384-dimensional vector
   - Pre-trained on millions of text pairs
   - Understands semantic relationships
       ↓
   ChromaDB (Vector Database)
   - Stores: embedding + text + metadata
   - Location: data/rag_vectordb/chroma.sqlite3
   - Uses L2 distance for similarity search
       ↓
   QUERY: "What's the news about ETF?"
       ↓
   Returns: Top 5 most similar chunks with similarity scores
   ```

   **Key Concept**

   1. **Why 384 Dimensions?**
      - SentenceTransformer (all-MiniLM-L6-v2) outputs 384-D vectors
      - Each dimension captures semantic meaning
      - Similar texts = close vectors in 384D space

   2. **Why L2 Distance?**
      - L2 = Euclidean distance: `sqrt(sum((a[i] - b[i])^2))`
      - Lower distance = more similar
      - Converted to similarity: `1 / (1 + distance)`

   3. **Why ChromaDB?**
      - Free, local, no server needed
      - Persists to SQLite (survives restarts)
      - Simple Python API

4. **Backtest JSON** (optional): `data/processed/backtest_results.json`
   - Used for: Portfolio metrics, past performance
   - Accessed when user asks about "my portfolio" or "backtest results"
   - Contains: Total return, Sharpe ratio, win rate, etc.

5. **CryptoPanic News API** (NEW - Dec 2025): Real-time crypto news with sentiment
   - API: `https://cryptopanic.com/api/developer/v2/posts/`
   - Free tier: 100 requests/month (Developer tier)
   - Used for: News sentiment analysis, market intelligence
   - Indexed into RAG for semantic search

   **CryptoPanic News RAG Architecture:**

   ```
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │ CRYPTOPANIC NEWS RAG SYSTEM                                                  │
   ├─────────────────────────────────────────────────────────────────────────────┤
   │                                                                              │
   │ 1. FETCH NEWS (CryptoPanic API v2)                                          │
   │    └─ GET /api/developer/v2/posts/?currencies=BTC&public=true               │
   │                                                                              │
   │ 2. TEXT CHUNKING (TextChunker)                                              │
   │    └─ Splits long articles into 400-char chunks with 50-char overlap        │
   │    └─ Preserves sentence boundaries for semantic coherence                  │
   │                                                                              │
   │ 3. EMBEDDING (SentenceTransformer)                                          │
   │    └─ Converts each chunk to 384-dimensional vector                         │
   │                                                                              │
   │ 4. STORAGE (ChromaDB)                                                       │
   │    └─ Stores: embedding, text, metadata (title, sentiment, published_at)    │
   │    └─ Collection: "market_patterns"                                         │
   │    └─ Type filter: "news_article"                                           │
   │                                                                              │
   │ 5. QUERY (Semantic Search)                                                  │
   │    └─ User: "Any bullish news?"                                             │
   │    └─ Filter: type="news_article" AND sentiment="bullish"                   │
   │    └─ Returns: Top 5 most similar chunks                                    │
   │                                                                              │
   │ FILES:                                                                       │
   │ ├─ src/data_pipeline/cryptopanic_client.py (API client, rate limiting)      │
   │ ├─ src/rag/text_chunker.py (sentence-boundary chunking)                     │
   │ ├─ src/rag/rag_system.py (add_news_article, query_news methods)             │
   │ └─ src/natural_language/agent.py (_query_news method)                       │
   └─────────────────────────────────────────────────────────────────────────────┘
   ```

   **Why Text Chunking for News?**

   ```
   PROBLEM: News articles are 500-2000 characters
   SentenceTransformer context: 512 tokens max
   Some articles EXCEED the limit!

   SOLUTION: TextChunker splits articles:
   - Chunk size: 400 characters (fits in 512 token limit)
   - Overlap: 50 characters (preserves context at boundaries)
   - Split at sentence boundaries (not mid-sentence)

   EXAMPLE:
   Original article (800 chars): "JPMorgan launches tokenized fund. The fund
   uses blockchain technology. This marks a shift in traditional finance..."

   Chunk 1 (400 chars): "JPMorgan launches tokenized fund. The fund uses
   blockchain technology."

   Chunk 2 (400 chars, with 50-char overlap): "blockchain technology. This
   marks a shift in traditional finance..."
   ```

   **Rate Limiting for CryptoPanic:**

   ```
   Free tier: 100 requests/month
   Conservative limit: 3 requests/day (100/30 = 3.3)

   CACHING STRATEGY:
   - Cache news to: data/cache/cryptopanic/news_BTC_2025-12-19.json
   - Reuse cached data for same-day queries
   - Only hit API once per day per currency
   ```

   **Testing News RAG:**

   ```python
   from src.rag.rag_system import RAGSystem

   rag = RAGSystem()

   # Index news (uses 1 API call)
   result = rag.index_cryptopanic_news(currency='BTC', limit=10)
   print(f"Indexed {result['chunks_indexed']} chunks")

   # Query news semantically
   results = rag.query_news("Bitcoin ETF institutional", top_k=3)
   for r in results:
       print(f"- {r['title'][:50]}... ({r['similarity']:.0%})")
   ```

**Why LangGraph?**
- Industry-standard agent framework 
- Clean state machine architecture (each node has one responsibility)
- State management built-in (shared state flows through nodes)
- Learning experience with modern agentic frameworks

**Safety:**
- LLM used ONLY for understanding questions and formatting responses
- Trading decisions made by Decision Box (NOT by LLM)
- Guardrails are hard-coded (not prompt-based)
- Natural language layer sits ABOVE existing system (no modifications)

**How the LLM Works (Gemini AI):**

The LLM handles exactly TWO tasks:

1. **Understanding** (Natural Language -> JSON):
   - User asks: "What's the BTC price?"
   - LLM classifies intent: `{"intent": "check_market", "confidence": 0.9}`
   - Guardrails validate: Intent must be one of 6 allowed intents
   - Python executes: Fetches real data from CSV/API (NO LLM involved)

2. **Formatting** (Structured Data -> Natural Language):
   - Python returns: `{'current_price': 98234.56, 'rsi': 45.2}`
   - LLM formats: "BTC is trading at $98,234.56. RSI is 45.2 (neutral)."

**Why This Separation?**
- **Safety**: LLM can't make trading decisions (could hallucinate)
- **Reliability**: Python calculations are deterministic, LLM is not
- **Control**: Guardrails prevent unauthorized actions

**Prompt Engineering:**

The prompts use 3 key techniques to ensure reliable output:

1. **Format Specification**: `"Return ONLY valid JSON (no markdown, no extra text)"`
   - Prevents LLM from wrapping JSON in code blocks
   - Without "ONLY": LLM might add preamble like "Sure! Here's the JSON:"

2. **Few-Shot Examples**: 8-10 examples showing desired inputs/outputs
   - Example: `"What's BTC price?" -> {"intent": "check_market"}`
   - Improves accuracy from ~70% (zero-shot) to ~95% (few-shot)

3. **Hard Constraints**: Fixed list of 6 allowed intents
   - `check_market`, `check_portfolio`, `run_trade`, `get_decision`, `analyze_backtest`, `help`
   - LLM can't invent new intents
   - Guardrails reject any unexpected intent using fuzzy matching

**Defense-in-Depth (3 Layers):**
1. Prompt explicitly lists 6 allowed intents (constrains LLM output)
2. Few-shot examples reinforce the constraint (teaches by example)
3. Hard-coded guardrails validate output (Python checks, not LLM)

This approach makes the system transparent, auditable, and safe for trading decisions.

### What You See While It's Running:

**During Live Trading (Binance Testnet), the bot displays:**

**Every Trading Cycle (every 5 minutes):**
- Current BTC price
- Fear & Greed Index score
- Technical indicators (RSI, ATR, MACD)
- Portfolio state (Cash, BTC, Total Value)
- ML prediction (predicted price, direction, confidence)
- Trading decision (BUY/SELL/HOLD)

**Performance Summary (every cycle after 5+ trades):**
- **BUSINESS METRICS** (shown first):
  - Portfolio Value
  - Total Return (%)
  - Max Drawdown (%)
  - Trades Executed
  - Signal Execution Rate (%)
  - Errors

- **TECHNICAL METRICS** (shown second):
  - ML Direction Accuracy (%)
  - ML Price Error (RMSE in $)
  - RSI Signal Win Rate (%)
  - MACD Signal Win Rate (%)
  - Fear & Greed Correlation
  - Strategy Win Rates (DCA, Swing, Stop-Loss)

## Quick Start

New to the project? Start here:
- [Quickstart Guide](docs/QUICKSTART.md) - Get up and running quickly
- [Deployment Strategy](docs/DEPLOYMENT_STRATEGY.md) - Local and cloud deployment guide

## Documentation Index

### Getting Started & Setup

- **[Quickstart Guide](docs/QUICKSTART.md)** - Quick setup and first run
- **[Deployment Strategy](docs/DEPLOYMENT_STRATEGY.md)** - Complete deployment guide (local → cloud)
  - Local deployment with NSSM on Windows
  - Service management and monitoring
  - Cloud deployment preparation
- **[Testing Guide](docs/TESTING_GUIDE.md)** - How to test the trading bot

### Core Architecture

- **[Architecture Guide](docs/ARCHITECTURE_GUIDE.md)** - Complete system architecture
- **[Architecture Summary](docs/ARCHITECTURE_SUMMARY.md)** - High-level architectural overview
- **[Agent Architecture Nuances](docs/AGENT_ARCHITECTURE_NUANCES.md)** - Agent system design details
- **[Metrics Architecture](docs/METRICS_ARCHITECTURE.md)** - Performance metrics and monitoring
- **[Data Flow Architecture](docs/BINANCE_TESTNET_AND_RAG_EXPLAINED.md#data-flow-architecture)** - How data flows through the system

### Trading & Market Data

- **[Binance Testnet & RAG Explained](docs/BINANCE_TESTNET_AND_RAG_EXPLAINED.md)** - Complete guide to:
  - What Binance Testnet is and how it works
  - Getting USDT for testing
  - RAG usage in backtest vs live mode
  - Historical data in live trading
  - Rate limiting protection
  - Common warnings explained

### Machine Learning

- **[Module 3 ML Explained](docs/MODULE3_ML_EXPLAINED.md)** - Complete explanation of ML prediction, features, and extrapolation problem
- **[ML Model Limitations](docs/ML_MODEL_LIMITATIONS.md)** - Understanding ML model constraints
- **[ML Quick Reference](docs/ML_QUICK_REFERENCE.md)** - Quick reference for ML components
- **[Multi-Period Analysis](docs/MULTI_PERIOD_ANALYSIS.md)** - Analyzing multiple timeframes
- **[LLM vs Template Nuances](docs/LLM_VS_TEMPLATE_NUANCES.md)** - LLM-based vs template-based approaches

### Notifications & Integrations

- **[Telegram Setup Guide](docs/TELEGRAM_SETUP_GUIDE.md)** - Complete Telegram bot setup
- **[Telegram Quick Start](docs/TELEGRAM_QUICK_START.md)** - Quick Telegram integration
- **[Gmail Setup Guide](docs/GMAIL_SETUP_GUIDE.md)** - Configure Gmail notifications
- **[Gmail Quick Start](docs/GMAIL_QUICK_START.md)** - Quick Gmail integration
- **[Google Sheets Setup](docs/GOOGLE_SHEETS_SETUP.md)** - Track trades in Google Sheets
- **[Complete Workflow with Telegram](docs/COMPLETE_WORKFLOW_WITH_TELEGRAM.md)** - End-to-end Telegram workflow
- **[Complete Notification Workflow](docs/COMPLETE_NOTIFICATION_WORKFLOW.md)** - All notification systems

### Usage & Features

- **[Natural Language Guide](docs/NATURAL_LANGUAGE_GUIDE.md)** - Using natural language commands
- **[Diagnostic Capabilities](docs/DIAGNOSTIC_CAPABILITIES.md)** - Built-in diagnostic tools
- **[Chat Fixes Summary](docs/CHAT_FIXES_SUMMARY.md)** - Chat interface improvements

### Reference & History

- **[Documentation Index](docs/DOCUMENTATION_INDEX.md)** - Alternative documentation index
- **[V1 Baseline Reference](docs/V1_BASELINE_REFERENCE.md)** - Version 1 baseline for comparison
- **[Test Chat](docs/TEST_CHAT.md)** - Chat interface testing

## Key Features

### Trading Strategies
- **DCA (Dollar Cost Averaging)**: Small, frequent purchases ($30 per trade)
- **Swing Trading**: Larger position-based trades ($500+ per trade)
- **Position Management**: Intelligent position sizing based on portfolio value
- **Risk Management**: Stop-loss, take-profit, and position limits

### Machine Learning - Hybrid Linear + RandomForest Architecture (v2.0)

**Architecture Overview:**
- **Hybrid Model**: Linear Regression (trend) + RandomForest (deviations)
- **Base Features**: 5 non-redundant features (down from 10)
- **Aggregated Features**: 16 total (down from 31, 48% reduction)
- **Training Performance**: 30x faster (20 seconds vs 10+ minutes)
- **Prediction Horizon**: 7 days ahead (UP/DOWN direction)

**Why Hybrid Architecture?**

The bot uses a two-stage approach to solve complementary problems:

1. **Linear Regression (Trend Extrapolation)**:
   - **What it does**: Captures linear price trends using least squares regression
   - **Why it's needed**: RandomForest CANNOT extrapolate beyond training data (e.g., trained on $20k-$90k, fails at $100k+)
   - **Features created**: `lr_trend` (extrapolated price), `lr_residual` (deviation from trend)
   - **Mathematical formula**: y = mx + b (closed-form solution for 30x speedup)
   - **Example**: If BTC trends from $60k → $70k over 7 days, Linear Regression predicts $80k (extrapolates)

2. **RandomForest (Non-Linear Deviations)**:
   - **What it does**: Learns complex patterns and deviations from the linear trend
   - **Why it's needed**: Markets have non-linear behaviors (volatility spikes, sentiment shifts)
   - **Input**: 5 features including Linear Regression outputs + volatility + volume
   - **Output**: Direction (UP/DOWN) + Confidence (0-1)
   - **Example**: Linear Regression says $80k, but high volatility + volume spike → RandomForest adjusts to DOWN

**Why RandomForest for Time Series? (Isn't this a regression problem?)**

Time series data (daily prices) is converted to tabular format using **rolling windows**:

```
Original Time Series:
Day 1: $60k
Day 2: $61k
Day 3: $62k
...
Day 7: $66k
Day 8: $67k (predict this)

Converted to Tabular (Rolling Window = 7 days):
Row 1: [features from days 1-7] → Label: Day 8 direction (UP)
Row 2: [features from days 2-8] → Label: Day 9 direction (DOWN)
...

RandomForest trains on these rows (each row = one prediction scenario)
```

This approach lets RandomForest capture patterns like:
- "When volatility is low and volume spikes, price usually goes UP"
- "When RSI >70 and Linear Regression shows uptrend, price usually corrects DOWN"

**Feature Engineering: 5 Non-Redundant Features (v2.0)**

**Selected Features** (eliminated redundancy through correlation analysis):
1. `lr_trend`: Linear Regression trend (extrapolates to next step)
2. `lr_residual`: Deviation from Linear Regression (captures anomalies)
3. `rolling_std`: 7-day price volatility (standard deviation)
4. `volume_spike`: Volume relative to average (identifies unusual activity)
5. `high_low_range`: Intraday volatility (daily high - low)

**Removed Features** (v1.0 → v2.0):
- ❌ `price_change_pct`, `roc_7d` → Redundant (both measure momentum, captured by `lr_trend`)
- ❌ `sma_ratio`, `momentum_oscillator` → Redundant (both measure trend relative to moving average)
- ❌ `higher_highs`, `lower_lows` → Low importance (binary flags with weak signal)
- ❌ `sma_30` → Redundant (trend already captured in `lr_trend`)

**Feature Aggregation** (Rolling Window Statistics):
Each feature is aggregated over 7-day window: min, max, avg
- Example: `rolling_std` → `rolling_std_min`, `rolling_std_max`, `rolling_std_avg`
- Total: 5 base features × 3 aggregations + 1 (current_price) = **16 features**
- Previous version: 10 base features × 3 + 1 = **31 features** (48% reduction)

**Performance Optimization: Closed-Form Linear Regression**

**Original Implementation** (SLOW - 10+ minutes):
```python
for i in range(2685):  # For each row
    lr_model = LinearRegression()  # Create sklearn object
    lr_model.fit(X, y)  # Fit model (overhead)
    prediction = lr_model.predict(...)
```

**Optimized Implementation** (FAST - 20 seconds, 30x faster):
```python
# Closed-form least squares formula (no sklearn overhead)
for i in range(2685):
    slope = Σ((x - x̄)(y - ȳ)) / Σ((x - x̄)²)
    intercept = ȳ - slope * x̄
    trend = slope * next_step + intercept  # Direct calculation
```

**Why this works**: Linear Regression has a mathematical closed-form solution. No need for sklearn's iterative fitting - pure NumPy math is 30x faster and gives identical results.

**Blockchain Data Usage**

**What is it?**
- Optional features: `hash_rate`, `mempool_size`, `block_size`
- Source: Bitcoin network metrics (mining difficulty, transaction queue, block capacity)

**How is it used?**
- **Feature Engineering**: Creates 3 additional technical features (aggregated to 9)
- **NOT for RAG**: Blockchain data is used in ML model, NOT for natural language pattern matching
- **Fallback**: If blockchain API fails, uses volume-based features instead

**Example**:
```
High hash_rate + Large mempool_size = Network congestion → DOWN prediction
Low hash_rate + Empty mempool = Network activity low → Neutral
```

**Current Status**: Blockchain features optional (enable with `enable_blockchain=True`)

**Known Limitations & Trade-offs**

✅ **Solved Problems**:
- **Extrapolation**: Linear Regression handles new all-time high prices
- **Speed**: 30x faster training (20 seconds vs 10+ minutes)
- **Overfitting Risk**: Fewer features (16 vs 31) reduces overfitting

⚠️ **Known Limitations**:
- **Direction Accuracy**: 60% (down from 65% with 10 features) - acceptable trade-off
- **Extreme Gaps**: If trained on $3k-$49k and tested on $100k+, accuracy drops (but production model retrains daily, so gaps are small)
- **Linear Assumption**: Linear Regression assumes trends continue linearly (markets can be non-linear)

**Why ML is ONE Signal** (Not Sole Decision Maker):
- Decision Box combines: ML prediction + RSI + MACD + Fear & Greed Index + ATR
- ML provides direction + confidence, but final trade decision uses ALL signals
- Example: ML says "UP 90% confidence" but RSI=75 (overbought) → Decision Box says "HOLD" (wait for cooldown)

**Model Training & Prediction Flow**:
1. **Training**: Pre-trained on all historical data (2018-2025, 2,685+ rows)
2. **Feature Creation**: Linear Regression + 4 technical features → 16 aggregated features
3. **RandomForest Training**: Learns patterns from 16 features → Direction (UP/DOWN)
4. **Prediction**: Every 5 minutes in live mode, every day in backtest
5. **Confidence Score**: RandomForest probability (0-1) indicates prediction certainty

---

#### Visual Architecture Diagrams

**RandomForest = Technique (Classifier vs Regressor)**:
```
                    ┌─────────────────────────┐
                    │     RANDOM FOREST       │
                    │      (Technique)        │
                    │   Many trees voting     │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┴──────────────────┐
              │                                     │
              ▼                                     ▼
┌─────────────────────────────┐     ┌─────────────────────────────┐
│   RandomForestCLASSIFIER    │     │   RandomForestREGRESSOR     │
│   Trees vote on CATEGORIES  │     │   Trees vote on NUMBERS     │
│   Output: "UP" or "DOWN"    │     │   Output: $73,500.00        │
│   Answer = Most common vote │     │   Answer = Average vote     │
└─────────────────────────────┘     └─────────────────────────────┘

YOUR MODELS:
1. RandomForestClassifier → Predicts DIRECTION (UP/DOWN) + confidence
2. RandomForestRegressor  → Predicts PRICE ($73,500)
Both use SAME technique (many trees voting), different output type!
```

**5 Base Features → 16 Total Features (Rolling Window)**:
```
STEP 1: 5 base features calculated per day
  lr_trend, lr_residual, rolling_std, volume_spike, high_low_range

STEP 2: Aggregate each feature over 7-day window
  ┌─────────────────────────────────────────────────────────────┐
  │                    7-DAY ROLLING WINDOW                     │
  │   [Day 1] [Day 2] [Day 3] [Day 4] [Day 5] [Day 6] [Day 7]  │
  └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
     For each feature: calculate MIN, MAX, AVG
     lr_trend → lr_trend_min, lr_trend_max, lr_trend_avg

STEP 3: The Math
  5 features × 3 aggregations = 15 features
  + 1 current_price = 16 TOTAL FEATURES
```

**Two Models: Same Input, Different Output**:
```
                    ┌─────────────────────────────────────┐
                    │          16 INPUT FEATURES          │
                    │  (lr_trend_min, lr_trend_max, ...)  │
                    └──────────────────┬──────────────────┘
                                       │
              ┌────────────────────────┴────────────────────────┐
              │                                                 │
              ▼                                                 ▼
┌──────────────────────────────────┐     ┌──────────────────────────────────┐
│      RandomForest REGRESSOR      │     │      RandomForest CLASSIFIER     │
│                                  │     │                                  │
│  QUESTION: "What will the       │     │  QUESTION: "Which DIRECTION      │
│             PRICE be in 7 days?" │     │             will price go?"      │
│                                  │     │                                  │
│  OUTPUT:                         │     │  OUTPUT:                         │
│  predicted_price: $73,500        │     │  direction: "UP"                 │
│                                  │     │  confidence: 0.68                │
└──────────────────────────────────┘     └──────────────────────────────────┘
              │                                          │
              └────────────────┬─────────────────────────┘
                               │
                               ▼
              ┌─────────────────────────────────────────┐
              │        BOTH OUTPUTS (NOT COMBINED)      │
              │  Decision Box uses BOTH independently   │
              └─────────────────────────────────────────┘
```

**Complete ML Pipeline**:
```
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: RAW DATA → CSV/API (Date, Price, High, Low, Volume)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: FEATURE ENGINEERING (5 base features)                         │
│   Linear Regression: lr_trend, lr_residual (can extrapolate to ATH!)  │
│   Volatility: rolling_std, high_low_range                              │
│   Volume: volume_spike                                                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: ROLLING WINDOW AGGREGATION (5 → 16 features)                  │
│   5 features × 3 (min/max/avg) + current_price = 16 features          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ↓
         ┌──────────────────────────┴──────────────────────────┐
         ↓                                                     ↓
┌─────────────────────────┐                    ┌─────────────────────────┐
│ REGRESSOR → Price       │                    │ CLASSIFIER → Direction  │
│ Output: $73,500         │                    │ Output: UP (68% conf)   │
└─────────────────────────┘                    └─────────────────────────┘
         │                                                     │
         └──────────────────────────┬──────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: DECISION BOX                                                  │
│   ML Predictions + RSI + MACD + Fear & Greed + ATR                    │
│   → FINAL DECISION: DCA_BUY / SWING_BUY / HOLD / SELL                 │
└────────────────────────────────────────────────────────────────────────┘

WHY LINEAR REGRESSION FEATURES ARE CRITICAL:
┌─────────────────────────────────────────────────────────────────────────┐
│  WITHOUT lr_trend: RandomForest trained on $20K-$90K FAILS at $100K   │
│  WITH lr_trend: lr_trend extrapolates → RandomForest adjusts → 60%    │
│  This is why Linear Regression is for FEATURE ENGINEERING, not pred.  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

#### Detailed Feature Explanations with Examples

**lr_trend - Where the Price is Heading:**
```
Example: Past 7 days of BTC prices
  Day 1: $60,000
  Day 2: $62,000
  Day 3: $64,000
  Day 4: $66,000
  Day 5: $68,000
  Day 6: $70,000
  Day 7: $72,000

Linear Regression draws a "best fit line" through these points:
  slope = +$2,000 per day

lr_trend = "Where will this line be tomorrow?"
         = $72,000 + $2,000 = $74,000

MEANING: "If the current trend continues, price will be $74,000"
```

**lr_residual - Deviation from Trend:**
```
Example:
  Linear Regression trend says: $72,000 (expected based on trend)
  Actual current price:         $75,000 (reality)

lr_residual = $75,000 - $72,000 = +$3,000

MEANING: "Price is $3,000 ABOVE the trend line"
         → Price is running HOT (maybe overbought, correction coming?)

If lr_residual = -$2,000:
         → Price is BELOW trend line (maybe oversold, bounce coming?)
```

**The Extrapolation Problem Solved:**
```
WITHOUT lr_trend (RandomForest alone):
  Training data: $3,000 to $90,000 (2018-2024)
  Test at $100,000: 49.7% accuracy (worse than random!)
  Problem: RandomForest can only INTERPOLATE (predict within training range)
           It CANNOT EXTRAPOLATE (predict beyond what it's seen)

WITH lr_trend (Hybrid approach):
  Linear Regression: "If $60K→$70K→$80K→$90K, next is $100K→$110K"
  lr_trend extrapolates → RandomForest learns to adjust based on volatility
  Result: 60% accuracy at all-time highs
```

---

#### Why Two RandomForest Models? (Detailed Scenarios)

**REGRESSOR alone - Not Enough:**
```
Predicts: $98,500
Problem: Is that UP or DOWN from current $97,000?
         Only +1.5% gain - is that meaningful?
         No confidence score!
```

**CLASSIFIER alone - Not Enough:**
```
Predicts: UP with 68% confidence
Problem: UP by how much? $100? $10,000?
         No target price for profit-taking!
```

**TOGETHER - Complete Picture:**

**Scenario A - Strong Signal (Take Action):**
```
Regressor: $105,000 (+8% from current $97,000)
Classifier: UP with 85% confidence

Analysis: Large expected gain + High confidence
Decision: SWING_BUY $500 (big position, high conviction)
```

**Scenario B - Weak Signal (Wait):**
```
Regressor: $98,500 (+1.5% from current $97,000)
Classifier: UP with 55% confidence

Analysis: Small expected gain + Low confidence
Decision: HOLD (wait for better opportunity)
```

**Scenario C - Conflicting Signal (Don't Trade):**
```
Regressor: $90,000 (-7% from current, predicts DOWN)
Classifier: UP with 60% confidence

Analysis: Regressor says DOWN, Classifier says UP (conflict!)
Decision: HOLD (signals disagree, too risky)
```

---

#### Decision Box Logic (How Final Decisions are Made)

**Inputs to Decision Box:**
```
FROM ML MODELS:
├── predicted_price: $98,500 (from Regressor)
├── direction: "UP" (from Classifier)
└── confidence: 0.68 (from Classifier)

FROM TECHNICAL INDICATORS:
├── RSI: 45 (neutral - not overbought/oversold)
├── MACD: bullish crossover
└── ATR: $2,345 (volatility level)

FROM SENTIMENT:
└── Fear & Greed Index: 32 (fear - people scared)
```

**Decision Logic (Simplified):**
```python
if direction == "UP" AND confidence > 0.70 AND RSI < 60:
    → SWING_BUY: "ML confident + RSI confirms not overbought"
    → Action: Buy $500 worth (large position)

elif fear_greed < 40 AND RSI < 60:
    → DCA_BUY: "Market fear = good accumulation opportunity"
    → Action: Buy $30 worth (small, defensive)

elif RSI > 70:
    → TAKE_PROFIT: "Overbought, sell some gains"
    → Action: Sell 10% of position

elif direction == "DOWN" AND confidence > 0.75:
    → HOLD or REDUCE: "ML predicts drop with high confidence"
    → Action: Don't buy, maybe sell some

else:
    → HOLD: "No clear signal from any indicator"
    → Action: Wait for better setup
```

**Why Not Just Use ML Alone?**
```
Example of ML + Technical Indicators working together:

ML says: "UP with 80% confidence"
RSI says: 85 (extremely overbought!)

WRONG approach (ML only):
  → BUY (ML says UP!)
  → But price is overbought, likely to drop
  → LOSS

CORRECT approach (ML + RSI):
  → ML says BUY, but RSI says OVERBOUGHT
  → Decision Box: HOLD (wait for RSI cooldown)
  → Avoided the loss!

THE POINT: ML is ONE signal among many
           Decision Box combines ALL signals for safer trading
```

---

See [Module 3 ML Explained](docs/MODULE3_ML_EXPLAINED.md) for detailed technical explanation and [Old vs New Comparison](docs/OLD_VS_NEW_COMPARISON.md) for performance benchmarks.

### Natural Language Interface
- **Chat Mode**: Ask questions in plain English instead of running commands
- **Single-Agent LangGraph**: 4-node state machine (understand → validate → execute → respond)
- **Why LangGraph**: Industry-standard agent framework, clean architecture with state management, resume value
- **Gemini AI Integration**: Free tier (10 requests/min, 250 requests/day) for natural language understanding
- **Hard-Coded Guardrails**: Only 5 allowed intents (check_market, check_portfolio, run_trade, get_decision, help)
- **Safety**: LLM used for understanding/formatting only, NOT for trading decisions (Decision Box unchanged)
- **Zero Code Changes**: Natural language layer sits ABOVE existing system, no modifications to trading logic
- **Examples**: "What's the market like?", "Should I buy?", "Explain DCA strategy"

### Data Sources
- **Binance Testnet**: Real market data with virtual money (paper trading)
- **CSV Historical Data**: Pandas-based loading of historical BTC prices (core trading)
- **MCP CoinGecko API**: Live price data (chat mode only)
- **RAG System**: Pattern matching for natural language queries (chat mode only)
- **Rate Limiting**: Leaky bucket algorithm for API protection

### Notifications & Communication
- **Telegram**: Real-time trade alerts and portfolio updates
- **Gmail**: Email notifications for trades and errors
- **Google Sheets**: Automated trade logging and tracking
- **Chat Interface**: Natural language queries ("What's the BTC price?", "Should I buy?")

## Running the Bot

### Backtest Mode
Test strategies on historical data:
```bash
python main.py --mode backtest
```

### Live Trading Mode
Execute real trades (on testnet):
```bash
python main.py --mode live
```

### Chat Mode (Natural Language Interface)
Ask questions in plain English:
```bash
python main.py --mode chat
```
**Examples:**
- "What's the market situation?"
- "Should I buy now?"
- "Explain DCA strategy"
- "Run a trade cycle"

See [Natural Language Guide](docs/NATURAL_LANGUAGE_GUIDE.md) for setup and examples.

### As a Windows Service (24/7)
Deploy as a background service:
```powershell
# See DEPLOYMENT_STRATEGY.md for complete guide
nssm install BTCTradingBot
nssm start BTCTradingBot
```

## Project Structure

```
btc-intelligent-trader/
 src/                          # Source code
    agents/                   # Agent-based architecture
    data/                     # Data fetching and processing
    execution/                # Trade execution (Binance)
    features/                 # Feature engineering
    ml/                       # Machine learning models
    natural_language/         # LangGraph agent + Gemini AI
    notifications/            # Telegram, Gmail, Sheets
    rag/                      # RAG pattern matching (natural language)
    risk/                     # Risk management
    strategy/                 # Trading strategies
    utils/                    # Utilities and helpers
 docs/                         # All documentation (you are here!)
 logs/                         # Bot execution logs
 data/                         # Historical data cache
 models/                       # Trained ML models
 main.py                       # Entry point
 README.md                     # This file

```

## Configuration

### Environment Variables
Create a `.env` file with your API keys:
```env
# Binance Testnet (for testing)
BINANCE_TESTNET_API_KEY=your_testnet_api_key
BINANCE_TESTNET_SECRET_KEY=your_testnet_secret_key

# Binance Production (for real trading)
BINANCE_API_KEY=your_production_api_key
BINANCE_SECRET_KEY=your_production_secret_key

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Gmail (optional)
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
GMAIL_RECIPIENT=recipient@email.com

# Google Sheets (optional)
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id

# Gemini AI for Natural Language Interface (optional)
GEMINI_API_KEY=your_gemini_api_key_here
```

See setup guides in [docs/](docs/) for detailed configuration instructions.

## Technology Stack

### Core System
- **Python 3.10.11**: Core programming language (tested and verified version)
- **UV**: Fast Python package manager
- **Pandas/NumPy**: Data processing and feature engineering
- **TA-Lib**: Technical indicators (RSI, MACD, Bollinger Bands)

### Machine Learning
- **Hybrid Architecture**: Linear Regression (trend extrapolation) + RandomForest (non-linear patterns)
- **scikit-learn**: Linear Regression (closed-form optimization) + RandomForest Classifier
- **Feature Engineering**: 5 base features → 16 aggregated features (v2.0, 48% reduction from v1.0)

### Trading & Data
- **Binance API (CCXT)**: Market data and trade execution
- **Pandas**: CSV historical data loading (core trading system)
- **MCP CoinGecko API**: Live price data (chat mode)
- **RAG (ChromaDB + Sentence Transformers)**: Pattern matching for natural language queries

### Natural Language Interface
- **Google Gemini AI**: LLM for natural language understanding (free tier: 10 RPM, 250 RPD)
- **LangGraph**: Agent workflow orchestration (4-node state machine)
- **Pydantic**: Data validation and hard-coded guardrails

### Notifications
- **Telegram Bot API**: Real-time trade alerts
- **Gmail API**: Email notifications
- **Google Sheets API**: Automated trade logging

### Deployment
- **NSSM**: Windows service management (local 24/7 deployment)
- **Google Cloud Platform (GCP)**: Cloud deployment via Compute Engine (e2-small, Ubuntu 25.10)

## Development Status

**Current Status**: Fully operational on Binance Testnet
- Local deployment: Complete and tested (Windows Service via NSSM)
- Live trading: Working on testnet
- Machine learning: Trained and predicting (known extrapolation limitation documented)
- Natural language interface: Functional with LangGraph + Gemini AI
- Notifications: Telegram, Gmail, Sheets all functional
- Cloud deployment: GCP Compute Engine (Ubuntu 25.10, e2-small instance)

**Next Steps**:
1. Extended testnet performance validation (3+ months)
2. ML model improvement (replace RandomForest Regressor with LSTM for better extrapolation)
3. Strategy optimization based on backtest results
4. Production deployment (after successful testnet validation)

## Cloud Deployment Guide (GCP)

### Successful Deployment Summary

**Deployment Status:**

| Component | Status | Location |
|-----------|--------|----------|
| **VM** | ✅ Running | GCP us-central1-a |
| **Bot** | ✅ Active | tmux session |
| **Mode** | ✅ Chat | Natural language interface |
| **Data** | ✅ Loaded | 2,686 historical rows (2018-2025) |
| **APIs** | ✅ Connected | CoinGecko MCP, Fear & Greed Index |
| **Cost** | ✅ Free tier | Using $300 GCP credit |

**VM Specifications:**
- **Instance**: btc-trader-vm
- **Zone**: us-central1-a
- **Machine Type**: e2-small (2 vCPUs, 2 GB Memory)
- **OS**: Ubuntu 22.04 LTS (Minimal)
- **Disk**: 10 GB SSD
- **Networking**: HTTP/HTTPS traffic enabled
- **Cost**: ~$0.02/hour (~$15/month) from $300 free credit

---

### Step-by-Step GCP Deployment Guide

This guide shows how to deploy the bot to Google Cloud Platform using SSH and Linux commands.

#### Prerequisites

- GCP account with $300 free credit activated
- VM instance created (`btc-trader-vm`)
- GitHub repository: https://github.com/krishna11-dot/Bitcoin-Trading-Bot

---

#### Step 1: Connect to GCP VM via SSH

**In GCP Console (Browser):**

1. Go to: https://console.cloud.google.com/compute/instances
2. Find `btc-trader-vm`
3. Click **START** button (if stopped)
4. Click **SSH** button

**✅ Success:** Terminal opens with:
```
krishnanair041@btc-trader-vm:~$
```

---

#### Step 2: Update System and Install Dependencies

```bash
# Update package list
sudo apt update

# Upgrade existing packages
sudo apt upgrade -y

# Install Python 3.11, Git, and tools
sudo apt install python3.11 python3.11-venv python3-pip git nano -y

# Verify Python version
python3 --version  # Should show Python 3.10+ or 3.11+
```

**What this does:** Installs Python, Git, text editor, and system updates

---

#### Step 3: Clone GitHub Repository

```bash
# Navigate to home directory
cd ~

# Clone repository
git clone https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git

# Enter project directory
cd Bitcoin-Trading-Bot

# Verify files
ls -la
```

**✅ Success:** Shows `README.md`, `requirements.txt`, `src/`, `tests/`, etc.

---

#### Step 4: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install all dependencies (takes 2-3 minutes)
pip install -r requirements.txt
```

**✅ Success:** Prompt shows `(venv)` prefix

**What this does:** Creates isolated Python environment and installs all packages (pandas, numpy, langgraph, chromadb, google-generativeai, etc.)

---

#### Step 5: Upload Dataset to VM

**Option A: Upload via GCP Console (Recommended)**

1. In SSH window, click **⚙️ gear icon** → **Upload file**
2. Select: `C:\Users\krish\btc-intelligent-trader\data\raw\btc_daily_data_2018_to_2025.csv`
3. Wait for upload to complete

```bash
# Create data directories
mkdir -p data/raw data/processed data/rag_vectordb

# Move uploaded file to correct location
mv ~/btc_daily_data_2018_to_2025.csv data/raw/

# Verify file exists
ls -lh data/raw/btc_daily_data_2018_to_2025.csv
wc -l data/raw/btc_daily_data_2018_to_2025.csv  # Should show ~2686 rows
```

**Option B: Transfer via GitHub (If Upload Fails)**

**On Local Windows (PowerShell):**
```powershell
cd C:\Users\krish\btc-intelligent-trader

# Temporarily force-add CSV (overrides .gitignore)
git add -f data/raw/btc_daily_data_2018_to_2025.csv
git commit -m "Temporary: Add CSV for VM transfer"
git push origin main
```

**On VM (SSH):**
```bash
cd ~/Bitcoin-Trading-Bot
git pull origin main
ls -lh data/raw/btc_daily_data_2018_to_2025.csv
```

**Clean up (remove CSV from GitHub):**
```powershell
# On local Windows
git rm --cached data/raw/btc_daily_data_2018_to_2025.csv
git commit -m "Remove CSV from tracking"
git push origin main
```

---

#### Step 6: Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env file
nano .env
```

**In nano editor, add your actual API keys:**

**⚠️ SECURITY WARNING: NEVER commit real API keys to GitHub!**

- See `.env.example` file for the complete template
- Get your actual API keys from:
  - **Gemini AI**: https://aistudio.google.com/app/apikey
  - **Telegram Bot**: @BotFather on Telegram
  - **Telegram Chat ID**: @userinfobot on Telegram
  - **Gmail App Password**: https://myaccount.google.com/apppasswords

**The `.env` file stays on your local machine and VM only - it's in `.gitignore`**

**Save and exit:**
- Press `Ctrl + O` (save)
- Press `Enter` (confirm)
- Press `Ctrl + X` (exit)

```bash
# Secure .env file
chmod 600 .env

# Verify key is set
grep "GEMINI_API_KEY" .env | cut -c1-35
```

---

#### Step 7: Run Backtest (Verify Deployment)

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run backtest
python3 main.py --mode backtest
```

**⏱️ Takes:** 1-2 minutes

**✅ Success:** Shows backtest results:
```
=== BACKTEST RESULTS ===
DCA Strategy: -14.25% return (6-month period tested)
Swing Strategy: Results shown
Beat buy-and-hold by 5.8%
```

**What this does:** Tests bot on historical data to verify everything works

---

#### Step 8: Set Up 24/7 Background Execution (tmux)

```bash
# Install tmux
sudo apt install tmux -y

# Start new tmux session
tmux new -s trading-bot
```

**Inside tmux (new terminal appears):**

```bash
# Navigate to project
cd ~/Bitcoin-Trading-Bot

# Activate virtual environment
source venv/bin/activate

# Start chat mode
python3 main.py --mode chat
```

**✅ Success:** Shows:
```
🚀 Bitcoin Trading Assistant Started!
You:
```

**Detach from tmux (keep bot running in background):**
- Press `Ctrl + B`, then press `D`

**✅ Bot now runs 24/7 in background!**

---

#### Step 9: Manage Bot (Daily Operations)

**Check if bot is running:**
```bash
tmux ls  # Shows: trading-bot: 1 windows (created ...)
```

**View bot output:**
```bash
tmux attach -t trading-bot  # Press Ctrl+B, then D to detach again
```

**Stop bot:**
```bash
tmux kill-session -t trading-bot
```

**Restart bot:**
```bash
tmux new -s trading-bot
cd ~/Bitcoin-Trading-Bot
source venv/bin/activate
python3 main.py --mode chat
# Press Ctrl+B, then D
```

**Update code from GitHub:**
```bash
# Stop bot first
tmux kill-session -t trading-bot

# Pull latest changes
cd ~/Bitcoin-Trading-Bot
git pull origin main

# Reinstall dependencies (if requirements changed)
source venv/bin/activate
pip install -r requirements.txt

# Restart bot
tmux new -s trading-bot
# Inside tmux: python3 main.py --mode chat
```

---

#### Step 10: Monitor and Troubleshoot

**Check system resources:**
```bash
# CPU and memory usage
htop  # Press Q to exit

# Disk usage
df -h

# Check Python processes
ps aux | grep python3

# VM external IP
curl ifconfig.me
```

**Check logs:**
```bash
# View bot output (if running in tmux)
tmux attach -t trading-bot

# Check error logs
tail -f logs/trading_bot.log  # If log file exists
```

**Common issues:**
```bash
# Issue: ModuleNotFoundError
source venv/bin/activate
pip install -r requirements.txt

# Issue: GEMINI_API_KEY not set
nano .env  # Add your API key

# Issue: File not found
ls -la data/raw/  # Verify CSV exists
```

---

### Pushing Updates to GitHub (Manual)

**From Local Windows (PowerShell):**

```powershell
# Navigate to project
cd C:\Users\krish\btc-intelligent-trader

# Check status
git status

# Add all changes
git add .

# Commit with descriptive message
git commit -m "Update: [describe your changes]"

# Push to GitHub
git push origin main
```

**Security Checklist Before Pushing:**

```powershell
# Verify no sensitive data
Get-Content .gitignore | Select-String "\.env"  # Should show .env is ignored
Get-Content .env  # Make sure it's NOT staged

# Check what will be committed
git diff --cached

# If you accidentally added .env:
git reset .env
```

**Example: Update README**

```powershell
git add README.md
git commit -m "Update: Add ChromaDB explanation and GCP deployment guide"
git push origin main
```

**Author Configuration:**
```powershell
# Set your name and email (one-time setup)
git config user.name "Your Name"
git config user.email "your_email@gmail.com"

# Verify configuration
git config --list | Select-String "user"
```

**Replace with YOUR actual name and email**

---

### Deployment Cost Tracking

**GCP Free Tier:**
- $300 credit for 90 days
- e2-small instance: ~$0.02/hour (~$15/month)
- **Your $300 lasts:** ~20 months (but free trial is only 90 days)

**Monitor costs:**
1. Go to: https://console.cloud.google.com/billing
2. View **Cost breakdown** and **Forecasts**
3. Set **Budget alerts** to notify when spending reaches thresholds

**Stop VM when not needed:**
```bash
# In GCP Console → Compute Engine → VM Instances
# Click STOP button for btc-trader-vm
# Restarts: Click START, wait 30 seconds, then SSH
```

---

## Safety & Risk Management

This bot implements multiple layers of risk management:
- Position sizing based on portfolio value
- Maximum position limits
- Stop-loss and take-profit levels
- Rate limiting for API calls
- Comprehensive error handling
- Testnet validation before production

**Always test thoroughly on testnet before using real money.**

## Contributing

This is a personal trading bot project. See documentation for architecture details if you want to understand or extend the system.

## License

Private project. All rights reserved.

## Support & Documentation

For detailed guides on specific topics, see the [docs/](docs/) directory. Each document covers a specific aspect of the system:

- Setup and deployment guides
- Architecture and design decisions
- Feature documentation
- Integration guides
- Troubleshooting and FAQs

Start with [QUICKSTART.md](docs/QUICKSTART.md) if you're new to the project.

---

**Last Updated**: 2025-12-19
**Project Status**: Active Development & Cloud Deployed
**Recent Changes**: Added CryptoPanic News RAG system with tool orchestration architecture
**Deployment**:
- **Primary**: Google Cloud Platform (GCP) - Ubuntu 22.04 VM with tmux
- **Secondary**: Local Windows (Windows Service via NSSM)
**Trading**: Analysis & Backtesting (NOT live trading - research tool only)
**Repository**: https://github.com/krishna11-dot/Bitcoin-Trading-Bot
