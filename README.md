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
- **Predicts price direction** using RandomForest ML model (7-day forecasts)
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
                   (Binance API + RAG System)

  • Fetches real-time BTC price and market data (Binance API)
  • Retrieves historical patterns via RAG for context matching
    (RAG used for natural language pattern matching, NOT tabular data)
  • Manages rate limiting and API calls


                                 ↓


         ↓                       ↓                       ↓

    MODULE 1             MODULE 2             MODULE 3
   TECHNICAL            SENTIMENT            PREDICTION
   INDICATORS           ANALYSIS                (ML)

 • RSI                • Fear & Greed       • RandomForest
 • MACD                 Index              • 10 features
 • ATR                • Market             • 7-day window
 • SMA 50/200           sentiment          • Direction
                      • Confidence           (UP/DOWN)
                        multiplier         • Confidence




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
   - **CoinGecko MCP**: Optional live prices for chat mode (FREE Demo tier: 30 calls/min)
   - **CSV Historical Data**: Backtesting and technical indicators
   - **RAG System**: Historical pattern matching for natural language context

   **Data Source Selection**:
   - Chat mode: MCP (live) → CSV fallback
   - Backtest mode: CSV only (no MCP for historical consistency)

   **RAG Usage Note**: Used for natural language pattern matching (e.g., "similar market conditions"), NOT for extracting tabular data.
   For tabular data, use SQL or Pandas (simpler, more efficient). RAG is powerful but should be used where its complexity is justified.

2. **Module 1** calculates technical indicators (RSI, MACD, ATR, SMA 50/200)

3. **Module 2** analyzes market sentiment using Fear & Greed Index

4. **Module 3** uses RandomForest ML model with 10 essential features to predict price direction and confidence
   - Can engineer 24 features total, but uses 10 for prediction (simpler, less overfitting)
   - Features: volatility (2), trend (2), momentum (2), volume (1), market structure (2), moving average (1)
   - Predicts 7 days ahead using 7-day rolling window
   - Note: ML is ONE signal - Decision Box combines ML + technical indicators + sentiment for reliability

5. **Decision Box** combines all signals to make trading decisions (DCA, Swing, Stop-Loss, Take-Profit)

6. **Execution** executes trades on Binance Testnet

7. **Notifications** sends alerts via Telegram, Gmail, and logs to Google Sheets

#### Natural Language Interface (Mode: chat)

**Single-Agent LangGraph Architecture with Three Data Sources:**

```
User Question: "What's today's Bitcoin price?"
       ↓
1. Understand Node (Gemini LLM) → Interprets intent: "check_market"
       ↓
2. Validate Node (Guardrails) → Validates intent is safe (not malicious)
       ↓
3. Execute Node → Fetches data from THREE sources:
       ├─→ MCP (CoinGecko API): Live BTC price ($89,083 as of Dec 7, 2025)
       ├─→ CSV Historical Data: Technical indicators (RSI, MACD, ATR)
       └─→ RAG System: Similar historical patterns (ChromaDB vector search)
       ↓
       Combines all three sources into structured data
       ↓
4. Respond Node (Gemini LLM) → Formats as natural language:
   "BTC is $89,083 (live from CoinGecko). RSI is 29.2 (oversold).
    Last time RSI was this low (Jan 2023), BTC rallied +15%."
```

**Data Source Details:**

1. **MCP (Model Context Protocol)**: Live price from CoinGecko API
   - Used for: Current BTC price in chat mode
   - Fallback: CSV if API unavailable
   - NOT used in backtest mode (historical consistency)

2. **CSV Historical Data**: 2018-2025 Bitcoin price history
   - Used for: Technical indicators (RSI, MACD, ATR)
   - Always loaded in background
   - Primary source for backtesting

