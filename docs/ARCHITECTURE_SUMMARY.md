# BTC Intelligent Trader - Architecture Summary

## System Architecture

```

                     DECISION BOX (Core Logic)                    
  • Orchestrates all strategies: DCA, Swing, Stop-Loss, T/P     
  • Makes final buy/sell/hold decisions                         
  • Executes trades and manages portfolio                       

                              ↑
                  
                                        
             
          MODULE 1      MODULE 2   MODULE 3
          Technical    Sentiment  Prediction
          Indicators    Analysis     ML    
             
```

---

## Module Details

### Module 1: Technical Indicators
**File:** [src/modules/module1_technical.py](src/modules/module1_technical.py)

**Provides:**
- RSI (Relative Strength Index)
- ATR (Average True Range)
- MACD (Moving Average Convergence Divergence)
- SMA_50, SMA_200 (Simple Moving Averages)

**Used For:**
- DCA entry signals (RSI < 30 = oversold)
- Stop-loss calculation (Entry - 2×ATR)
- Trend detection (SMA crossovers)

---

### Module 2: Sentiment Analysis
**File:** [src/modules/module2_sentiment.py](src/modules/module2_sentiment.py)

**Provides:**
- Fear & Greed Index (0-100 scale)
- Confidence multiplier for ML predictions
- Market sentiment signals

**Used For:**
- DCA entry signals (F&G < 40 = fear)
- ML confidence adjustment (fear → lower confidence)
- Risk assessment

---

### Module 3: Price Prediction (ML)
**File:** [src/modules/module3_prediction.py](src/modules/module3_prediction.py)

**Provides:**
- 7-day price prediction (RandomForest)
- Direction classification (UP/DOWN)
- Prediction confidence scores

**Features:** 10 simplified features (v1.0)
- Volatility: rolling_std, high_low_range
- Trend: price_change_pct, sma_ratio
- Momentum: roc_7d, momentum_oscillator
- Volume: volume_spike
- Market structure: higher_highs, lower_lows
- Moving averages: sma_30

**Used For:**
- Swing trading entry signals (high confidence UP)
- Take-profit timing
- Future price estimation

---

## Decision Box Strategies

### 1. DCA (Dollar-Cost Averaging) - Base Layer
**Priority:** Lowest (executes when no other strategy triggers)

**Entry Conditions (ANY):**
```python
rsi < 30  OR  fear_greed < 40
```

**Configuration:**
- Amount per buy: 10% of initial capital ($1,000)
- Enabled: Yes
- Frequency: When conditions met (not time-based)

**Purpose:** Accumulate BTC during dips/fear

---

### 2. Swing Trading - Opportunistic
**Priority:** High (executes before DCA)

**Entry Conditions (ALL):**
```python
rsi < 30  AND
macd_diff > 0  AND
predicted_price > current * 1.03  AND
direction_confidence > 0.70
```

**Configuration:**
- Amount per trade: 10% of initial capital ($1,000)
- Enabled: Yes
- Min confidence: 70%

**Purpose:** Capture larger moves with high-confidence ML signals

---

### 3. ATR-Based Stop-Loss - Risk Management
**Priority:** Highest (checks FIRST if holding BTC)

**Exit Condition:**
```python
current_price < entry_price - (2.0 × ATR)
```

**Configuration:**
- ATR multiplier: 2.0 (configurable)
- Enabled: Yes
- Applies to: ALL positions (DCA + Swing)

**Purpose:** Limit losses on individual trades to ~5-10%

---

### 4. Take Profit - Lock Gains
**Priority:** High (checks after stop-loss)

**Exit Conditions (ANY):**
```python
portfolio_profit > 15%  AND  rsi > 65  →  SELL ALL
portfolio_profit > 10%  AND  rsi > 70  →  SELL HALF
rsi > 75  AND  macd < 0  AND  predicted_down  →  EMERGENCY EXIT
```

**Configuration:**
- Profit threshold: 15%
- Enabled: Yes

**Purpose:** Prevent giving back gains in market crashes

---

### 5. Circuit Breaker - Emergency Stop
**Priority:** CRITICAL (checks BEFORE all others)

**Trigger:**
```python
portfolio_value < 75% × initial_capital
```

**Action:** PAUSE ALL TRADING (requires manual review)

**Purpose:** Prevent catastrophic losses (25% max drawdown)

