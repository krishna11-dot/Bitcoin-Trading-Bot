# GCP Deployment Guide - BTC Intelligent Trader

## 🎁 GCP Free Trial Overview

**What You Get**:
- **$300 free credits** valid for 90 days
- Access to all GCP services
- No automatic charges after trial (requires explicit upgrade)
- Perfect for running your trading bot 24/7

**Free Tier (Always Free - even after trial)**:
- 1 f1-micro VM instance per month (US regions only)
- 30 GB standard persistent disk storage
- 1 GB network egress per month

---

## 📋 Prerequisites

Before starting, ensure you have:
- [ ] Google account
- [ ] Credit/debit card (for verification, won't be charged)
- [ ] Your trading bot code ready
- [ ] `.env` file with all credentials configured

---

## 🚀 Deployment Methods Comparison

### Method 1: Compute Engine VM (Recommended for 24/7 Trading)
**Best for**: Continuous trading bot operation

| Pros | Cons |
|------|------|
| ✅ Full control over environment | ❌ Requires manual setup |
| ✅ Can run 24/7 | ❌ Need to manage OS updates |
| ✅ SSH access for debugging | ❌ Pays for idle time |
| ✅ Always-free tier available (f1-micro) | ❌ More complex than serverless |

**Cost**: Free tier f1-micro or ~$5-15/month for e2-micro

---

### Method 2: Cloud Run (Best for Scheduled Backtests)
**Best for**: Running backtests on schedule, not live trading

| Pros | Cons |
|------|------|
| ✅ Serverless (no VM management) | ❌ Not suitable for 24/7 live trading |
| ✅ Pay only when running | ❌ Max 60 min execution time |
| ✅ Auto-scaling | ❌ Cold starts possible |
| ✅ Easy deployment | ❌ Stateless (can't maintain portfolio state) |

**Cost**: Pay per request, very cheap for occasional runs

---

### Method 3: Kubernetes (GKE) - Advanced
**Best for**: Production-grade deployments with high availability

| Pros | Cons |
|------|------|
| ✅ Auto-scaling | ❌ Complex setup |
| ✅ High availability | ❌ Expensive ($70+/month) |
| ✅ Professional-grade | ❌ Overkill for single bot |

**Cost**: Not recommended for personal trading bot (too expensive)

---

## 🎯 Recommended: Compute Engine VM (24/7 Trading Bot)

This guide focuses on **Compute Engine VM** as it's best for continuous trading.

---

## Step 1: Activate GCP Free Trial

### 1.1 Sign Up for GCP

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Get started for free"**
3. Sign in with your Google account
4. Fill in:
   - Country
   - Terms of Service (accept)
   - Email preferences

### 1.2 Verify Identity

1. Choose **Account type**: Individual
2. Enter personal information:
   - Name
   - Address
   - Phone number
3. Add payment method (credit/debit card)
   - **Note**: You won't be charged unless you manually upgrade
   - Required for verification only

### 1.3 Activate Trial

1. Click **"Start my free trial"**
2. Confirm $300 credit activation
3. You'll see **"$300 credit available"** in the top banner

**✅ Free Trial Active!**

---

## Step 2: Create a New Project

### 2.1 Create Project

1. In GCP Console, click **project dropdown** (top bar)
2. Click **"New Project"**
3. Enter details:
   - **Project name**: `btc-trading-bot`
   - **Project ID**: `btc-trading-bot-12345` (auto-generated)
   - **Location**: No organization
4. Click **"Create"**

### 2.2 Enable Billing

1. Go to **Billing** → **Account Management**
2. Link your project to the free trial billing account
3. Verify **$300 credit** is showing

---

## Step 3: Set Up Compute Engine VM

### 3.1 Enable Compute Engine API

1. Go to **Compute Engine** → **VM instances**
2. Click **"Enable Compute Engine API"** (first time only)
3. Wait 1-2 minutes for activation

### 3.2 Create VM Instance

1. Click **"Create Instance"**

2. **Configure instance**:

   **Basic Info**:
   - **Name**: `btc-trader-vm`
   - **Region**: `us-central1` (Iowa - cheapest, has free tier)
   - **Zone**: `us-central1-a`

   **Machine Configuration**:
   - **Series**: E2
   - **Machine type**:
     - **Free Tier**: `e2-micro` (2 vCPU, 1 GB RAM) - $0/month for 1 instance
     - **Recommended**: `e2-small` (2 vCPU, 2 GB RAM) - ~$13/month

   **Boot Disk**:
   - Click **"Change"**
   - **Operating System**: Ubuntu
   - **Version**: Ubuntu 22.04 LTS
   - **Boot disk type**: Standard persistent disk
   - **Size**: 30 GB (free tier includes 30 GB)
   - Click **"Select"**

   **Firewall**:
   - ☑️ Allow HTTP traffic
   - ☑️ Allow HTTPS traffic

3. Click **"Create"**

**Wait 1-2 minutes** for VM to start.

### 3.3 Connect to VM via SSH

#### Option A: Browser SSH (Easiest)

1. In **VM instances** list, click **SSH** button next to your VM
2. Browser-based terminal opens automatically

#### Option B: gcloud CLI (Advanced)

```bash
# Install gcloud CLI first
gcloud compute ssh btc-trader-vm --zone=us-central1-a
```

**✅ You're now connected to your VM!**

---

## Step 4: Set Up Python Environment on VM

### 4.1 Update System

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv git -y

# Verify installation
python3 --version  # Should show Python 3.10+
pip3 --version
```

### 4.2 Clone Your Repository

```bash
# Navigate to home directory
cd ~

# Clone your GitHub repo (if public)
git clone https://github.com/your-username/btc-intelligent-trader.git

# Or upload your code via SCP/SFTP (if private)
# We'll cover uploading files in Step 5
```

### 4.3 Create Virtual Environment

```bash
cd btc-intelligent-trader

# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

---

## Step 5: Upload Your Code & Credentials

### Method 1: Upload via gcloud CLI (Recommended)

#### 5.1 Install gcloud on Your Local Machine

**Windows**:
```powershell
# Download and run installer
# https://cloud.google.com/sdk/docs/install
```

**Mac/Linux**:
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

#### 5.2 Upload Files

```bash
# From your local machine (PowerShell/Terminal)

# Upload entire project
gcloud compute scp --recurse <your-project-directory> btc-trader-vm:~/btc-intelligent-trader --zone=us-central1-a

# Or upload just .env file
gcloud compute scp .env btc-trader-vm:~/btc-intelligent-trader/.env --zone=us-central1-a

# Upload config files
gcloud compute scp config/gmail_credentials.json btc-trader-vm:~/btc-intelligent-trader/config/ --zone=us-central1-a
gcloud compute scp config/service_account.json btc-trader-vm:~/btc-intelligent-trader/config/ --zone=us-central1-a
```

### Method 2: Upload via GitHub (If Public Repo)

```bash
# On VM
cd ~
git clone https://github.com/your-username/btc-intelligent-trader.git
cd btc-intelligent-trader

# Create .env manually
nano .env
# Paste your .env contents
# Ctrl+X, Y, Enter to save
```

### Method 3: Upload via Browser (Small Files)

1. In SSH terminal, click **gear icon** → **Upload file**
2. Select `.env` file from your computer
3. Move to correct location:
```bash
mv .env ~/btc-intelligent-trader/.env
```

---

## Step 6: Configure Environment Variables

### 6.1 Create .env File

```bash
cd ~/btc-intelligent-trader

# Create .env
nano .env
```

**Paste your credentials** (example):
```env
# Trading APIs
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here

# Gemini API
GEMINI_API_KEY=your_gemini_key

# Google Sheets
GOOGLE_SHEET_ID=your_sheet_id

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Gmail
GMAIL_RECIPIENT_EMAIL=your_email@gmail.com

# Trading Parameters
INITIAL_CAPITAL=10000
DCA_AMOUNT=100
SWING_AMOUNT=500
RSI_OVERSOLD=30
RSI_OVERBOUGHT=70
K_ATR=2.0
FEAR_THRESHOLD=40
RAG_CONFIDENCE_THRESHOLD=0.70
```

**Save**: `Ctrl+X`, `Y`, `Enter`

### 6.2 Verify .env

```bash
cat .env  # Check contents
```

---

## Step 7: Test Your Bot

### 7.1 Run Backtest

```bash
cd ~/btc-intelligent-trader
source venv/bin/activate

# Run backtest
python main.py --mode backtest --months 3
```

**Expected output**: Backtest results with performance metrics

### 7.2 Test API Connections

```bash
python main.py --mode test-apis
```

**Expected output**:
```
[OK] Current BTC Price: $XX,XXX.XX
[OK] Fear & Greed: 45/100 (Neutral)
```

### 7.3 Test Live Trading (Testnet)

```bash
# Run for 5 minutes to test
timeout 300 python main.py --mode live
```

**✅ If all tests pass, proceed to 24/7 deployment!**

---

## Step 8: Deploy as 24/7 Service

### 8.1 Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/btc-trader.service
```

**Paste this configuration**:
```ini
[Unit]
Description=BTC Intelligent Trading Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/btc-intelligent-trader
Environment="PATH=/home/YOUR_USERNAME/btc-intelligent-trader/venv/bin"
ExecStart=/home/YOUR_USERNAME/btc-intelligent-trader/venv/bin/python main.py --mode live
Restart=always
RestartSec=10
StandardOutput=append:/home/YOUR_USERNAME/btc-intelligent-trader/logs/trading.log
StandardError=append:/home/YOUR_USERNAME/btc-intelligent-trader/logs/error.log

[Install]
WantedBy=multi-user.target
```

**Replace `YOUR_USERNAME`** with your actual username:
```bash
whoami  # Get your username
```

**Save**: `Ctrl+X`, `Y`, `Enter`

### 8.2 Create Logs Directory

```bash
cd ~/btc-intelligent-trader
mkdir -p logs
```

### 8.3 Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable btc-trader.service

# Start service
sudo systemctl start btc-trader.service

# Check status
sudo systemctl status btc-trader.service
```

**Expected output**:
```
● btc-trader.service - BTC Intelligent Trading Bot
     Loaded: loaded (/etc/systemd/system/btc-trader.service; enabled)
     Active: active (running) since ...
```

### 8.4 Monitor Logs

```bash
# View live logs
tail -f ~/btc-intelligent-trader/logs/trading.log

# View last 50 lines
tail -n 50 ~/btc-intelligent-trader/logs/trading.log

# View errors
tail -f ~/btc-intelligent-trader/logs/error.log
```

**✅ Your bot is now running 24/7!**

---

## Step 9: Service Management Commands

### Check Service Status
```bash
sudo systemctl status btc-trader.service
```

### Stop Service
```bash
sudo systemctl stop btc-trader.service
```

### Restart Service
```bash
sudo systemctl restart btc-trader.service
```

### View Logs
```bash
# Live logs
journalctl -u btc-trader.service -f

# Last 100 lines
journalctl -u btc-trader.service -n 100
```

### Disable Service (stop auto-start)
```bash
sudo systemctl disable btc-trader.service
```

---

## Step 10: Set Up Monitoring & Alerts

### 10.1 Create Monitoring Script

```bash
nano ~/monitor_bot.sh
```

**Paste**:
```bash
#!/bin/bash

# Check if bot is running
if systemctl is-active --quiet btc-trader.service; then
    echo "✅ Bot is running"

    # Show recent logs
    echo "Recent activity:"
    tail -n 5 ~/btc-intelligent-trader/logs/trading.log
else
    echo "❌ Bot is DOWN! Restarting..."
    sudo systemctl restart btc-trader.service
fi

# Show system resources
echo ""
echo "System Resources:"
free -h
df -h /
```

**Make executable**:
```bash
chmod +x ~/monitor_bot.sh
```

**Run monitor**:
```bash
./monitor_bot.sh
```

### 10.2 Set Up Daily Email Reports

Already built into your bot! Ensure Gmail is configured:

```bash
# Verify Gmail credentials exist
ls ~/btc-intelligent-trader/config/gmail_credentials.json
```

---

## Step 11: Firewall & Security

### 11.1 Configure Firewall

```bash
# Enable firewall
sudo ufw enable

# Allow SSH (important!)
sudo ufw allow 22/tcp

# Check status
sudo ufw status
```

### 11.2 Secure Your .env File

```bash
# Set restrictive permissions
chmod 600 ~/btc-intelligent-trader/.env

# Verify
ls -la ~/btc-intelligent-trader/.env
# Should show: -rw------- (only owner can read/write)
```

### 11.3 Set Up SSH Key Authentication (Optional but Recommended)

```bash
# On your local machine, generate SSH key
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Copy to GCP VM
gcloud compute ssh btc-trader-vm --zone=us-central1-a -- "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys" < ~/.ssh/id_rsa.pub
```

---

## Step 12: Cost Optimization

### 12.1 Use Always-Free Tier

**Free Tier VM (e2-micro)**:
- 1 instance per month (US regions only)
- 30 GB standard persistent disk
- Perfect for your trading bot

**To use free tier**:
1. **Region**: Must be in `us-west1`, `us-central1`, or `us-east1`
2. **Machine type**: `e2-micro`
3. **Disk**: 30 GB standard persistent disk

**Cost**: $0/month (always free)

### 12.2 Monitor Costs

1. Go to **Billing** → **Reports**
2. Check daily spend
3. Set up budget alerts:
   - **Billing** → **Budgets & alerts**
   - Set budget: $10/month
   - Alert at: 50%, 90%, 100%

### 12.3 Stop VM When Not Needed

```bash
# Stop VM (disk persists, no compute charges)
gcloud compute instances stop btc-trader-vm --zone=us-central1-a

# Start VM again
gcloud compute instances start btc-trader-vm --zone=us-central1-a
```

**Cost when stopped**: ~$1.20/month (disk storage only)

---

## Step 13: Backup & Disaster Recovery

### 13.1 Create VM Snapshot

```bash
# Create snapshot
gcloud compute disks snapshot btc-trader-vm --snapshot-names=btc-trader-backup-$(date +%Y%m%d) --zone=us-central1-a
```

**Cost**: $0.026 per GB/month (~$0.78/month for 30 GB)

### 13.2 Backup .env to Secret Manager (Advanced)

```bash
# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Create secret from .env
gcloud secrets create btc-trading-env --data-file=.env

# Retrieve secret later
gcloud secrets versions access latest --secret=btc-trading-env
```

---

## Step 14: Update Your Bot Code

### 14.1 Pull Latest Changes from GitHub

```bash
# SSH into VM
gcloud compute ssh btc-trader-vm --zone=us-central1-a

# Navigate to project
cd ~/btc-intelligent-trader

# Stop service
sudo systemctl stop btc-trader.service

# Pull latest code
git pull origin main

# Restart service
sudo systemctl start btc-trader.service

# Verify
sudo systemctl status btc-trader.service
```

### 14.2 Manual Code Update (Without Git)

```bash
# From local machine, upload updated files
gcloud compute scp --recurse src/ btc-trader-vm:~/btc-intelligent-trader/src/ --zone=us-central1-a

# SSH to VM
gcloud compute ssh btc-trader-vm --zone=us-central1-a

# Restart service
sudo systemctl restart btc-trader.service
```

---

## Alternative: Cloud Run Deployment (For Scheduled Backtests)

If you want to run backtests on schedule (not 24/7 live trading):

### Step 1: Create Dockerfile

```dockerfile
# Create: Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py", "--mode", "backtest", "--months", "6"]
```

### Step 2: Deploy to Cloud Run

```bash
# Build and deploy
gcloud run deploy btc-trader \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="$(cat .env | grep -v '^#' | xargs)"
```

### Step 3: Schedule with Cloud Scheduler

```bash
# Create weekly backtest schedule
gcloud scheduler jobs create http weekly-backtest \
  --schedule="0 0 * * 0" \
  --uri="https://btc-trader-xxx.run.app" \
  --http-method=GET
```

**Cost**: Pay only when running (~$0.01 per backtest)

---

## 💰 Cost Breakdown (Estimated)

### Option 1: Free Tier (e2-micro)
| Service | Cost |
|---------|------|
| e2-micro VM (US regions) | **$0/month** (always free) |
| 30 GB disk | **$0/month** (included in free tier) |
| Networking | **$0/month** (1 GB free egress) |
| **Total** | **$0/month** |

**Limitations**:
- Limited RAM (1 GB) - may struggle with ML models
- Limited CPU - slower backtests

### Option 2: e2-small (Recommended)
| Service | Cost |
|---------|------|
| e2-small VM (2 vCPU, 2 GB RAM) | **$13/month** |
| 30 GB disk | **$1.20/month** |
| Networking | **$0/month** |
| **Total** | **~$14/month** |

**With $300 credit**: Runs for 21 months free!

### Option 3: e2-medium (High Performance)
| Service | Cost |
|---------|------|
| e2-medium VM (2 vCPU, 4 GB RAM) | **$26/month** |
| 30 GB disk | **$1.20/month** |
| **Total** | **~$27/month** |

**With $300 credit**: Runs for 11 months free!

---

## 🔧 Troubleshooting

### Bot Not Starting

```bash
# Check logs
journalctl -u btc-trader.service -n 50

# Check Python errors
tail -f ~/btc-intelligent-trader/logs/error.log

# Test manually
cd ~/btc-intelligent-trader
source venv/bin/activate
python main.py --mode live
```

### SSH Connection Issues

```bash
# Reset firewall
gcloud compute firewall-rules create allow-ssh --allow tcp:22

# Use browser SSH
# Click SSH button in GCP Console
```

### Out of Memory

```bash
# Check memory usage
free -h

# Upgrade to larger VM
gcloud compute instances set-machine-type btc-trader-vm --machine-type=e2-small --zone=us-central1-a
```

### Disk Full

```bash
# Check disk usage
df -h

# Clean up logs
cd ~/btc-intelligent-trader/logs
rm -f trading.log.* error.log.*
```

---

## 📊 Monitoring Dashboard

### Set Up Uptime Checks

1. Go to **Monitoring** → **Uptime checks**
2. Click **Create Uptime Check**
3. Configure:
   - **Title**: BTC Trader Health Check
   - **Protocol**: TCP
   - **Port**: 22
   - **Check frequency**: 5 minutes
4. Set up alerts for downtime

---

## 🎯 Quick Reference Commands

```bash
# SSH to VM
gcloud compute ssh btc-trader-vm --zone=us-central1-a

# Upload file
gcloud compute scp <local-file> btc-trader-vm:~/<remote-path> --zone=us-central1-a

# Check bot status
sudo systemctl status btc-trader.service

# View logs
tail -f ~/btc-intelligent-trader/logs/trading.log

# Restart bot
sudo systemctl restart btc-trader.service

# Stop VM (save costs)
gcloud compute instances stop btc-trader-vm --zone=us-central1-a

# Start VM
gcloud compute instances start btc-trader-vm --zone=us-central1-a
```

---

## ✅ Final Checklist

- [ ] GCP free trial activated ($300 credit)
- [ ] VM instance created and running
- [ ] Python environment set up
- [ ] Code uploaded to VM
- [ ] .env file configured
- [ ] Bot tested (backtest, test-apis, live)
- [ ] Systemd service created and enabled
- [ ] Logs directory created
- [ ] Monitoring script set up
- [ ] Firewall configured
- [ ] Cost alerts set up
- [ ] Backup/snapshot created

---

## 🚀 You're Done!

Your BTC trading bot is now:
- ✅ Running 24/7 on GCP
- ✅ Auto-restarts on failure
- ✅ Sends Telegram notifications
- ✅ Sends daily Gmail summaries
- ✅ Costs $0-15/month (or free with trial)
- ✅ Accessible via SSH from anywhere

**Next steps**:
1. Monitor logs daily for first week
2. Check Telegram notifications working
3. Verify Gmail daily summaries
4. Review GCP billing dashboard weekly

**Happy Trading! 🎉**
