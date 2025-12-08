# Telegram Notifications - Quick Start (5 Minutes)

## Step 1: Create Bot (2 minutes)
1. Open Telegram → Search `@BotFather`
2. Send: `/newbot`
3. Copy token: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

## Step 2: Get Chat ID (1 minute)
1. Search `@userinfobot`
2. Send: `/start`
3. Copy ID: `987654321`

## Step 3: Configure (1 minute)
```bash
copy .env.example .env
```

Edit `.env`:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
```

## Step 4: Test (1 minute)
```bash
python src/notifications/telegram_notifier.py
```

Check Telegram for 5 test messages!

---

## What You'll Get

**Every trade sends instant alert:**

```
 BUY SIGNAL EXECUTED

Strategy: DCA
Price: $95,234.00
Amount: $1,000.00
BTC Acquired: 0.010500 BTC

Reason: DCA: RSI < 30

Portfolio Value: $10,500.00
```

---

## Where Notifications Trigger

**Live Trading:**
```bash
python main.py --mode live
```
→ Telegram alerts enabled **Chat Mode:**
```bash
python main.py --mode chat
> Execute a trade
```
→ Telegram alerts enabled **Backtesting:**
```bash
python main.py --mode backtest
```
→ Telegram disabled (no spam) ---

## Files Changed

1. **Created:**
   - `src/notifications/telegram_notifier.py` - Telegram integration
   - `.env.example` - Template for credentials

2. **Modified:**
   - `src/decision_box/trading_logic.py` - Added notification calls
   - `src/backtesting/backtest_engine.py` - Disabled for backtests

---

## Troubleshooting

**Not working?**
```bash
# Check .env file exists
dir .env

# Test connection
python -c "from src.notifications.telegram_notifier import TelegramNotifier; t = TelegramNotifier(); t.test_connection()"
```

**Still not working?**
- Verify bot token is correct
- Verify chat ID is correct
- Check no extra spaces in .env
- Start your bot (send `/start` to it)

---

**Full Guide:** [TELEGRAM_SETUP_GUIDE.md](TELEGRAM_SETUP_GUIDE.md)

**Total Time:** 5 minutes ⏱
**Status:** Ready to use 