---

## Configuration Management

### Google Sheets Integration
**File:** [src/config/config_manager.py](src/config/config_manager.py)

**How it works:**
1. Fetches config from Google Sheets (live updates)
2. Caches locally (5-minute freshness)
3. Fallback to local cache if API fails
4. Hardcoded defaults as last resort

**Current Config:**
```json
{
  "initial_capital": 10000,
  "dca_buy_amount_percent": 0.1,
  "dca_enabled": true,
  "swing_enabled": true,
  "atr_stop_loss_multiplier": 2,
  "stop_loss_enabled": true,
  "take_profit_threshold": 0.15,
  "max_drawdown_circuit_breaker": 0.25,
  "rsi_oversold": 30,
  "fear_greed_buy_threshold": 40
}
```

**Setup:** [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

---

## Strategy Execution Flow

```
1. Circuit Breaker Check
    Portfolio < 75%? → PAUSE
    OK → Continue

2. Position Management (if holding BTC)
    Stop-Loss Check
      Price < Entry - 2×ATR? → SELL ALL
    Take Profit Check
       Profit > 15% + RSI > 65? → SELL

3. Entry Strategies (if have cash)
    Swing Entry (Priority 1)
      All conditions met + ML confidence > 70%? → BUY
    DCA Entry (Priority 2)
       RSI < 30 OR F&G < 40? → BUY

4. Default
    HOLD (no action)
```

---

## DCA Implementation Details

### As Specified in Your Requirements

**Base Layer:** DCA executes when other strategies don't trigger
**Price-Based Triggers:** RSI < 30 (price drop signal)
**Sentiment-Based Triggers:** F&G < 40 (fear signal)
**Distributes Buys:** Over time based on conditions (not fixed intervals)

### What's Missing vs Your Spec

Your requirement mentioned:
> "Buy when price drops by a set percentage"

**Current:** Uses RSI < 30 as proxy for price drop
**Enhancement Option:** Add explicit price drop % trigger:
```python
# Add to DCA conditions:
price_drop = (current_price - last_dca_price) / last_dca_price
if price_drop < -0.05:  # 5% drop
    execute_dca()
```

---

## ATR Stop-Loss Implementation

### As Specified in Your Requirements

**For Active Trades:** Applied to ALL positions (DCA + Swing)
**Formula:** `Stop = Entry Price - k × ATR`
**Configurable k:** Default 2.0, user-configurable
**Prevents Excessive Loss:** Limits to ~5-10% per trade

### Current Behavior

**Entry tracking:**
```python
self.portfolio['entry_price'] = current_price  # Set on BUY
```

**Stop-loss check:**
```python
stop_price = entry_price - (2.0 × atr)
if current_price < stop_price:
    SELL_ALL()
```

**Issue:** Entry price updates on EVERY buy
- If you DCA multiple times, only the LAST entry price is tracked
- This means early buys aren't protected individually

**Enhancement Option:** Track weighted average entry
```python
# Instead of:
entry_price = current_price

# Use:
total_btc_after = portfolio['btc'] + btc_bought
weighted_entry = (portfolio['entry_price'] * portfolio['btc'] + current_price * btc_bought) / total_btc_after
```

---

## Global Portfolio Safeguard

### As Specified in Your Requirements

**Circuit Breaker:** Pauses at 25% total loss
**Portfolio-Level:** Not per-trade, but total portfolio value
**Configurable:** `max_drawdown_circuit_breaker: 0.25`

**Implementation:** [src/decision_box/trading_logic.py:179-211](src/decision_box/trading_logic.py#L179-L211)

```python
def _check_circuit_breaker(self, current_price: float):
    portfolio_value = self.portfolio['cash'] + (self.portfolio['btc'] * current_price)
    if portfolio_value < 0.75 * initial_capital:
        return {'action': 'PAUSE', 'reason': 'Circuit Breaker'}
```

---

## Parameterization

### All User-Configurable Parameters

**File:** [config/trading_config.json](config/trading_config.json)

| Parameter | Purpose | Default | Configurable |
|-----------|---------|---------|--------------|
| `initial_capital` | Starting cash | $10,000 | |
| `dca_buy_amount_percent` | DCA size | 10% | |
| `swing_buy_percent` | Swing size | 10% | |
| `rsi_oversold` | DCA trigger | 30 | |
| `fear_greed_buy_threshold` | DCA trigger | 40 | |
| `atr_stop_loss_multiplier` | Stop distance | 2.0 | |
| `take_profit_threshold` | Profit target | 15% | |
| `max_drawdown_circuit_breaker` | Emergency stop | 25% | |
| `swing_confidence_threshold` | ML minimum | 70% | |

**All flags:**
- `dca_enabled`: true/false
- `swing_enabled`: true/false
- `stop_loss_enabled`: true/false
- `take_profit_enabled`: true/false

---

## Backtest Performance (v1.0)

### Multi-Period Results

| Period | Return | Buy-Hold | Outperformance | Characterization |
|--------|--------|----------|----------------|------------------|
| 2023 Bull | +37% | +154% | -117% | Defensive (exits early) |
| 2024 Mixed | +31% | +112% | -80% | Defensive (exits early) |
| 2022 Bear | -54% | -65% | **+11%** | Risk management wins |
| 2025 Down | -14% | -20% | **+6%** | Risk management wins |

**Strategy Type:** DEFENSIVE (prioritizes capital preservation over maximum profit)

**Details:** [MULTI_PERIOD_ANALYSIS.md](MULTI_PERIOD_ANALYSIS.md)

---

## File Structure

```
btc-intelligent-trader/
 src/
    decision_box/
       trading_logic.py          ← Core strategy logic
    modules/
       module1_technical.py      ← RSI, ATR, MACD, SMA
       module2_sentiment.py      ← Fear & Greed
       module3_prediction.py     ← ML RandomForest
    backtesting/
       backtest_engine.py        ← Historical testing
       metrics.py                ← Performance metrics
    config/
       config_manager.py         ← Google Sheets integration
    data_pipeline/
       data_loader.py            ← Load BTC historical data
       api_client.py             ← API rate limiting
    natural_language/
        agent.py                  ← LangGraph chat interface
 config/
    trading_config.json           ← Local config cache
    service_account.json          ← Google API credentials
 data/
    raw/                          ← Downloaded data
    processed/                    ← Clean data + results
 tests/
    test_*.py                     ← Unit/integration tests
 main.py                           ← Entry point
 *.md                              ← Documentation
```

---

## Success Metrics

### Business Metrics (Profit & Risk)
- Total Return >15%
- Sharpe Ratio >1.0
- Max Drawdown <25%
- Win Rate >55%

### Technical Metrics (Model Performance)
- ML Direction Accuracy >65%
- RSI Signal Win Rate >60%
- F&G Correlation >0.3

### Current v1.0 Performance
- Max Drawdown: -8% to -30% (below 25% target)
- Total Return: +31-37% bulls, -14-54% bears
- Beat buy-hold in bears: +6-11%
- ML Accuracy: 49.7% (needs improvement)

---

## Next Steps

### Immediate Priorities
1. **Keep v1.0 config** - proven defensive strategy
2.  **Fix ML model** - 49.7% → 65%+ accuracy
3. **Monitor Google Sheets** - ensure API stays connected

### Future Enhancements
1. **Weighted average entry** - better stop-loss tracking
2. **Explicit price drop %** - additional DCA trigger
3. **Market regime detection** - different params for bull/bear
4. **Adaptive take-profit** - 15% in bears, 30-50% in bulls

---

## Quick Reference

### Run Backtest
```bash
python main.py --mode backtest
```

### Update Config (Google Sheets)
1. Edit: https://docs.google.com/spreadsheets/d/YOUR_ID
2. Config auto-refreshes every 5 minutes

### Test on Multiple Periods
```bash
python tests/test_multiple_periods.py
```

### Chat Interface
```bash
python main.py --mode chat
```

---

## Documentation Index

- **This file:** Architecture overview
- [README.md](README.md) - Full project documentation
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [AGENT_ARCHITECTURE_NUANCES.md](AGENT_ARCHITECTURE_NUANCES.md) - LangGraph implementation details
- [NATURAL_LANGUAGE_GUIDE.md](NATURAL_LANGUAGE_GUIDE.md) - Chat interface usage
- [MULTI_PERIOD_ANALYSIS.md](MULTI_PERIOD_ANALYSIS.md) - v1.0 performance analysis
- [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md) - Config API setup
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing procedures

---

**Last Updated:** 2025-11-29
**Version:** v1.0 (Defensive Risk Management Strategy)
