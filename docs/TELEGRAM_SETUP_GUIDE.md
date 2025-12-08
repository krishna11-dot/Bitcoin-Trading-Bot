# Telegram Notifications Setup Guide

**Date:** 2025-11-29
**Status:** READY TO USE
**Purpose:** Get real-time trade alerts on your phone

---

## What You'll Get

Every time the bot executes a trade, you'll receive an instant Telegram message with:

###  BUY Notifications
```
 BUY SIGNAL EXECUTED

Strategy: DCA
Price: $95,234.00
Amount: $1,000.00
BTC Acquired: 0.010500 BTC

Reason: DCA: RSI < 30, Fear & Greed < 40

Portfolio Value: $10,500.00
```

###  SELL Notifications
```
 SELL SIGNAL EXECUTED

Strategy: Take Profit
Price: $97,850.00
BTC Sold: 0.010500 BTC
Cash Received: $1,027.43

Reason: Take Profit: +15% gain, RSI > 65

Portfolio Value: $11,527.43
```

### [WARNING]CIRCUIT BREAKER Alerts
```
[WARNING]CIRCUIT BREAKER ACTIVATED

Trading has been PAUSED

Reason: Portfolio value below 75% of initial capital

Current Price: $90,000.00
Portfolio Value: $7,500.00
```

---

## Setup Steps (5 Minutes)

### Step 1: Create Telegram Bot

1. **Open Telegram** on your phone or desktop
2. **Search for** `@BotFather` (verified account with blue checkmark)
3. **Send** `/newbot` command
4. **Choose a name** for your bot (e.g., "My BTC Trader Bot")
5. **Choose a username** (must end in 'bot', e.g., "my_btc_trader_bot")
6. **Copy the bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

**Screenshot:**
```
BotFather: Done! Congratulations on your new bot...
Use this token to access the HTTP API:
123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

---

### Step 2: Get Your Chat ID

1. **Search for** `@userinfobot` on Telegram
2. **Send** `/start` command
3. **Copy your Chat ID** (looks like: `987654321`)

**Screenshot:**
```
User Info Bot:
Id: 987654321
First name: Your Name
```

---

### Step 3: Configure Environment Variables

1. **Copy** the `.env.example` file to `.env`:
   ```bash
   copy .env.example .env
   ```

2. **Edit** `.env` file:
   ```env
   # Telegram Notifications
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=987654321
   ```

3. **Save** the file

**Important:** The `.env` file is already in `.gitignore` and will NOT be committed to version control.

---

### Step 4: Test the Connection

Run the Telegram notifier test script:

```bash
python src/notifications/telegram_notifier.py
```

**Expected Output:**
```
============================================================
TELEGRAM NOTIFIER - Testing
============================================================

[TEST 1] Testing connection...
[TELEGRAM] Test message sent successfully!

[TEST 2] Testing BUY notification...
[TEST 3] Testing SELL notification...
[TEST 4] Testing CIRCUIT BREAKER notification...
[TEST 5] Testing portfolio summary...