3. **RAG (Retrieval-Augmented Generation)**: ChromaDB vector database
   - Used for: Natural language pattern matching
   - Example: "Find similar market conditions to today"
   - NOT for extracting CSV data (use Pandas for that)
   - Returns: Similar historical scenarios with outcomes

   **ChromaDB vs FAISS - Understanding the Technology Stack:**

   ```
   Your Bot
       ↓
   ChromaDB (User-friendly vector database interface)
       ↓
   FAISS (Fast similarity search engine - used internally by ChromaDB)
       ↓
   Vector Similarity Search Results
   ```

   **What's Actually Being Used:**
   - **ChromaDB**: Vector database you interact with (like Google Drive - easy interface)
   - **FAISS**: Search algorithm ChromaDB uses internally (like hard drive - actual mechanism)
   - **You use ChromaDB API, never touch FAISS directly**

   **How RAG Works - Example Flow:**

   1. **Bot Creates Historical Pattern (During Backtest):**
      ```
      Date: 2024-03-15
      Price: $70,000
      RSI: 45
      Fear & Greed: 32
      Narrative: "Bitcoin consolidated near resistance with neutral RSI and fear sentiment"
      ```

   2. **ChromaDB Stores Pattern:**
      - Converts narrative to vector embedding (numerical representation)
      - Stores in database with metadata (date, price, RSI, Fear & Greed)
      - Uses FAISS internally for fast vector indexing

   3. **When You Ask a Question:**
      ```
      You: "What happened last time BTC was near $100K with neutral RSI?"
      ```

   4. **ChromaDB Searches:**
      - Converts your question to vector using Sentence Transformers
      - FAISS finds similar historical patterns (fast vector similarity search)
      - Returns top 3 most similar market conditions

   5. **Bot Responds with Historical Context:**
      ```
      "In March 2024, when BTC consolidated near $70K with neutral RSI (45),
       the price broke resistance 2 weeks later and rallied +15%."
      ```

   **ChromaDB vs Direct CSV Access:**

   | Task | Tool Used | Why |
   |------|-----------|-----|
   | "Show me price on Jan 1, 2024" | Pandas (CSV) | Structured data lookup |
   | "Find similar market conditions" | ChromaDB (RAG) | Pattern matching with natural language |
   | "Calculate average RSI" | Pandas (CSV) | Mathematical aggregation |
   | "What happened when fear was this low?" | ChromaDB (RAG) | Semantic similarity search |

   **Without ChromaDB (Manual Search - Slow & Imprecise):**
   ```python
   for row in csv:
       if row['rsi'] == 45 and row['price'] > 95000:
           print(row)
   # Problems: Must match exact values, no "similarity" concept
   ```

   **With ChromaDB (Semantic Search - Fast & Intelligent):**
   ```python
   rag.find_similar_patterns(
       query="BTC consolidating with low volatility",
       top_k=3
   )
   # Benefits: Finds "similar" patterns, understands natural language, fast vector search
   ```

   **Technology Stack:**
   ```
   Your Question: "Find similar market conditions"
       ↓
   Sentence Transformer (converts text → 384-dim vector)
       ↓
   ChromaDB API (vector database interface)
       ↓
   FAISS (cosine similarity search - finds nearest neighbors)
       ↓
   Returns: Top 3 similar historical patterns with similarity scores
       ↓
   Gemini LLM uses context to generate natural language answer
   ```

   **Populating RAG Database:**
   ```bash
   # Build RAG index from historical data (stores 2,685+ patterns)
   python3 main.py --mode backtest --rebuild-rag

   # Check patterns stored
   ls -la data/rag_vectordb/
   ```

4. **Backtest JSON** (optional): `data/processed/backtest_results.json`
   - Used for: Portfolio metrics, past performance
   - Accessed when user asks about "my portfolio" or "backtest results"
   - Contains: Total return, Sharpe ratio, win rate, etc.

**Why LangGraph?**
- Industry-standard agent framework (resume value)
- Clean state machine architecture (each node has one responsibility)
- State management built-in (shared state flows through nodes)
- Learning experience with modern agentic frameworks

**Safety:**
- LLM used ONLY for understanding questions and formatting responses
- Trading decisions made by Decision Box (NOT by LLM)
- Guardrails are hard-coded (not prompt-based)
- Natural language layer sits ABOVE existing system (no modifications)

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

### Machine Learning
- **RandomForest Model**: Predicts BTC price direction 7 days ahead (UP/DOWN)
- **Feature Engineering**: 24 features created, 10 essential features used for prediction
- **7-Day Rolling Window**: Uses 7 days of historical patterns to predict future direction
- **Model Training**: Pre-trained on all available historical data
- **Prediction Confidence**: Provides confidence score (0-1) for each prediction
- **Extrapolation Awareness**: ML is ONE signal combined with technical indicators (not sole decision maker)
- **Known Limitation**: RandomForest cannot extrapolate beyond training data range (49.7% direction accuracy when prices exceed training range). Strategy still profitable due to defensive DCA and stop-loss strategies. See [ML Model Limitations](docs/ML_MODEL_LIMITATIONS.md) for details.

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
- **RAG System**: Historical data retrieval for context-aware decisions
- **Real-time Data**: Live price feeds and market indicators
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
    rag/                      # RAG system for historical data
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
- **scikit-learn RandomForest**: Direction prediction (UP/DOWN classification)
- **Feature Engineering**: 24 features → 10 essential features for prediction

### Trading & Data
- **Binance API (CCXT)**: Market data and trade execution
- **RAG (ChromaDB + Sentence Transformers)**: Historical data retrieval and pattern matching

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
- GitHub repository: https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System

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
git clone https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System.git

# Enter project directory
cd Bitcoin-Trading-Bot-System

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
cd ~/Bitcoin-Trading-Bot-System
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
cd ~/Bitcoin-Trading-Bot-System

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
cd ~/Bitcoin-Trading-Bot-System
source venv/bin/activate
python3 main.py --mode chat
# Press Ctrl+B, then D
```

**Update code from GitHub:**
```bash
# Stop bot first
tmux kill-session -t trading-bot

# Pull latest changes
cd ~/Bitcoin-Trading-Bot-System
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

**Last Updated**: 2025-12-08
**Project Status**: Active Development & Cloud Deployed
**Deployment**:
- **Primary**: Google Cloud Platform (GCP) - Ubuntu 22.04 VM with tmux
- **Secondary**: Local Windows (Windows Service via NSSM)
**Trading**: Analysis & Backtesting (NOT live trading - research tool only)
**Repository**: https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System
