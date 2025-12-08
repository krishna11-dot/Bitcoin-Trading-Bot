# BTC INTELLIGENT TRADER - ARCHITECTURE GUIDE

##  QUICK SUMMARY

Your system has **3 MODULES** → **1 DECISION BOX** → **5 STRATEGIES** → **TRADES**

```
Module 1 (Technical) → RSI, ATR, MACD
Module 2 (Sentiment) → Fear & Greed Index
Module 3 (Prediction) → ML Price Forecast
         ↓
    DECISION BOX (The Brain)
         ↓
Strategy 1: Circuit Breaker (Emergency)
Strategy 2: ATR Stop-Loss (Risk limit)
Strategy 3: Take Profit (Lock gains)
Strategy 4: Swing Trading (Big moves)
Strategy 5: DCA (Steady buying)
         ↓
    BUY/SELL/HOLD/PAUSE
```

---

##  FOLDER STRUCTURE

### **Root Files (Entry Points)**

| File | Purpose | When to Use |
|------|---------|-------------|
| **main.py** | Main entry point | `python main.py --mode backtest` |
| **live_trader.py** | Live paper trading | `python live_trader.py --interval 60` |
| **test_strategies.py** | Test 5 strategies work | `python test_strategies.py` |
| **test_api_keys.py** | Verify Binance API | `python test_api_keys.py` |

### **data/ Folder - Historical Data**

```
data/
 raw/
    Bitcoin_Historical_Data.csv     # INPUT: Raw price data (1771 days)

 processed/
    bitcoin_clean.csv               # PROCESSED: Clean data (used by all modules)
    fear_greed_historical.csv       # CACHED: F&G Index (2000 days)
    blockchain_metrics.csv          # CACHED: On-chain data (refreshed weekly)
    backtest_trades.csv             # OUTPUT: Trade log from backtests

 rag_vectordb/
     faiss_index.bin                 # RAG: Pattern matching index
     historical_data.pkl             # RAG: Historical indicators
```

**What it does:**
- Stores historical BTC price data
- Caches API responses to avoid repeated calls
- Saves backtest results

### **src/ Folder - Core Trading Engine**

```
src/
 data_pipeline/          # Data loading & API calls
 modules/                # 3 analysis modules (Technical, Sentiment, Prediction)
 decision_box/           # THE BRAIN - Trading strategies
 execution/              # Order placement (Binance API)
 backtesting/            # Historical testing framework
```

---

##  THE DECISION BOX (The Brain)

**File:** `src/decision_box/trading_logic.py` (562 lines)

### What It Does

The Decision Box is **THE CORE BRAIN** that takes data from 3 modules and decides: BUY, SELL, HOLD, or PAUSE.

### How It Works

```python
# INPUT
technical = {RSI: 35, ATR: 2000, MACD: -500}      # From Module 1
sentiment = {fear_greed: 25, rag_confidence: 0.0}  # From Module 2
prediction = {price: 107000, confidence: 0.65}     # From Module 3

# DECISION BOX EVALUATES 5 STRATEGIES (in priority order)
decision = decision_box.make_decision(technical, sentiment, prediction, current_price=105000)

# OUTPUT
{
    'action': 'BUY',
    'amount': 500,
    'strategy': 'DCA',
    'reason': 'DCA: RSI 35, F&G 25 (Fear < 40)'
}
```

### The 5 Strategies (Priority Order)

**1. CIRCUIT BREAKER (Highest Priority)** 
- **Location:** `trading_logic.py` lines 179-211
- **Purpose:** Emergency stop during severe losses
- **Trigger:** Portfolio < 75% of initial capital (25% drawdown)
- **Action:** PAUSE all trading
- **Example:** Start $10k → Drop to $7.4k → CIRCUIT BREAKER activates

**2. ATR STOP-LOSS** 
- **Location:** `trading_logic.py` lines 213-254
- **Purpose:** Limit losses on individual trades
- **Formula:** `Stop = Entry Price - (2.0 × ATR)`
- **Trigger:** Current price < Stop price
- **Action:** SELL all BTC
- **Example:** Entry $105k, ATR $1.5k → Stop $102k → Price $101.5k → SELL

**3. TAKE PROFIT** 
- **Location:** `trading_logic.py` lines 256-327
- **Purpose:** Lock in gains before reversal
- **Trigger:** Portfolio +15% AND RSI > 65
- **Action:** SELL all BTC
- **Example:** Start $10k → Grow to $11.5k (+15%), RSI 67 → SELL

