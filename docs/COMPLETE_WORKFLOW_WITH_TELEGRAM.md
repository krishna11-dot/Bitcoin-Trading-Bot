# Complete Trading Workflow with Telegram Notifications

**Date:** 2025-11-29
**Status:** FULLY INTEGRATED

---

## Complete System Architecture

```

                        USER (You)                                          
  • Configures parameters in Google Sheets                                 
  • Asks questions via Natural Language Chat                               
  • Receives trade alerts on Telegram                                     

                                                        
              (Reads config)                             (Receives alerts)
                                                        
                   
   GOOGLE SHEETS API                           TELEGRAM BOT API       
  • v1.0 parameters                           • Real-time trade alerts
  • Live config updates                       • Circuit breaker warns 
  • 5-min cache                               • Portfolio summaries   
                   
                                                        
                                                        
                                                        

                   CONFIG MANAGER                                         
  • Loads from Google Sheets                                              
  • Caches locally (5 min)                                                
  • Fallback to local JSON                                                

             
              (Provides config)
             

                   DECISION BOX (Core Trading Logic)                      
    
    STRATEGY PRIORITY ORDER:                                           
    1. Circuit Breaker → PAUSE trading if loss > 25%                   
    2. Stop-Loss → SELL if price < entry - 2×ATR                       
    3. Take Profit → SELL if profit > 15% + RSI > 65                   
    4. Swing Trading → BUY if high ML confidence + RSI oversold        
    5. DCA → BUY if RSI < 30 OR Fear & Greed < 40                      
    6. HOLD → Default (no action)                                      
    
                                                                           
  execute_trade(decision, current_price):                                 
    if action == 'BUY':                                                   
        portfolio['btc'] += btc_bought                                    
        portfolio['cash'] -= amount                                       
                  
          telegram.notify_trade(decision, price, value)              
                  
                                                                           
    elif action == 'SELL':                                                
        portfolio['cash'] += cash_received                                
        portfolio['btc'] -= amount                                        
                  
          telegram.notify_trade(decision, price, value)              
                  
                                                                           
    elif action == 'PAUSE':                                               
                  
          telegram.notify_trade(decision, price, value)              
            [WARNING]CIRCUIT BREAKER ALERT                                   
                  

                   
                    (Gets indicators, sentiment, predictions)
                   
        
                             
                             
  
 MODULE 1   MODULE 2   MODULE 3 
 Technical  Sentiment    ML     
Indicators  Analysis  Prediction
  
                             
                             
     
                  
                   (Fetches data)
                  
        
          DATA PIPELINE       
          • Historical CSV    
          • Live APIs (future)
        
```

---

## Workflow by Mode

### Mode 1: Live Trading

```
START: python main.py --mode live

1. Load Config from Google Sheets
    Parameters: RSI 30, F&G 40, ATR 2.0, T/P 15%

2. Fetch Live BTC Price
    Current: $95,234.00

3. Calculate Technical Indicators
    Module 1: RSI = 28, ATR = $2,450, MACD = positive

4. Get Sentiment Data
    Module 2: Fear & Greed = 35 (fear)

5. Get ML Prediction
    Module 3: Predicted = $96,500, Confidence = 52%

6. Make Decision (Decision Box)
    Check strategies in priority order:
      1. Circuit Breaker? NO (portfolio > 75%)
      2. Stop-Loss? NO (not holding BTC)
      3. Take Profit? NO (not holding BTC)
      4. Swing Entry? NO (ML confidence 52% < 70%)
      5. DCA Entry? YES (RSI 28 < 30 AND F&G 35 < 40) Decision: BUY $1,000 via DCA

7. Execute Trade
    Buy 0.010500 BTC at $95,234
    Update portfolio: cash -= $1,000, btc += 0.010500

8.  SEND TELEGRAM NOTIFICATION
    Message sent to your phone:
        BUY SIGNAL EXECUTED
       Strategy: DCA
       Price: $95,234.00
       Amount: $1,000.00
       BTC Acquired: 0.010500 BTC

       Reason: DCA: RSI < 30, Fear & Greed < 40
       Portfolio Value: $10,500.00

9. Wait for next cycle (repeat)
```

**Key Points:**
- Telegram enabled for live trading
- You get instant notification on your phone
- Notifications include all trade details

---

### Mode 2: Chat Interface

```
START: python main.py --mode chat

[YOU] Execute a trade

1. Natural Language Understanding
    LangGraph: Intent = "run_trade"

2. Guardrails Validation
    "run_trade" is VALID intent 3. Execute Tool
    Calls Decision Box make_decision()
    Gets decision: BUY $1,000 DCA
    Calls execute_trade()

4.  SEND TELEGRAM NOTIFICATION
    Same as live mode

5. Format Response
    LLM: "Trade executed successfully! Bought 0.010500 BTC via DCA"

[BOT] Trade executed successfully! Bought 0.010500 BTC via DCA strategy.

[TELEGRAM]  BUY SIGNAL EXECUTED (you receive this too)
```

