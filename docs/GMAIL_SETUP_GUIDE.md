# Gmail API Setup Guide - Daily Summary Notifications

**Purpose:** Complete step-by-step guide to set up Gmail API for daily portfolio summaries

**Read time:** 20 minutes

**Last updated:** 2025-11-30

---

## What This Does

Your trading bot will send **beautiful HTML email summaries** every day with:
- Portfolio value and total return
-  Cash vs BTC breakdown
-  Performance metrics (Sharpe ratio, drawdown, win rate)
-  All trades executed today
- Professional formatting (looks like a real trading report)

**Example:**
```
Subject: BTC Trading Bot - Daily Summary 2025-11-30

Portfolio Value: $95,832.45
 +5.83% Total Return

Asset Breakdown:
- Cash: $45,123.00
- Bitcoin: 0.543210 BTC ($50,709.45)

Trades Today:
 BUY @ $93,450 - $5,000 (DCA Strategy)
```

---

## Architecture Fit

**Where Gmail Fits:**
```
Module 1 (Sentiment) 
Module 2 (Technical)  
Module 3 (ML)         > Decision Box > Execute Trade
                                                 
                                                 > Telegram (real-time)
                                                 > Gmail (daily summary)
                        > Natural Language Chat
```

**Telegram vs Gmail:**
- **Telegram**: Real-time alerts for each trade (BUY/SELL/PAUSE)
- **Gmail**: Daily summary email at end of day (full portfolio report)

---

## Prerequisites

**Before you start:**
- Trading bot working (completed QUICKSTART.md)
- Gmail account (personal or business)
- Google Cloud Console access
- ~20 minutes