**4. SWING TRADING** 
- **Location:** `trading_logic.py` lines 329-374
- **Purpose:** Capture large opportunistic moves
- **Trigger (ALL must be true):**
  - RSI < 30 (extreme oversold)
  - MACD > 0 (bullish momentum)
  - Predicted +3% move
  - ML confidence > 70%
- **Action:** BUY $500
- **Example:** RSI 28, MACD +250, ML predicts +3.3% with 75% confidence → BUY

**5. DCA (Dollar-Cost Averaging)** - **Location:** `trading_logic.py` lines 376-428
- **Purpose:** Steady accumulation during favorable conditions
- **Trigger (ANY):**
  - RSI < 60 (oversold)
  - Fear & Greed < 40 (market fear)
- **Action:** BUY $500
- **Example:** RSI 55, F&G 25 → BUY $500

---

##  THE 3 MODULES

### **MODULE 1: TECHNICAL INDICATORS**

**File:** `src/modules/module1_technical.py` (417 lines)

**What It Does:** Analyzes price momentum, volatility, and trend

**Function:** `calculate_indicators(df, current_date)`

**Inputs:**
- DataFrame with Date and Price columns
- Current date (YYYY-MM-DD)

**Outputs:**
```python
{
    'RSI': 37.30,           # 0-100 (oversold <30, overbought >70)
    'ATR': 2003.19,         # Volatility in dollars
    'MACD': 1234.56,        # Trend indicator
    'MACD_signal': 3355.70,
    'MACD_diff': -2121.14,  # >0 bullish, <0 bearish
    'SMA_50': 104523.45,    # 50-day average
    'SMA_200': 95678.23     # 200-day average
}
```

**Purpose:** Identify when to buy (oversold) and sell (overbought)

**Success Criteria:** All indicators in valid ranges, no future data

---

### **MODULE 2: SENTIMENT ANALYSIS**

**File:** `src/modules/module2_sentiment.py` (472 lines)

**What It Does:** Analyzes market sentiment and historical patterns

**Components:**
1. **Fear & Greed Index** (live API)
   - Source: Alternative.me API
   - Range: 0-100 (0=Extreme Fear, 100=Extreme Greed)
   - Strategy: Buy at <40, avoid >75

2. **RAG (Pattern Matching)**
   - Uses FAISS vector database
   - Finds similar past market conditions
   - Returns confidence of bullish outcome

**Inputs:**
- DataFrame with technical indicators
- Current date

**Outputs:**
```python
{
    'fear_greed_score': 14,    # 0-100 from API
    'rag_confidence': 0.0,     # 0-1 (pattern match strength)
    'signal': 'BUY'/'SELL'/'HOLD'
}
```

**Purpose:** Add market psychology to technical signals

**Success Criteria:** F&G API working, RAG >0.7 confidence

---

### **MODULE 3: PRICE PREDICTION (ML)**

**File:** `src/modules/module3_prediction.py` (1365 lines) - LARGEST MODULE

**What It Does:** Forecasts BTC price 7 days ahead using machine learning

**Dual Model Approach:**
1. **Linear Regression** → Predicts price magnitude ($106,234.56)
2. **Random Forest Classifier** → Predicts direction (UP/DOWN)

**13 Engineered Features:**
- Volatility (2): rolling_std, high_low_range
- Trend (2): price_change_pct, sma_ratio
- Momentum (2): roc_7d, momentum_oscillator
- Volume (2): volume_spike, volume_trend
- Blockchain (3): hash_rate, mempool_size, block_size
- Structure (2): higher_highs, lower_lows

**Inputs:**
- Historical price DataFrame
- Technical indicators
- Blockchain data (from blockchain.info API)

**Outputs:**
```python
{
    'predicted_price': 106234.56,      # 7-day ahead price
    'direction': 'UP',                 # UP or DOWN
    'direction_confidence': 0.68       # 0-1 probability
}
```

**Purpose:** Predict future price to time entries/exits

**Success Criteria:** MAPE <8%, Direction accuracy >65%

---

## DATA FLOW (How Everything Connects)

### **Backtesting Flow**

