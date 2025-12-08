# Gmail Quick Start - 5 Minutes to Daily Summaries

**Purpose:** Fastest path to Gmail daily summaries

**Read time:** 5 minutes

**Last updated:** 2025-11-30

---

## What You Get

Beautiful daily email summaries with:
- Portfolio value and returns
- Performance metrics
- All trades executed today
- Professional HTML formatting

---

## Prerequisites

**You said you have:**
- Gmail API enabled

**You need:**
-  OAuth client ID (Desktop app)
-  credentials.json downloaded
-  Recipient email in .env

---

## 4-Step Setup (5 minutes total)

### Step 1: Create OAuth Client ID (2 minutes)

**Go to:** https://console.cloud.google.com/apis/credentials

**Create:**
1. Click `+ CREATE CREDENTIALS`
2. Select `OAuth client ID`
3. **Application type:** `Desktop app` ← IMPORTANT
4. Name: `BTC Trading Bot - Gmail`
5. Click `CREATE`
6. Download JSON as `gmail_credentials.json`
7. Move to `config/gmail_credentials.json`

**Why Desktop app?**
- Your bot runs locally (not a web server)
- Correct type for local Python scripts

---

### Step 2: Add Recipient Email (30 seconds)

**Edit:** `.env`

**Add:**
```env
GMAIL_RECIPIENT_EMAIL=your-email@gmail.com
```

---

### Step 3: Install Libraries (1 minute)

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

---

### Step 4: Authorize & Test (1.5 minutes)

```bash
python src/notifications/gmail_notifier.py
```

**What happens:**
1. Browser opens automatically
2. Login to Google
3. Click "Allow" for "Send email on your behalf"
4. Test email sent!

**Check your email:**
```
Subject:  BTC Trading Bot - Gmail Test
Gmail API Test Successful
```

---

## Verification

**All working if:**
- No errors in terminal
- Test email received
- Token saved to `config/gmail_token.pickle`
- Future emails don't need browser (automated)

---

## Troubleshooting

### "Credentials not found"
```bash
# Check file location
ls config/gmail_credentials.json
# Should exist
```

### "GMAIL_RECIPIENT_EMAIL not set"
```bash
# Add to .env
echo "GMAIL_RECIPIENT_EMAIL=your-email@gmail.com" >> .env
```

### "Access blocked" warning
1. Click "Advanced"
2. Click "Go to BTC Trading Bot (unsafe)"
3. This is YOUR app - safe to proceed

### Email in spam
- Mark as "Not Spam"
- Add to contacts
- Future emails → Inbox

---

## Daily Summaries

**Manual test:**
```python
from src.notifications.gmail_notifier import GmailNotifier

g = GmailNotifier()

# Sample data
g.send_daily_summary(
    portfolio={'cash': 50000, 'btc': 0.5},
    trades_today=[],
    metrics={'total_return': 5.83, 'sharpe_ratio': 0.87},
    current_price=93450
)
```

**Automatic:** See GMAIL_SETUP_GUIDE.md for scheduled summaries

---

## Gmail vs Telegram

| Feature | Telegram | Gmail |
|---------|----------|-------|
| **When** | Every trade | Daily summary |
| **Format** | Text | Rich HTML |
| **Setup** | 2 min | 5 min |
| **Content** | Trade alert | Full report |

**Use both** for best experience!

---

## What's Included in Daily Summary

**Email contains:**
- Portfolio value with color-coded returns
-  Cash + BTC breakdown
-  Sharpe ratio, drawdown, win rate
-  All trades today (BUY/SELL with prices, amounts, strategies)
- Professional formatting

---

## Next Steps

**After setup:**
1. Run backtest to generate metrics
2. Test with real data
3. Set up scheduled daily summaries (optional)

**Full guide:** [GMAIL_SETUP_GUIDE.md](GMAIL_SETUP_GUIDE.md) - Detailed 20-minute version

---

## Quick Reference

**Files created:**
```
config/
   gmail_credentials.json  ← Your OAuth credentials
   gmail_token.pickle       ← Auto-generated refresh token

.env
   GMAIL_RECIPIENT_EMAIL=your-email@gmail.com
```

**Test command:**
```bash
python src/notifications/gmail_notifier.py
```

**Import in code:**
```python
from src.notifications.gmail_notifier import GmailNotifier
gmail = GmailNotifier()
gmail.send_daily_summary(...)
```

---

**Status:** Setup Complete **Time:** 5 minutes **OAuth Type:** Desktop Application **Automated:** After first auth **Last Updated:** 2025-11-30
