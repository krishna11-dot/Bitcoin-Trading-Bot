# Complete Notification Workflow - Telegram + Gmail

**Purpose:** Understanding the complete notification architecture with both real-time alerts and daily summaries

**Read time:** 15 minutes

**Last updated:** 2025-11-30

---

## Notification Strategy

**Two-tier notification system:**

1. **Telegram** → Real-time trade alerts (instant awareness)
2. **Gmail** → Daily summary emails (detailed analysis)

**Why both?**
- Telegram: Quick glance ("Just bought BTC!")
- Gmail: Deep dive ("How did I perform today?")

---

## Architecture Diagram

```

                        TRADING SYSTEM                            

                              
                    
                       Data Ingestion   
                      (Bitcoin Data)    
                    
                              
              
                                            
        
         Module 1      Module 2    Module 3   
        Sentiment     Technical    ML Model   
       (Fear & Greed) (RSI/MACD)  Prediction  
        
                                            
              
                              
                    
                       DECISION BOX    
                     (Trading Logic)   
                                       
                      Strategy Priority:
                      1. Circuit Breaker
                      2. Stop-Loss      
                      3. Take-Profit    
                      4. DCA            
                      5. Swing Trading  
                    
                              
                    
                      EXECUTE TRADE    
                      (BUY/SELL/PAUSE) 
                    
                              
              
                                            
                  
         TELEGRAM                      GMAIL       
       (Real-time)                 (Daily Summary) 
                                                   
        BUY Alert                Portfolio Value 
        SELL Alert               All Trades      
       [PAUSED]PAUSE Alert              Metrics         
                  
                              
                    
                     Portfolio Updated 
                     (Cash + BTC)      
                    
```

---

## Notification Timing

### Telegram: Real-Time (Immediate)

**Triggers:** After EVERY trade execution

**Example timeline:**
```
10:30 AM → DCA triggers (RSI < 30)
10:30 AM → Execute BUY $5,000
10:30 AM →  Telegram: " BUY @ $93,450"
```

**Purpose:** Instant awareness of what bot is doing

---

### Gmail: Daily Summary (End of Day)

**Triggers:** Once per day (scheduled)

**Example timeline:**
```
10:30 AM → Trade 1: BUY $5,000
02:15 PM → Trade 2: SELL $3,000
06:45 PM → Trade 3: BUY $2,000
11:59 PM →  Gmail: Daily Summary (all 3 trades + metrics)
```

**Purpose:** Comprehensive daily review

---

## Workflow by Mode

### Mode 1: Live Trading (Production)

**Flow:**
```
1. Data ingestion (every hour)
   ↓
2. Modules analyze data
   ↓
3. Decision Box determines action
   ↓
4. IF action is BUY/SELL/PAUSE:
   > Execute trade
   > Send Telegram alert (real-time)
   > Add to today's trade list
   ↓
5. At 11:59 PM:
   > Send Gmail summary (all trades + metrics)
```

**Notifications:**
- Telegram: Enabled (real-time alerts)
- Gmail: Enabled (daily summary)

---

### Mode 2: Chat (Natural Language)

**Flow:**
```
User: "How many trades did I make?"
   ↓
LangGraph Agent:
  > understand_node (classify intent)
  > validate_node (verify valid)
  > execute_node (query backtest results)
  > respond_node (answer user)
```

**Notifications:**
- Telegram: Disabled (no trades executed)
- Gmail: Disabled (read-only mode)

---

### Mode 3: Backtest (Historical)

**Flow:**
```
1. Load historical data (2018-2025)
   ↓
2. Simulate trades day by day
   ↓
3. FOR EACH SIMULATED TRADE:
   > Execute in backtest (no real money)
   > Telegram: DISABLED (avoid spam)
   > Gmail: DISABLED (avoid spam)
   ↓
4. At end of backtest:
   > Save results.json (19 trades, -14.25% return)
```

**Notifications:**
- Telegram: Disabled (prevents 19+ spam messages)
- Gmail: Disabled (backtest is historical, not daily)

**Why disabled?**
- Backtest runs through 2+ years in seconds
- Would send hundreds of notifications
- Results saved to JSON instead

---

## Notification Content

### Telegram Alert (Real-Time)

**BUY Example:**
```
 BUY SIGNAL EXECUTED

Strategy: DCA (RSI + Fear & Greed)
Price: $93,450.00
Amount: $5,000.00
BTC Acquired: 0.053512 BTC

Reason: RSI at 28 (< 30), Fear & Greed at 35 (< 40)
Portfolio Value: $95,832.45
```

**SELL Example:**
```
 SELL SIGNAL EXECUTED

Strategy: Take Profit
Price: $98,120.00
Amount: $5,750.00
BTC Sold: 0.058613 BTC
Profit: +$750.00 (+15.0%)

Reason: 15% gain target reached
Portfolio Value: $98,582.45
```