```
1. Load CSV
   data/raw/Bitcoin_Historical_Data.csv
   ↓
2. Clean Data
   BitcoinDataLoader → bitcoin_clean.csv
   ↓
3. For each day in backtest period:

   a) Module 1 (Technical)
      Input: Price history up to current date
      Output: RSI, ATR, MACD

   b) Module 2 (Sentiment)
      Input: Technical indicators + historical F&G
      Output: fear_greed_score, rag_confidence

   c) Module 3 (Prediction)
      Input: Price history + blockchain data
      Output: predicted_price, direction_confidence

   d) Decision Box
      Input: All 3 module outputs
      Output: BUY/SELL/HOLD decision

   e) Execute Trade (simulated)
      Update portfolio (cash, BTC holdings)

   f) Track Metrics
      Total return, Sharpe ratio, drawdown, win rate
   ↓
4. Generate Report
   Print results + save trades to backtest_trades.csv
```

### **Live Trading Flow**

```
1. Initialization (once)
   - Load historical CSV
   - Pre-load 200 days of price history
   - Train ML models
   - Build RAG index
   ↓
2. Trading Cycle (every 5 minutes)

   Step 1: Fetch Live Data
   - Binance API → Current BTC price
   - Alternative.me → Fear & Greed score
   - Binance API → Portfolio balance

   Step 2: Calculate Indicators
   - Update price history (rolling 200 prices)
   - Module 1 → RSI, ATR, MACD

   Step 3: Analyze Sentiment
   - Module 2 → fear_greed_score
   - RAG disabled (live mode)

   Step 4: Make Prediction
   - Module 3 → predicted_price, confidence

   Step 5: Get Decision
   - Decision Box → BUY/SELL/HOLD/PAUSE

   Step 6: Execute Trade
   - If BUY: POST order to Binance Testnet
   - If SELL: POST order to Binance Testnet
   - If HOLD: No action

   Step 7: Update Performance
   - Calculate return, drawdown
   - Print metrics
   ↓
3. Sleep 300 seconds → Repeat from Step 2
```

---

##  WHERE ARE THE 5 STRATEGIES?

**ALL 5 STRATEGIES ARE IN ONE FILE:**

**`src/decision_box/trading_logic.py`**

| Strategy | Method Name | Lines |
|----------|-------------|-------|
| Circuit Breaker | `_check_circuit_breaker()` | 179-211 |
| ATR Stop-Loss | `_check_stop_loss()` | 213-254 |
| Take Profit | `_check_take_profit()` | 256-327 |
| Swing Trading | `_check_swing_entry()` | 329-374 |
| DCA | `_check_dca_conditions()` | 376-428 |

**Main Decision Method:** `make_decision()` (lines 88-177)

**How They're Evaluated:**
```python
def make_decision(self, technical, sentiment, prediction, current_price):
    # Priority 1: Circuit Breaker (highest priority)
    decision = self._check_circuit_breaker(current_price)
    if decision: return decision

    # If holding BTC, check exit strategies
    if self.portfolio['btc'] > 0:
        # Priority 2: Stop-Loss
        decision = self._check_stop_loss(current_price, technical['ATR'])
        if decision: return decision

        # Priority 3: Take Profit
        decision = self._check_take_profit(current_price, technical['RSI'], ...)
        if decision: return decision

    # Entry strategies (if cash available)
    # Priority 4: Swing Trading
    decision = self._check_swing_entry(technical['RSI'], ...)
    if decision: return decision

    # Priority 5: DCA
    decision = self._check_dca_conditions(current_price, technical['RSI'], ...)
    if decision: return decision

    # Default: HOLD
    return {'action': 'HOLD', 'reason': 'No conditions met'}
```

---

##  PURPOSE & SUCCESS CRITERIA

### **System Purpose**
Test if algorithmic trading strategies can beat buy-and-hold by combining:
- Technical analysis (RSI, ATR, MACD)
- Sentiment analysis (Fear & Greed)
- Machine learning price predictions

### **Success Criteria (6-Month Backtest)**

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Total Return | >15% | 13.88% | [WARNING]Close (1.1% short) |
| Sharpe Ratio | >1.0 | 1.13 | PASSED |
| Max Drawdown | <25% | -10.21% | PASSED |
| Win Rate | >55% | 75.0% | PASSED (Exceptional!) |

**Current Performance:** Beat buy-and-hold by +13.3% 

---

##  CONFIGURATION (.env)

```ini
# API Keys (from Binance Testnet)
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here

# Trading Parameters
INITIAL_CAPITAL=10000      # Starting cash
DCA_AMOUNT=500             # DCA buy size
SWING_AMOUNT=500           # Swing buy size
RSI_OVERSOLD=60            # DCA trigger (RSI < 60)
K_ATR=2.0                  # Stop-loss multiplier
FEAR_THRESHOLD=40          # DCA trigger (F&G < 40)
```

---

## HOW TO RUN

