# Google Sheets Configuration Setup Guide

This guide walks you through setting up Google Sheets as your configuration source with local fallback.

---

##  What This Does

Your trading bot now loads configuration from Google Sheets instead of hardcoded values:

```

   GOOGLE SHEETS (Primary Source)   
                                     
   Key                  | Value      
        
   initial_capital      | 10000      
   dca_buy_amount       | 0.05       
   atr_multiplier       | 2.0        
   ...                  | ...        

         ↓ (fetches every 5 min)

    YOUR TRADING BOT                 
  config/trading_config.json (cache) 

```

**Benefits**:
- Change config without redeploying code
- Share config across team members
- Offline support (local cache)
- Secure (read-only service account)

---

##  Step-by-Step Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Agree to Terms of Service (if first time)
3. Click the project dropdown at the top
4. Click **"New Project"**
5. Name it: `Trading-Bot-Config`
6. Click **"Create"**

---

### Step 2: Enable Required APIs

1. With your new project selected, go to **"APIs & Services"** > **"Library"**
2. Search for **"Google Sheets API"**
3. Click on it and click **"Enable"**
4. Also search for and enable **"Google Drive API"**

---

### Step 3: Create Service Account

1. Go to **"APIs & Services"** > **"Credentials"**
2. Click **"Create Credentials"** at the top
3. Select **"Service account"**
4. Enter name: `trading-bot-sheets-access`
5. Skip optional steps and click **"Done"**

---

### Step 4: Generate JSON Key File

1. You'll see your service account in the list
2. Click on its **email address** to open details
3. Go to the **"Keys"** tab
4. Click **"Add Key"** > **"Create new key"**
5. Select **JSON** key type
6. Click **"Create"**
7. A JSON file will download automatically
8. **IMPORTANT**: Rename it to `service_account.json`
9. Move it to: `c:\Users\krish\btc-intelligent-trader\config\service_account.json`

**Security Note**: This file is like a password. Never commit it to Git!

---

### Step 5: Create Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Click **"Blank"** to create new sheet
3. Name it: `BTC Trading Config`

**Sheet Structure** (exactly 2 columns):

| **Key** | **Value** |
|---------|-----------|
| initial_capital | 10000 |
| dca_buy_amount_percent | 0.05 |
| dca_enabled | true |
| swing_enabled | false |
| swing_buy_percent | 0.10 |
| atr_stop_loss_multiplier | 2.0 |
| stop_loss_enabled | true |
| take_profit_threshold | 0.15 |
| take_profit_enabled | true |
| max_drawdown_circuit_breaker | 0.25 |
| max_position_size | 0.95 |
| rsi_oversold | 30 |
| rsi_overbought | 70 |
| rsi_neutral_low | 40 |
| rsi_neutral_high | 60 |
| fear_greed_buy_threshold | 40 |
| fear_greed_sell_threshold | 75 |
| data_fetch_interval_seconds | 300 |
| verbose | true |
| log_level | INFO |

**Important**:
- First row MUST be header: `Key | Value`
- All config keys in **first column**
- All values in **second column**
- Sheet name doesn't matter (uses first sheet by default)

---

### Step 6: Share Sheet with Service Account

1. Open your `service_account.json` file in a text editor
2. Find the `"client_email"` field (looks like: `trading-bot-sheets-access@project.iam.gserviceaccount.com`)
3. Copy this email address
4. In your Google Sheet, click the green **"Share"** button
5. Paste the service account email
6. Set permission to **"Viewer"** (read-only is enough)
7. Click **"Send"** or **"Share"**

---

### Step 7: Get Sheet ID

1. Look at your Google Sheet URL:
   ```
   https://docs.google.com/spreadsheets/d/1abc123xyz456/edit
                                         ↑
                                    This is your Sheet ID
   ```
2. Copy the ID part between `/d/` and `/edit`
3. Open `.env` file in your project
4. Add/update this line:
   ```bash
   GOOGLE_SHEET_ID=1abc123xyz456
   ```

---

### Step 8: Install Dependencies

Run in your terminal:

```bash
pip install -r requirements.txt
```

This installs:
- `gspread` (Google Sheets API client)
- `google-auth` (Authentication)
- `google-auth-oauthlib` (OAuth support)
- `google-auth-httplib2` (HTTP client)

---

### Step 9: Test Configuration

Run the config manager test:

```bash
python -m src.config.config_manager
```

**Expected Output**:
```
============================================================
TESTING CONFIGURATION MANAGER
============================================================

[CONFIG] Fetching from Google Sheets...
[CONFIG]  Config loaded from Google Sheets

[CONFIG] Loaded configuration:
  initial_capital: 10000
  dca_buy_amount_percent: 0.05
  dca_enabled: True
  ...

[OK] Configuration manager working!
```

---

### Step 10: Run Your Trading Bot

```bash
python main.py --mode backtest
```

**Expected Output**:
```
======================================================================
BTC INTELLIGENT TRADER
======================================================================

[INFO] Loading configuration...
[CONFIG] Fetching from Google Sheets...
[CONFIG]  Config loaded from Google Sheets
[OK] Configuration loaded
     Initial Capital: $10,000
     DCA Enabled: True
     Swing Enabled: False

STEP 1: LOADING HISTORICAL DATA
...
```

---

##  Configuration Keys Explained

### Capital
- `initial_capital`: Starting capital in USD (e.g., `10000`)

### DCA Strategy
- `dca_buy_amount_percent`: Percentage of capital per DCA buy (e.g., `0.05` = 5%)
- `dca_enabled`: Enable/disable DCA (`true` or `false`)