**You already have:**
- Gmail API enabled (you mentioned this)
-  OAuth 2.0 Client ID (we'll create this)
-  credentials.json downloaded (we'll do this)
-  GMAIL_RECIPIENT_EMAIL in .env (we'll add this)

---

## Step 1: Create OAuth 2.0 Client ID (5 minutes)

### 1.1 Go to Google Cloud Console

**URL:** https://console.cloud.google.com/

**Navigate to:**
```
APIs & Services → Credentials
```

---

### 1.2 Create OAuth Client ID

**Click:** `+ CREATE CREDENTIALS` → `OAuth client ID`

**You'll see this form:**

---

### 1.3 Configure OAuth Consent Screen (FIRST TIME ONLY)

If you haven't configured the consent screen, you'll be prompted.

**Click:** `CONFIGURE CONSENT SCREEN`

**Fill in:**
```
User Type: External (or Internal if using Google Workspace)

App Information:
  App name: BTC Trading Bot
  User support email: your-email@gmail.com
  Developer contact: your-email@gmail.com

Scopes:
  Click "ADD OR REMOVE SCOPES"
  Search: gmail.send
  Select: .../auth/gmail.send (Send email on your behalf)
  Click "UPDATE"

Test Users:
  Add your email: your-email@gmail.com
  (This is the email that will receive daily summaries)

Save and Continue
```

**Important:**
- App stays in "Testing" mode (that's fine for personal use)
- Only test users can receive emails
- No Google verification needed for personal use

---

### 1.4 Create Desktop Application Credentials

**Back to:** `APIs & Services → Credentials → + CREATE CREDENTIALS → OAuth client ID`

**Application type:** Select `Desktop app`

**Why Desktop app?**
- Your trading bot runs locally on your computer
- Not a web app (no redirect URLs needed)
- Not a mobile app
- Desktop app is correct for local Python scripts

**Name:** `BTC Trading Bot - Gmail`

**Click:** `CREATE`

---

### 1.5 Download credentials.json

**After creation:**
- A dialog appears with Client ID and Client Secret
- **Click:** `DOWNLOAD JSON`
- Save as: `gmail_credentials.json`

**Example credentials.json:**
```json
{
  "installed": {
    "client_id": "123456789-abcdefg.apps.googleusercontent.com",
    "project_id": "btc-trading-bot-12345",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_secret": "GOCSPX-abc123def456",
    "redirect_uris": ["http://localhost"]
  }
}
```

---

### 1.6 Move credentials to config/

**Move downloaded file:**
```bash
# Windows
move gmail_credentials.json btc-intelligent-trader\config\

# Mac/Linux
mv gmail_credentials.json btc-intelligent-trader/config/
```

**Verify:**
```bash
ls config/
# Should see:
# - config_parameters.json
# - service_account.json (Google Sheets)
# - gmail_credentials.json (NEW)
```

---

## Step 2: Configure Recipient Email (1 minute)

### 2.1 Edit .env File

**Open:** `btc-intelligent-trader/.env`

**Add this line:**
```env
# Gmail Daily Summary
GMAIL_RECIPIENT_EMAIL=your-email@gmail.com
```

**Example .env:**
```env
# Telegram Notifications
TELEGRAM_BOT_TOKEN=8283300908:AAHHxyC2wYwz0EMYxqxtcM4dO3VgEpefofU
TELEGRAM_CHAT_ID=6909185216

# Gmail Daily Summary
GMAIL_RECIPIENT_EMAIL=krishna@example.com
```

**Note:** This is the email where you'll receive daily summaries

---

## Step 3: Install Required Libraries (2 minutes)

### 3.1 Install Google Auth Libraries

**Run:**
```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

**What this installs:**
- `google-auth-oauthlib`: OAuth2 authentication flow
- `google-auth-httplib2`: HTTP transport for API calls
- `google-api-python-client`: Gmail API client

**Verify installation:**
```bash
python -c "from google.oauth2.credentials import Credentials; print(' Google auth installed')"
```

---

## Step 4: Run OAuth Authorization Flow (3 minutes)

### 4.1 Test Gmail Connection

**Run:**
```bash
python src/notifications/gmail_notifier.py
```

**What happens:**

**First time:**
1. Script opens browser automatically
2. Shows Google login page
3. Select your account
4. Shows: "BTC Trading Bot wants to access your Google Account"
5. Shows permission: "Send email on your behalf"
6. Click "Allow"
7. Browser shows: "The authentication flow has completed"
8. Script saves refresh token to `config/gmail_token.pickle`
9. Sends test email

**Expected output:**
```
======================================================================
GMAIL API CONNECTION TEST
======================================================================

[GMAIL] Running OAuth authorization flow...
        A browser window will open for authorization
[GMAIL] Token saved to config/gmail_token.pickle
[GMAIL]  Authentication successful
  Recipient: your-email@gmail.com

 Sending test email...
[GMAIL]  Email sent to your-email@gmail.com

Test email sent successfully!
   Check your-email@gmail.com
```

---

### 4.2 Check Your Email

**Look for:**
```
From: your-email@gmail.com (yourself)
Subject:  BTC Trading Bot - Gmail Test

Gmail API Test Successful

Your BTC Trading Bot can now send daily summaries via Gmail!

Next steps:
- Run backtest to generate performance data
- Daily summaries will be sent automatically
- Check spam folder if you don't see emails
```

**If email is in spam:**
- Mark as "Not Spam"
- Add yourself to contacts
- Future emails will go to inbox

---

### 4.3 Subsequent Runs (No Browser)

**After first authorization:**
- Refresh token saved in `config/gmail_token.pickle`
- No browser popup needed
- Token auto-refreshes every 7 days
- Completely automated

---

## Step 5: Integration (Already Done)

Gmail notifier is ready to use. You can:

### Option A: Send Manual Summary

**Test with sample data:**
```python
from src.notifications.gmail_notifier import GmailNotifier

notifier = GmailNotifier()

# Sample portfolio data
portfolio = {
    'cash': 45123.00,
    'btc': 0.543210
}

trades_today = [
    {
        'action': 'BUY',
        'price': 93450.00,
        'amount': 5000.00,
        'strategy': 'DCA (RSI + Fear & Greed)',
        'timestamp': '2025-11-30 10:30:00'
    }
]

metrics = {
    'total_return': 5.83,
    'sharpe_ratio': 0.87,
    'max_drawdown': -15.2,
    'win_rate': 52.6,
    'total_trades': 19
}

notifier.send_daily_summary(
    portfolio=portfolio,
    trades_today=trades_today,
    metrics=metrics,
    current_price=93450.00
)
```

---

### Option B: Automatic Daily Summaries (Scheduled)

**Create scheduled job** (see SCHEDULED_SUMMARIES.md for details):

**Windows Task Scheduler:**
```
Trigger: Daily at 11:59 PM
Action: python main.py --send-daily-summary
```

**Mac/Linux Cron:**
```bash
crontab -e
# Add:
59 23 * * * cd /path/to/btc-intelligent-trader && python main.py --send-daily-summary
```

---

## Architecture Deep Dive

### Where Gmail Fits

**File:** `src/decision_box/trading_logic.py`

**Integration points:**

**Option 1: End of Trading Day**
```python
class TradingDecisionBox:
    def end_of_day_summary(self):
        """Called at end of trading day."""

        # Collect today's data
        trades_today = self._get_trades_today()
        current_metrics = self._calculate_metrics()

        # Send Gmail summary
        self.gmail.send_daily_summary(
            portfolio=self.portfolio,
            trades_today=trades_today,
            metrics=current_metrics,
            current_price=self.current_price
        )
```

---

**Option 2: After Each Trade (Daily Digest)**
```python
class TradingDecisionBox:
    def __init__(self, config, telegram_enabled=True, gmail_enabled=True):
        self.telegram = TelegramNotifier(enabled=telegram_enabled)
        self.gmail = GmailNotifier(enabled=gmail_enabled)
        self.trades_today = []  # Track trades for daily summary

    def execute_trade(self, decision, current_price):
        # Execute trade
        self._execute_buy_or_sell(decision, current_price)

        # Real-time Telegram alert
        self.telegram.notify_trade(decision, current_price)

        # Add to daily summary list
        self.trades_today.append({
            'action': decision['action'],
            'price': current_price,
            'amount': decision.get('amount', 0),
            'strategy': decision.get('strategy', 'Unknown'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
```

---

### Graceful Degradation

**Same pattern as Telegram:**
```python
# Gmail fails → Trading continues
self.gmail = GmailNotifier(enabled=gmail_enabled)

if not self.gmail.enabled:
    print("[GMAIL] Disabled - trading continues normally")

# Send email (doesn't crash if fails)
success = self.gmail.send_daily_summary(...)
# Returns True/False, doesn't raise exceptions
```

---

## Troubleshooting

### Error: "Credentials not found"

**Problem:** `gmail_credentials.json` not in `config/`

**Fix:**
```bash
# Check location
ls config/gmail_credentials.json

# If not there, re-download from Google Cloud Console
# Move to correct location
move gmail_credentials.json config/
```

---

### Error: "GMAIL_RECIPIENT_EMAIL not set"

**Problem:** Missing from .env

**Fix:**
```bash
# Edit .env
echo "GMAIL_RECIPIENT_EMAIL=your-email@gmail.com" >> .env
```

---

### Error: "Access blocked: This app isn't verified"

**Problem:** Google showing unverified app warning

**Fix:**
1. Click "Advanced"
2. Click "Go to BTC Trading Bot (unsafe)"
3. This is YOUR app, safe to proceed
4. For production: Submit app for verification (not needed for personal use)

---

### Error: "The user has not granted the app..."

**Problem:** Didn't grant "Send email" permission

**Fix:**
1. Delete `config/gmail_token.pickle`
2. Run test again: `python src/notifications/gmail_notifier.py`
3. Browser opens → Grant permission
4. Make sure to click "Allow" for "Send email on your behalf"

---

### Emails Going to Spam

**Solutions:**
1. **Mark as Not Spam**: Open spam folder → "Not Spam"
2. **Add to contacts**: Add yourself to Gmail contacts
3. **Create filter**:
   - Search: `from:your-email@gmail.com subject:"BTC Trading Bot"`
   - Create filter → "Never send to spam"

---

### Browser Not Opening (Headless Server)

**Problem:** Running on server without display

**Fix:** Run OAuth flow on local machine first:
```bash
# On local machine:
python src/notifications/gmail_notifier.py
# Browser opens, authorize, token saved

# Copy token to server:
scp config/gmail_token.pickle server:/path/to/btc-intelligent-trader/config/

# Server uses saved token (no browser needed)
```

---

### Token Expired

**Problem:** Token expires after 7 days (auto-refreshes normally)

**Fix:** Script auto-refreshes token. If fails:
```bash
# Delete old token
rm config/gmail_token.pickle

# Re-run OAuth flow
python src/notifications/gmail_notifier.py
```

---

## Security Best Practices

### 1. Credentials Files (IMPORTANT)

**Never commit to git:**
```bash
# .gitignore already includes:
config/gmail_credentials.json
config/gmail_token.pickle
.env
```

**Verify:**
```bash
git status
# Should NOT show:
# - config/gmail_credentials.json
# - config/gmail_token.pickle
# - .env
```

---

### 2. OAuth Scopes (Least Privilege)

**Current scope:** `https://www.googleapis.com/auth/gmail.send`

**What this allows:**
- Send emails on your behalf
- Cannot read your emails
- Cannot delete emails
- Cannot modify settings

**Why this is safe:**
- Minimal permissions needed
- Bot can only send, not read
- Your inbox is protected

---

### 3. Test Users

**While app in "Testing" mode:**
- Only test users can authorize
- Add trusted emails only
- Revoke access anytime: https://myaccount.google.com/permissions

---

## Email Customization

### Change Email Format

**Edit:** `src/notifications/gmail_notifier.py`

**Function:** `_build_summary_html()`

**Customize:**
```python
# Change colors
return_color = "#00C851" if total_return >= 0 else "#ff4444"

# Change subject
subject = f"Daily Summary {date.strftime('%Y-%m-%d')}"

# Add your logo
html = f"""
<img src="https://your-domain.com/logo.png" width="100">
<h1>Your Custom Title</h1>
...
"""
```

---

### Add More Metrics

**Add to summary:**
```python
def _build_summary_html(self, ...):
    # Add custom metrics
    recent_trades = metrics.get('recent_5_trades', [])
    best_strategy = metrics.get('best_strategy', 'Unknown')

    # Add to HTML
    html += f"""
    <h3>Best Strategy</h3>
    <p>{best_strategy}</p>

    <h3>Recent Trades</h3>
    <ul>
        {' '.join([f'<li>{trade}</li>' for trade in recent_trades])}
    </ul>
    """
```

---

## Gmail vs Telegram Comparison

| Feature | Telegram | Gmail |
|---------|----------|-------|
| **Timing** | Real-time (every trade) | Daily summary (end of day) |
| **Format** | Plain text | Rich HTML |
| **Content** | Single trade details | Full portfolio report |
| **Setup** | 2 minutes (bot token) | 20 minutes (OAuth flow) |
| **Notifications** | Mobile push | Email inbox |
| **Use case** | Quick alerts | Detailed analysis |

**Recommendation:** Use BOTH
- Telegram: Real-time awareness ("Just bought BTC!")
- Gmail: Daily review ("How did I do today?")

---

## What Gets Sent

### Daily Summary Includes:

**1. Portfolio Summary**
- Total portfolio value
- Total return percentage (with color coding)
- Cash balance
- Bitcoin holdings (BTC amount + USD value)

**2. Performance Metrics**
- Sharpe ratio (risk-adjusted return)
- Max drawdown (worst loss)
- Win rate (% profitable trades)
- Total trades executed

**3. Trades Today**
- All trades executed that day
- Action (BUY/SELL/PAUSE)
- Price at execution
- Amount traded
- Strategy used (DCA, Swing, Stop-loss, etc.)
- Timestamp

**4. Professional Formatting**
- Color-coded returns (green = profit, red = loss)
- Clean tables
- Icons ( BUY,  SELL, [PAUSED]PAUSE)
- Mobile-responsive HTML

---

## Testing Checklist

### Before Going Live

- [ ] `config/gmail_credentials.json` exists
- [ ] `GMAIL_RECIPIENT_EMAIL` in .env
- [ ] Google auth libraries installed
- [ ] OAuth flow completed (token saved)
- [ ] Test email received successfully
- [ ] Email NOT in spam folder
- [ ] Credentials NOT committed to git
- [ ] Trading bot integration tested

**Run all tests:**
```bash
# Test 1: Gmail connection
python src/notifications/gmail_notifier.py

# Test 2: Manual summary
python -c "
from src.notifications.gmail_notifier import GmailNotifier
g = GmailNotifier()
print('Enabled:', g.enabled)
"

# Test 3: Full integration (if implemented)
python main.py --send-daily-summary
```

---

## Summary

**You now have:**
- Gmail API configured with OAuth2
- Daily summary emails (HTML formatted)
- Secure authentication (refresh token)
- Graceful error handling
- Integration ready

**Setup time:** 20 minutes (one-time)

**Daily emails:** Automatic (after integration)

**Next steps:**
1. Run backtest to generate metrics
2. Test daily summary with real data
3. Set up scheduled job for automatic summaries

---

## Related Documentation

- **Quick start:** [GMAIL_QUICK_START.md](GMAIL_QUICK_START.md) - 5-minute version
- **Telegram setup:** [TELEGRAM_SETUP_GUIDE.md](TELEGRAM_SETUP_GUIDE.md) - Real-time alerts
- **Architecture:** [COMPLETE_WORKFLOW_WITH_NOTIFICATIONS.md](COMPLETE_WORKFLOW_WITH_NOTIFICATIONS.md)
- **Testing:** [TESTING_GUIDE.md](TESTING_GUIDE.md)

---

**Status:** Setup Complete **OAuth Type:** Desktop Application **Scope:** gmail.send (minimum required) **Security:** Credentials secured, not in git **Last Updated:** 2025-11-30