**PAUSE Example:**
```
[PAUSED]TRADING PAUSED

Strategy: Circuit Breaker
Current Price: $85,320.00
Trigger: -20% drawdown threshold

Trading paused for 7 days to prevent further losses.
Resume Date: 2025-12-07
Portfolio Value: $80,123.00
```

---

### Gmail Summary (Daily)

**Email Subject:**
```
BTC Trading Bot - Daily Summary 2025-11-30
```

**Email Content (HTML formatted):**

**1. Portfolio Summary**
```
Portfolio Value: $95,832.45
 +5.83% Total Return

Asset Breakdown:

 Cash (USD)               $45,123.00   
 Bitcoin Holdings         0.543210 BTC 
 BTC Value @ $93,450      $50,709.45   

```

**2. Performance Metrics**
```

 Sharpe Ratio      0.87     
 Max Drawdown      -15.2%   
 Win Rate          52.6%    
 Total Trades      19       

```

**3. Trades Today**
```

 Action  Price      Amount     Strategy             Time     

  BUY  $93,450    $5,000     DCA (RSI + F&G)      10:30 AM 
  SELL $98,120    $5,750     Take Profit          02:15 PM 
  BUY  $95,800    $2,000     DCA (Fear & Greed)   06:45 PM 

```

---

## Integration Points

### File: `src/decision_box/trading_logic.py`

**Lines 57-82: Initialization**
```python
class TradingDecisionBox:
    def __init__(self, config: Dict,
                 telegram_enabled: bool = True,
                 gmail_enabled: bool = True):

        self.config = config
        self.portfolio = {...}

        # Initialize notifications
        self.telegram = TelegramNotifier(enabled=telegram_enabled)
        self.gmail = GmailNotifier(enabled=gmail_enabled)

        # Track today's trades for Gmail summary
        self.trades_today = []
```

---

**Lines 475-484: BUY Execution + Telegram**
```python
def execute_trade(self, decision: Dict, current_price: float):
    if decision['action'] == 'BUY':
        # Execute BUY
        btc_bought = decision['amount'] / current_price
        self.portfolio['btc'] += btc_bought
        self.portfolio['cash'] -= decision['amount']

        # Real-time Telegram alert
        portfolio_value = self.portfolio['cash'] + (self.portfolio['btc'] * current_price)
        self.telegram.notify_trade(decision, current_price, portfolio_value)

        # Add to today's summary list
        self.trades_today.append({
            'action': 'BUY',
            'price': current_price,
            'amount': decision['amount'],
            'strategy': decision.get('strategy', 'Unknown'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
```

---

**Lines 550-565: End of Day Gmail Summary**
```python
def send_daily_summary(self):
    """Called at end of trading day (11:59 PM)."""

    # Calculate current metrics
    current_price = self._get_current_price()
    metrics = {
        'total_return': self._calculate_total_return(),
        'sharpe_ratio': self._calculate_sharpe(),
        'max_drawdown': self._calculate_max_drawdown(),
        'win_rate': self._calculate_win_rate(),
        'total_trades': len(self.trade_history)
    }

    # Send Gmail summary
    self.gmail.send_daily_summary(
        portfolio=self.portfolio,
        trades_today=self.trades_today,
        metrics=metrics,
        current_price=current_price
    )

    # Reset for next day
    self.trades_today = []
```

---

### File: `src/backtesting/backtest_engine.py`

**Line 85: Disable notifications during backtest**
```python
class BacktestEngine:
    def run(self, data: pd.DataFrame, config: Dict):
        # Disable notifications for backtest (prevents spam)
        self.decision_box = TradingDecisionBox(
            config,
            telegram_enabled=False,  # ← Prevents 19+ Telegram alerts
            gmail_enabled=False      # ← Prevents daily summary spam
        )
```

---

## Error Handling & Graceful Degradation

**Both Telegram and Gmail use same pattern:**

### 1. Missing Credentials → Disabled (Not Crash)

**Telegram:**
```python
# If TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing:
self.enabled = False
print("[TELEGRAM] Warning: Credentials missing, notifications disabled")
# Trading continues normally
```

**Gmail:**
```python
# If gmail_credentials.json or GMAIL_RECIPIENT_EMAIL missing:
self.enabled = False
print("[GMAIL] Warning: Setup incomplete, summaries disabled")
# Trading continues normally
```

---

### 2. API Failures → Logged (Not Crash)

**Telegram:**
```python
def send_message(self, message: str) -> bool:
    try:
        response = requests.post(self.api_url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"[TELEGRAM] Error: {e}")
        return False  # Trading continues
```

**Gmail:**
```python
def send_email(self, subject: str, body_html: str) -> bool:
    try:
        self.service.users().messages().send(...).execute()
        return True
    except Exception as e:
        print(f"[GMAIL] Error: {e}")
        return False  # Trading continues
```

---

### 3. Timeouts → Continue Trading

**Both have 5-second timeouts:**
```python
# Telegram
response = requests.post(..., timeout=5)

# Gmail
# Built into Google API client (30s default, adjustable)
```