### Swing Strategy
- `swing_enabled`: Enable/disable swing trading (`true` or `false`)
- `swing_buy_percent`: Percentage for swing trades (e.g., `0.10` = 10%)

### Stop-Loss
- `atr_stop_loss_multiplier`: ATR multiplier for stop-loss (e.g., `2.0`)
- `stop_loss_enabled`: Enable/disable stop-loss (`true` or `false`)

### Take Profit
- `take_profit_threshold`: Profit threshold to take profit (e.g., `0.15` = 15%)
- `take_profit_enabled`: Enable/disable take profit (`true` or `false`)

### Risk Management
- `max_drawdown_circuit_breaker`: Max drawdown before pausing (e.g., `0.25` = 25%)
- `max_position_size`: Max position as % of capital (e.g., `0.95` = 95%)

### Technical Indicators
- `rsi_oversold`: RSI level considered oversold (e.g., `30`)
- `rsi_overbought`: RSI level considered overbought (e.g., `70`)
- `rsi_neutral_low`: RSI neutral range low (e.g., `40`)
- `rsi_neutral_high`: RSI neutral range high (e.g., `60`)

### Sentiment
- `fear_greed_buy_threshold`: Buy below this F&G value (e.g., `40`)
- `fear_greed_sell_threshold`: Sell above this F&G value (e.g., `75`)

### Data Fetching
- `data_fetch_interval_seconds`: How often to fetch new data (e.g., `300` = 5 min)

### Logging
- `verbose`: Enable verbose logging (`true` or `false`)
- `log_level`: Logging level (`INFO`, `DEBUG`, `WARNING`, `ERROR`)

---

## [REFRESH]Fallback Chain

Your bot uses this fallback chain:

1. **Google Sheets** (if available and cache < 5 min old)
2. **Local Cache** (`config/trading_config.json`)
3. **Hardcoded Defaults** (in `config_manager.py`)

**Examples**:

### Scenario 1: Normal Operation
```
[CONFIG] Using local cache (fresh)
```
→ Cache is < 5 min old, uses cached values

### Scenario 2: Cache Stale
```
[CONFIG] Fetching from Google Sheets...
[CONFIG]  Config loaded from Google Sheets
```
→ Cache > 5 min old, fetches fresh from Sheets

### Scenario 3: No Internet
```
[CONFIG] [WARNING]Failed to fetch from Google Sheets: Connection error
[CONFIG] Using local cache (fallback)
```
→ Can't reach Sheets, uses stale cache

### Scenario 4: First Run (No Cache)
```
[CONFIG] Fetching from Google Sheets...
[CONFIG]  Config loaded from Google Sheets
```
→ No cache exists, fetches from Sheets and creates cache

### Scenario 5: Offline + No Cache
```
[CONFIG] [WARNING]Failed to fetch from Google Sheets: Connection error
[CONFIG] [WARNING]Using hardcoded defaults (no cache available)
```
→ Last resort: uses defaults from code

---

##  Security Best Practices

### DO
- Keep `service_account.json` in `.gitignore`
- Share Sheet with **Viewer** permission only (read-only)
- Rotate service account keys periodically
- Use environment variables for Sheet ID

### DON'T
- Commit `service_account.json` to Git
- Give service account **Editor** permission (unless needed)
- Share service account JSON publicly
- Hardcode Sheet ID in code (use `.env`)

---

##  Troubleshooting

### Error: "gspread not installed"

**Solution**:
```bash
pip install gspread google-auth
```

---

### Error: "Service account file not found"

**Solution**:
1. Check file is at: `config/service_account.json`
2. Verify file name is exactly `service_account.json`
3. Ensure it's a valid JSON file (open in text editor)

---

### Error: "GOOGLE_SHEET_ID not set in .env"

**Solution**:
1. Open `.env` file
2. Add line: `GOOGLE_SHEET_ID=your_sheet_id_here`
3. Get ID from Sheet URL: `https://docs.google.com/spreadsheets/d/YOUR_ID/edit`

---

### Error: "Failed to fetch from Google Sheets: 403 Forbidden"

**Solution**:
1. Check you shared the Sheet with the service account email
2. Verify permission is **Viewer** or **Editor**
3. Ensure APIs are enabled in Google Cloud Console

---

### Error: "Failed to fetch from Google Sheets: Connection error"

**Solution**:
- Check your internet connection
- Bot will use local cache if available
- If no cache, will use hardcoded defaults

---

## Testing Different Configs

You can test different configurations easily:

1. **Update Google Sheet** (change values)
2. **Wait 5 minutes** (or force refresh)
3. **Run bot again**

**Force refresh** (ignore cache):
```python
from src.config.config_manager import ConfigManager

config_mgr = ConfigManager()
config = config_mgr.get_config(force_remote=True)  # Force fetch from Sheets
```

---

## Next Steps

1. Test configuration loading works
2. Run a backtest with your config
3. Modify values in Google Sheet
4. Run backtest again to see changes
5. Share Sheet with team members (if applicable)

---

##  Additional Resources

- [Google Sheets API Docs](https://developers.google.com/sheets/api)
- [gspread Documentation](https://docs.gspread.org/)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)

---

##  You're Done!

Your trading bot now uses Google Sheets for configuration management with robust fallback support.

**Benefits you now have**:
- Change config without code changes
- Team collaboration (shared config)
- Offline support (local cache)
- Secure (read-only access)
- Version control (Sheet history)
- Easy rollback (revert Sheet changes)

Happy trading! 