### **Backtest (Historical Testing)**
```bash
python main.py --mode backtest --months 6
```
**Output:** Trade log, metrics, comparison to buy-and-hold

### **Live Paper Trading (Testnet)**
```bash
python main.py --mode live
```
**Output:** Real-time trading with virtual funds (5-min cycles)

### **Test API Connections**
```bash
python test_api_keys.py
```
**Output:** Verifies Binance + Fear & Greed APIs work

### **Test Individual Strategies**
```bash
python test_strategies.py
```
**Output:** Unit tests for all 5 strategies

---

## QUICK REFERENCE

### **File Sizes**
- Module 1 (Technical): 417 lines
- Module 2 (Sentiment): 472 lines
- Module 3 (Prediction): 1365 lines (largest)
- Decision Box: 562 lines
- Backtest Engine: 693 lines
- **Total Core Code: ~4,100 lines**

### **Key Classes**
1. `BitcoinDataLoader` - CSV cleaning
2. `APIClient` - Binance/F&G/Blockchain APIs
3. `SentimentAnalyzer` - Fear & Greed + RAG
4. `BitcoinPricePredictor` - ML forecasting
5. `TradingDecisionBox` - 5 strategies (THE BRAIN)
6. `BinanceExecutor` - Order placement
7. `BacktestEngine` - Historical validation

### **Data Files**
- Input: `Bitcoin_Historical_Data.csv` (1771 days)
- Processed: `bitcoin_clean.csv`
- Output: `backtest_trades.csv`
- Cache: `fear_greed_historical.csv`, `blockchain_metrics.csv`

---

## KEY INSIGHTS

1. **Decision Box = The Brain**
   - Takes 3 module inputs
   - Evaluates 5 strategies in priority order
   - Returns single decision (BUY/SELL/HOLD/PAUSE)

2. **3 Modules = Data Analysis**
   - Module 1: Technical (RSI, ATR, MACD)
   - Module 2: Sentiment (F&G Index, RAG)
   - Module 3: Prediction (ML price forecast)

3. **5 Strategies = Trading Logic**
   - Circuit Breaker (emergency)
   - Stop-Loss (risk limit)
   - Take Profit (exit)
   - Swing (opportunistic)
   - DCA (steady buying)

4. **All in One File**
   - All 5 strategies in `trading_logic.py`
   - Single file = easy to understand/modify

5. **Anti-Future-Data**
   - No lookahead bias
   - Only uses data up to current date
   - Realistic backtest results

---

##  COMMON QUESTIONS

**Q: What's the difference between backtesting and live trading?**
A: Backtesting tests on historical data (fast), live trading uses real-time data (slow, 5-min cycles).

**Q: Where are the trading strategies?**
A: All 5 in `src/decision_box/trading_logic.py`

**Q: What does the Decision Box do?**
A: It's the brain - takes module outputs, evaluates 5 strategies, returns BUY/SELL/HOLD.

**Q: What are the 3 modules?**
A:
- Module 1: Technical indicators (RSI, ATR, MACD)
- Module 2: Sentiment (Fear & Greed, RAG)
- Module 3: ML price prediction

**Q: How does data flow?**
A: CSV → Modules 1/2/3 → Decision Box → Strategies → BUY/SELL/HOLD

**Q: Is this live trading with real money?**
A: NO! Binance Testnet = virtual funds (paper trading).

**Q: Why is backtesting working but live trading broken?**
A: CSV data ends Nov 5, but today is Nov 22. Live needs current data.

---

##  LEARNING PATH

**To understand the system:**

1. **Start here:** This file (ARCHITECTURE_GUIDE.md)
2. **Read:** `src/decision_box/trading_logic.py` (see 5 strategies)
3. **Run:** `python main.py --mode backtest --months 3` (see it work)
4. **Modify:** Change DCA_AMOUNT in .env, re-run backtest
5. **Test:** `python test_strategies.py` (unit tests)

**To add a new strategy:**
1. Open `src/decision_box/trading_logic.py`
2. Add new method like `_check_my_strategy()`
3. Call it in `make_decision()` at desired priority
4. Test with `test_strategies.py`

---

## SUMMARY

Your BTC Intelligent Trader system:
- **3 Modules** analyze market data
- **1 Decision Box** implements 5 trading strategies
- **Backtesting** validates on historical data (13.88% return!)
- **Live Trading** runs on Binance Testnet (paper money)
- **~4,100 lines** of core trading logic
- **75% win rate** (exceptional performance!)

All strategies are in one file: `src/decision_box/trading_logic.py`

Now you understand the COMPLETE architecture! 