**Result:** If notification takes > 5 seconds, it fails gracefully, trading continues

---

## Testing Notifications

### Test 1: Telegram Connection

```bash
python -c "
from src.notifications.telegram_notifier import TelegramNotifier
t = TelegramNotifier()
print('Enabled:', t.enabled)
t.send_message('Test message from BTC bot')
"
```

**Expected:**
- Prints: `Enabled: True`
- Telegram message received

---

### Test 2: Gmail Connection

```bash
python src/notifications/gmail_notifier.py
```

**Expected:**
- First run: Browser opens for OAuth
- Test email sent
- Token saved to `config/gmail_token.pickle`

---

### Test 3: Both Together

```python
from src.notifications import TelegramNotifier, GmailNotifier

# Initialize both
telegram = TelegramNotifier()
gmail = GmailNotifier()

# Test Telegram
telegram.send_message(" Test: Telegram working!")

# Test Gmail
gmail.send_email(
    subject=" Test: Gmail working!",
    body_html="<h2>Gmail API Test Successful</h2>"
)

print(f"Telegram: {telegram.enabled}")
print(f"Gmail: {gmail.enabled}")
```

---

## Comparison Table

| Feature | Telegram | Gmail |
|---------|----------|-------|
| **Timing** | Real-time (every trade) | Daily (end of day) |
| **Format** | Plain text, Markdown | Rich HTML |
| **Content** | Single trade details | Full portfolio report |
| **Setup Time** | 2 minutes | 20 minutes |
| **Authentication** | Bot token (simple) | OAuth 2.0 (complex) |
| **Notifications** | Mobile push | Email inbox |
| **Suitable For** | Quick awareness | Detailed analysis |
| **Trade Frequency** | High (every trade) | Low (once per day) |
| **Mobile Experience** | Excellent (instant) | Good (email app) |
| **Desktop Experience** | Good (Telegram app) | Excellent (full HTML) |

---

## When to Use Which

### Use Telegram When:
- You want instant awareness of trades
- You're away from computer (mobile alerts)
- You need quick glance at what happened
- Trading frequently (multiple trades per day)

### Use Gmail When:
- You want detailed daily analysis
- You need historical record (searchable emails)
- You prefer rich formatting (charts, tables)
- You review portfolio at end of day

### Use BOTH When:
- You want real-time awareness + daily review
- You trade actively (need both quick + detailed info)
- You want professional reporting (Gmail) + mobile alerts (Telegram)

**Recommendation:** Use BOTH for best experience!

---

## Scheduling Daily Summaries

### Windows Task Scheduler

**Create task:**
1. Open Task Scheduler
2. Create Basic Task
3. Name: "BTC Trading Bot - Daily Summary"
4. Trigger: Daily at 11:59 PM
5. Action: Start a program
   - Program: `python`
   - Arguments: `main.py --send-daily-summary`
   - Start in: `<your-project-directory>`

---

### Mac/Linux Cron

**Edit crontab:**
```bash
crontab -e
```

**Add:**
```bash
# Daily summary at 11:59 PM
59 23 * * * cd /path/to/btc-intelligent-trader && python main.py --send-daily-summary
```

---

### Python Scheduler (In-Process)

**Add to main.py:**
```python
import schedule
import time

def send_daily_summary():
    """Send daily Gmail summary."""
    from src.decision_box.trading_logic import TradingDecisionBox
    decision_box = TradingDecisionBox(config)
    decision_box.send_daily_summary()

# Schedule daily at 11:59 PM
schedule.every().day.at("23:59").do(send_daily_summary)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute
```

---

## Summary

**You now have:**
- Telegram: Real-time trade alerts
- Gmail: Daily portfolio summaries
- Graceful degradation (trading continues if notifications fail)
- Clear separation: instant awareness vs detailed analysis
- Production-ready notification system

**Setup:**
- Telegram: 2 minutes (already done)
- Gmail: 20 minutes (see GMAIL_SETUP_GUIDE.md)

**Total:** 22 minutes for complete notification system

---

## Related Documentation

- **Telegram Setup:** [TELEGRAM_SETUP_GUIDE.md](TELEGRAM_SETUP_GUIDE.md)
- **Telegram Quick Start:** [TELEGRAM_QUICK_START.md](TELEGRAM_QUICK_START.md)
- **Gmail Setup:** [GMAIL_SETUP_GUIDE.md](GMAIL_SETUP_GUIDE.md)
- **Gmail Quick Start:** [GMAIL_QUICK_START.md](GMAIL_QUICK_START.md)
- **Architecture:** [ARCHITECTURE_SUMMARY.md](ARCHITECTURE_SUMMARY.md)
- **Testing:** [TESTING_GUIDE.md](TESTING_GUIDE.md)

---

**Status:** Complete Notification System **Real-time Alerts:** Telegram **Daily Summaries:** Gmail **Production-Ready:** Both **Last Updated:** 2025-11-30