**Key Points:**
- Telegram enabled for chat trades
- You get notification even for manual trades
- Chat confirms trade + Telegram alert

---

### Mode 3: Backtesting

```
START: python main.py --mode backtest

1. Load Historical Data
    2025 data (6 months)

2. Initialize Decision Box
    TradingDecisionBox(config, telegram_enabled=False) 3. Run 19 Trades on Historical Data
    Each trade:
      - Make decision
      - Execute trade
      - NO TELEGRAM (disabled to avoid spam)

4. Calculate Metrics
    Total return: -14.25%
    Buy-hold: -20.08%
    Outperformance: +5.83% 5. Save Results to JSON
    data/processed/backtest_results.json

6. Print Summary
```

**Key Points:**
- Telegram DISABLED for backtesting
- Avoids 19 notification spam
- Results available in JSON for analysis

---

## Notification Examples by Strategy

### 1. DCA Entry

**Trigger:**
- RSI < 30 (28)
- Fear & Greed < 40 (35)

**Telegram:**
```
 BUY SIGNAL EXECUTED

Strategy: DCA
Price: $95,234.00
Amount: $1,000.00
BTC Acquired: 0.010500 BTC

Reason: DCA: RSI < 30, Fear & Greed < 40

Portfolio Value: $10,500.00
```

---

### 2. Swing Trade Entry

**Trigger:**
- RSI < 30
- MACD > 0
- ML confidence > 70%
- Predicted price > current × 1.03

**Telegram:**
```
 BUY SIGNAL EXECUTED

Strategy: Swing
Price: $95,000.00
Amount: $1,000.00
BTC Acquired: 0.010526 BTC

Reason: Swing: RSI < 30, MACD bullish, ML confidence 75%

Portfolio Value: $11,000.00
```

---

### 3. Stop-Loss Exit

**Trigger:**
- Current price < entry price - 2×ATR
- Entry: $95,000, ATR: $2,450
- Stop: $90,100
- Current: $90,050 Trigger

**Telegram:**
```
 SELL SIGNAL EXECUTED

Strategy: Stop-Loss
Price: $90,050.00
BTC Sold: 0.010526 BTC
Cash Received: $947.98

Reason: Stop-Loss: Price fell below $90,100 (entry - 2×ATR)

Portfolio Value: $9,947.98
```

---

### 4. Take Profit Exit

**Trigger:**
- Portfolio profit > 15%
- RSI > 65

**Telegram:**
```
 SELL SIGNAL EXECUTED

Strategy: Take Profit
Price: $109,750.00
BTC Sold: 0.010526 BTC
Cash Received: $1,155.23

Reason: Take Profit: +15% gain, RSI > 65 (overbought)

Portfolio Value: $11,155.23
```

---

### 5. Circuit Breaker

**Trigger:**
- Portfolio value < 75% of initial capital
- Initial: $10,000
- Current: $7,450 Trigger

**Telegram:**
```
[WARNING]CIRCUIT BREAKER ACTIVATED

Trading has been PAUSED

Reason: Portfolio value below 75% of initial capital

Current Price: $85,000.00
Portfolio Value: $7,450.00
```

**Important:** You'll get this alert IMMEDIATELY to take action.

---

## File Modifications Summary

### Files Created

1. **`src/notifications/__init__.py`**
   - Module initialization

2. **`src/notifications/telegram_notifier.py`** (270 lines)
   - TelegramNotifier class
   - notify_trade() method
   - notify_portfolio_summary() method
   - notify_error() method
   - test_connection() method

3. **`.env.example`**
   - Template for credentials
   - Instructions for setup

4. **`TELEGRAM_SETUP_GUIDE.md`**
   - Complete setup guide
   - Troubleshooting
   - Examples

5. **`TELEGRAM_QUICK_START.md`**
   - 5-minute quick start
   - Essential steps only

6. **`COMPLETE_WORKFLOW_WITH_TELEGRAM.md`** (this file)
   - Architecture diagrams
   - Workflow explanations

---

### Files Modified

1. **`src/decision_box/trading_logic.py`**
   - **Line 35:** Added import
     ```python
     from src.notifications.telegram_notifier import TelegramNotifier
     ```

   - **Line 57:** Added telegram_enabled parameter
     ```python
     def __init__(self, config: Dict, telegram_enabled: bool = True):
     ```

   - **Line 82:** Initialize notifier
     ```python
     self.telegram = TelegramNotifier(enabled=telegram_enabled)
     ```

   - **Lines 475-477:** BUY notification
     ```python
     portfolio_value = self.portfolio['cash'] + (self.portfolio['btc'] * current_price)
     self.telegram.notify_trade(decision, current_price, portfolio_value)
     ```

   - **Lines 501-503:** SELL notification
     ```python
     portfolio_value = self.portfolio['cash'] + (self.portfolio['btc'] * current_price)
     self.telegram.notify_trade(decision, current_price, portfolio_value)
     ```

   - **Lines 508-510:** PAUSE notification
     ```python
     portfolio_value = self.portfolio['cash'] + (self.portfolio['btc'] * current_price)
     self.telegram.notify_trade(decision, current_price, portfolio_value)
     ```