============================================================
All tests complete! Check your Telegram for messages.
============================================================
```

**Check your Telegram** - you should receive 5 test messages.

---

## Where Telegram Fits in the Workflow

### Architecture Diagram

```

                   USER (You on Telegram)                     
                   Receives instant alerts                   

                           
                    
                      Telegram   
                       Bot API   
                    
                           

              src/notifications/telegram_notifier.py          
  • Formats trade messages                                    
  • Sends HTTP requests to Telegram API                       
  • Handles errors gracefully (won't break trading)           

                           

           src/decision_box/trading_logic.py                  
                                                               
  execute_trade(decision, current_price, date):               
    if decision['action'] == 'BUY':                           
        # Update portfolio                                    
        portfolio['btc'] += btc_bought                        
        portfolio['cash'] -= amount                           
                                                               
        #  SEND TELEGRAM NOTIFICATION                       
        telegram.notify_trade(decision, current_price)  ← HERE
                                                               
    elif decision['action'] == 'SELL':                        
        # Update portfolio                                    
        portfolio['cash'] += cash_received                    
        portfolio['btc'] -= amount_sold                       
                                                               
        #  SEND TELEGRAM NOTIFICATION                       
        telegram.notify_trade(decision, current_price)  ← HERE
                                                               
    elif decision['action'] == 'PAUSE':                       
        #  SEND CIRCUIT BREAKER ALERT                       
        telegram.notify_trade(decision, current_price)  ← HERE

```

---

## Organized Workflow Integration

### Where Notifications Happen

**1. Live Trading Mode** (`python main.py --mode live`)
```
Data Fetch → Module 1,2,3 → Decision Box → Execute Trade →  Telegram Alert → YOU
```

**2. Chat Interface** (`python main.py --mode chat`)
```
User: "Execute a trade"
   ↓
Decision Box → Execute Trade →  Telegram Alert → YOU
```

**3. Backtesting Mode** (`python main.py --mode backtest`)
```
Historical Data → Decision Box → Execute Trade → No Telegram (disabled)
```
**Telegram is automatically disabled during backtesting** to avoid spam from hundreds of historical trades.

---

## File Structure

```
btc-intelligent-trader/
 .env                                    ← YOUR CREDENTIALS (not in git)
 .env.example                            ← Template (copy this)
 src/
    notifications/                      ← NEW FOLDER
       __init__.py                     ← Module init
       telegram_notifier.py            ← Telegram integration
    decision_box/
       trading_logic.py                ← MODIFIED (added notifications)
    backtesting/
        backtest_engine.py              ← MODIFIED (disabled Telegram)
 TELEGRAM_SETUP_GUIDE.md                 ← This file
```

---

## Usage Examples

### Scenario 1: Live Trading with Notifications

```bash
# Start live trading (Telegram enabled by default)
python main.py --mode live
```

**What happens:**
1. Bot fetches live BTC price
2. Makes trading decision
3. If BUY/SELL → Executes trade
4. **Immediately sends Telegram notification** 
5. You get alert on your phone

---

### Scenario 2: Backtesting (No Spam)

```bash
# Run backtest (Telegram automatically disabled)
python main.py --mode backtest
```

**What happens:**
1. Bot simulates 19 trades on historical data
2. **No Telegram notifications** (would be spam)
3. Results saved to JSON file
4. You can check results in chat mode

---

### Scenario 3: Manual Trade via Chat

```bash
# Start chat interface
python main.py --mode chat
```

**Chat:**
```
[YOU] Execute a trade
[BOT] Executing trade cycle...

[TRADE] DCA: $1,000 (0.010500 BTC) at $95,234

[BOT] Trade executed successfully!
```

**Telegram Alert:**
```
 BUY SIGNAL EXECUTED
Strategy: DCA
Price: $95,234.00
...
```

---

## Customization Options

### Disable Notifications Temporarily

**Option 1: Set environment variable to empty**
```env
# In .env file
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

**Option 2: Disable in code**
```python
# In your script
decision_box = TradingDecisionBox(config, telegram_enabled=False)
```

---

### Custom Notification Format

Edit [src/notifications/telegram_notifier.py](src/notifications/telegram_notifier.py) `notify_trade()` method:

```python
# Example: Add more details
message = f"""
 *BUY SIGNAL EXECUTED*

*Strategy:* {strategy}
*Price:* ${current_price:,.2f}
*Amount:* ${amount:,.2f}
*BTC Acquired:* {btc_bought:.6f} BTC

*Reason:* {reason}

*Technical Indicators:*
  RSI: {technical['RSI']}
  MACD: {technical['MACD']}

*Portfolio Value:* ${portfolio_value:,.2f}
"""
```

---

## Troubleshooting

### Issue: "Bot token or chat ID not configured"

**Solution:**
1. Check `.env` file exists (not `.env.example`)
2. Verify credentials are correct
3. No extra spaces in `.env` file

---

### Issue: "Error: 401 Unauthorized"

**Solution:**
- Bot token is incorrect
- Get new token from @BotFather: `/newbot`

---

### Issue: "Error: 400 Bad Request - chat not found"

**Solution:**
- Chat ID is incorrect
- Get correct ID from @userinfobot
- Make sure to start your bot first (send `/start` to your bot)

---

### Issue: "Notifications not sending"

**Solution:**
1. Test connection:
   ```bash
   python src/notifications/telegram_notifier.py
   ```

2. Check error messages in console

3. Verify internet connection

4. Try sending a test message manually:
   ```bash
   python -c "from src.notifications.telegram_notifier import TelegramNotifier; t = TelegramNotifier(); t.test_connection()"
   ```

---

### Issue: "Notifications working but too much spam during backtest"

**Solution:**
- This shouldn't happen - Telegram is automatically disabled for backtests
- If you see spam, check [src/backtesting/backtest_engine.py](src/backtesting/backtest_engine.py) line 85:
  ```python
  self.decision_box = TradingDecisionBox(config, telegram_enabled=False)
  ```

---

## Security Best Practices

### DO:
- Keep `.env` file secret (never commit to git)
- Use `.env.example` as template for others
- Share bot token only with trusted people
- Revoke and regenerate token if compromised

### DON'T:
- Commit `.env` to version control
- Share screenshots with bot token visible
- Use same bot for multiple purposes
- Store credentials in code files

---

## Advanced Features

### Send Portfolio Summary Manually

```python
from src.notifications.telegram_notifier import TelegramNotifier
from src.decision_box.trading_logic import TradingDecisionBox

# Create notifier
telegram = TelegramNotifier()

# Get portfolio summary from decision box
portfolio = decision_box.get_portfolio_summary(current_price=95000)

# Send notification
telegram.notify_portfolio_summary(portfolio, current_price=95000)
```

**You'll receive:**
```
PORTFOLIO SUMMARY

BTC Holdings: 0.105000 BTC
BTC Value: $9,975.00
Cash: $5,000.00
Total Value: $14,975.00

Total Return: +49.75%
Total Trades: 12

Current BTC Price: $95,000.00
```

---

### Send Custom Error Alerts

```python
telegram = TelegramNotifier()
telegram.notify_error("API connection failed - check network")
```

**You'll receive:**
```
ERROR ALERT

API connection failed - check network

Please check the trading bot immediately.
```

---

## Next Steps

1. **Complete Setup**
   - Create bot with @BotFather
   - Get chat ID from @userinfobot
   - Configure `.env` file
   - Test connection

2. **Test Notifications**
   - Run test script
   - Verify 5 messages received
   - Try manual trade in chat mode

3. **Enable for Live Trading**
   - Telegram is enabled by default
   - Just run `python main.py --mode live`
   - You're all set!

4. ** Read More**
   - [V1_BASELINE_REFERENCE.md](V1_BASELINE_REFERENCE.md) - Strategy overview
   - [ARCHITECTURE_SUMMARY.md](ARCHITECTURE_SUMMARY.md) - System architecture
   - [NATURAL_LANGUAGE_GUIDE.md](NATURAL_LANGUAGE_GUIDE.md) - Chat interface guide

---

## Summary

### What's Integrated

1. **Telegram Notifier Module** - [src/notifications/telegram_notifier.py](src/notifications/telegram_notifier.py)
2. **Trading Logic Integration** - [src/decision_box/trading_logic.py](src/decision_box/trading_logic.py)
3. **Backtest Engine Updated** - [src/backtesting/backtest_engine.py](src/backtesting/backtest_engine.py)
4. **Environment Template** - [.env.example](.env.example)

### What You Need to Do

1. Create Telegram bot (5 min)
2. Get chat ID (1 min)
3. Create `.env` file (1 min)
4. Test connection (1 min)

**Total setup time: ~8 minutes**

---

## Support

**Issues?**
- Check troubleshooting section above
- Test with: `python src/notifications/telegram_notifier.py`
- Verify `.env` file format

**Working?**
- You'll get instant alerts for all trades - Circuit breaker warnings - Portfolio updates available ---

**Status:** Production-Ready **Last Updated:** 2025-11-29
**Integration:** Complete **Documentation:** Complete 