2. **`src/backtesting/backtest_engine.py`**
   - **Line 85:** Disable Telegram for backtests
     ```python
     self.decision_box = TradingDecisionBox(config, telegram_enabled=False)
     ```

---

## Integration Points

### 1. Decision Box → Telegram

**Location:** [src/decision_box/trading_logic.py](src/decision_box/trading_logic.py)

**When:** After every trade execution (BUY, SELL, PAUSE)

**What:** Sends formatted message with trade details

**Code:**
```python
def execute_trade(self, decision: Dict, current_price: float, date: str):
    if decision['action'] == 'BUY':
        # ... execute buy logic ...

        #  Telegram notification
        portfolio_value = self.portfolio['cash'] + (self.portfolio['btc'] * current_price)
        self.telegram.notify_trade(decision, current_price, portfolio_value)
```

---

### 2. Telegram Notifier → Telegram API

**Location:** [src/notifications/telegram_notifier.py](src/notifications/telegram_notifier.py)

**When:** Called by Decision Box

**What:** Sends HTTP POST to Telegram Bot API

**Code:**
```python
def send_message(self, message: str) -> bool:
    payload = {
        'chat_id': self.chat_id,
        'text': message,
        'parse_mode': 'Markdown'  # Enables formatting
    }

    response = requests.post(self.api_url, json=payload, timeout=5)
    return response.status_code == 200
```

---

### 3. Environment Variables → Telegram Notifier

**Location:** `.env` file

**When:** On initialization

**What:** Loads bot token and chat ID

**Code:**
```python
def __init__(self, bot_token: str = None, chat_id: str = None, enabled: bool = True):
    # Load .env file
    load_dotenv()

    # Get credentials
    self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
    self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
```

---

## Error Handling & Safety

### 1. Graceful Degradation

**If Telegram fails, trading continues:**

```python
try:
    response = requests.post(self.api_url, json=payload, timeout=5)
    if response.status_code == 200:
        return True
    else:
        print(f"[TELEGRAM] Error: {response.status_code}")
        return False  # ← Trading continues
except Exception as e:
    print(f"[TELEGRAM] Error: {str(e)}")
    return False  # ← Trading continues
```

**Key:** Telegram errors never crash the trading bot.

---

### 2. Timeout Protection

**All requests have 5-second timeout:**

```python
response = requests.post(self.api_url, json=payload, timeout=5)
```

**Reason:** Prevents hanging if Telegram API is slow.

---

### 3. Automatic Disable

**If credentials missing:**

```python
if not self.bot_token or not self.chat_id:
    self.enabled = False
    print("[TELEGRAM] Warning: Bot token or chat ID not configured.")
```

**Result:** Bot runs normally, just no notifications.

---

### 4. Backtest Spam Prevention

**Automatically disabled for backtests:**

```python
# In backtest_engine.py
self.decision_box = TradingDecisionBox(config, telegram_enabled=False)
```

**Result:** No spam from 19 historical trades.

---

## Setup Checklist

- [ ] Create Telegram bot via @BotFather
- [ ] Get bot token
- [ ] Get chat ID from @userinfobot
- [ ] Copy `.env.example` to `.env`
- [ ] Add bot token to `.env`
- [ ] Add chat ID to `.env`
- [ ] Run test: `python src/notifications/telegram_notifier.py`
- [ ] Verify 5 test messages received
- [ ] Done! ---

## Summary

### Where Telegram Fits

**In the Workflow:**
```
Data → Modules → Decision Box → Execute Trade →  Telegram → YOU
```

**In the Code:**
```
trading_logic.py → telegram_notifier.py → Telegram API → Your Phone
```

**In the Architecture:**
```
Core Trading Logic (Decision Box)
    ↓
Notifications Module (Telegram Notifier)
    ↓
External Service (Telegram Bot API)
    ↓
User (You on Telegram)
```

---

### What's Integrated

**Decision Box** - Calls Telegram after every trade
**Telegram Notifier** - Formats and sends messages
**Backtest Engine** - Disables Telegram to avoid spam
**Environment Config** - Loads credentials from .env
**Error Handling** - Never crashes trading if Telegram fails
**Documentation** - Complete guides and examples

---

### What You Need to Do

1. **5-minute setup:**
   - Create bot
   - Get credentials
   - Configure `.env`

2. **Test:**
   - Run test script
   - Verify messages received

3. **Use:**
   - Live trading → Get alerts - Chat mode → Get alerts - Backtesting → No alerts ---

**Status:** Production-Ready **Integration:** Complete **Documentation:** Complete **Testing:** Ready **Error Handling:** Safe **Total Setup Time:** 5 minutes
**Total Development Time:** Complete
**Ready to Use:** YES 