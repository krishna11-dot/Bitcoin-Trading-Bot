# GCP Deployment Quick Start (30 Minutes)

This is a condensed version of the full deployment guide. For detailed instructions, see [docs/GCP_DEPLOYMENT_GUIDE.md](docs/GCP_DEPLOYMENT_GUIDE.md).

## Overview

Deploy your BTC trading bot to GCP in 30 minutes using **$300 free trial credit**.

**Cost**: $0-15/month (free tier available)

---

## 🚀 Quick Setup (5 Steps)

### Step 1: Activate GCP Free Trial (5 min)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Get started for free"**
3. Add payment method (for verification only, won't be charged)
4. Activate **$300 credit**
5. Create new project: `btc-trading-bot`

---

### Step 2: Create VM Instance (3 min)

1. Go to **Compute Engine** → **VM instances**
2. Click **"Create Instance"**
3. Configure:
   - **Name**: `btc-trader-vm`
   - **Region**: `us-central1` (Iowa)
   - **Machine type**: `e2-small` (2 GB RAM, ~$13/month)
   - **Boot disk**: Ubuntu 22.04 LTS, 30 GB
4. Click **"Create"**

**Free Option**: Use `e2-micro` (1 GB RAM) for $0/month in US regions

---

### Step 3: Set Up Environment (10 min)

#### 3.1 Connect via SSH

Click **SSH** button next to your VM in GCP Console.

#### 3.2 Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python & Git
sudo apt install python3 python3-pip python3-venv git -y

# Clone your repo (or upload code)
cd ~
git clone https://github.com/your-username/btc-intelligent-trader.git
cd btc-intelligent-trader

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3.3 Upload .env File

**Option A**: Upload via gcloud (from your local machine)

```bash
# Install gcloud CLI first
gcloud compute scp .env btc-trader-vm:~/btc-intelligent-trader/.env --zone=us-central1-a
```

**Option B**: Create manually on VM

```bash
nano .env
# Paste your .env contents
# Ctrl+X, Y, Enter to save
```

---

### Step 4: Create 24/7 Service (5 min)

```bash
# Create service file
sudo nano /etc/systemd/system/btc-trader.service
```

**Paste this** (replace `YOUR_USERNAME` with output of `whoami`):

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

**Enable and start service**:

```bash
# Create logs directory
mkdir -p ~/btc-intelligent-trader/logs

# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable btc-trader.service

# Start service
sudo systemctl start btc-trader.service

# Check status
sudo systemctl status btc-trader.service
```

**✅ Your bot is now running 24/7!**

---

### Step 5: Monitor Logs (2 min)

```bash
# View live logs
tail -f ~/btc-intelligent-trader/logs/trading.log

# View last 50 lines
tail -n 50 ~/btc-intelligent-trader/logs/trading.log

# Check service status
sudo systemctl status btc-trader.service
```

---

## 🛠️ Essential Commands

### Service Management

```bash
# Check status
sudo systemctl status btc-trader.service

# Restart bot
sudo systemctl restart btc-trader.service

# Stop bot
sudo systemctl stop btc-trader.service

# View logs
tail -f ~/btc-intelligent-trader/logs/trading.log
```

### Update Code

```bash
# SSH to VM
gcloud compute ssh btc-trader-vm --zone=us-central1-a

# Stop service
sudo systemctl stop btc-trader.service

# Pull latest code
cd ~/btc-intelligent-trader
git pull origin main

# Restart service
sudo systemctl start btc-trader.service
```

### Upload Files

```bash
# From your local machine
gcloud compute scp <local-file> btc-trader-vm:~/btc-intelligent-trader/ --zone=us-central1-a
```

---

## 💰 Cost Optimization

### Free Tier (Always Free)

Use these settings for **$0/month**:
- **Region**: `us-central1`, `us-west1`, or `us-east1`
- **Machine type**: `e2-micro`
- **Disk**: 30 GB standard persistent disk

**Limitation**: Only 1 GB RAM (may struggle with ML models)

### Recommended (Low Cost)

- **Machine type**: `e2-small` (~$13/month)
- Better performance for ML models
- Runs for 21 months with $300 credit

### Stop VM When Not Needed

```bash
# Stop VM (saves ~90% cost)
gcloud compute instances stop btc-trader-vm --zone=us-central1-a

# Start VM again
gcloud compute instances start btc-trader-vm --zone=us-central1-a
```

**Cost when stopped**: ~$1.20/month (disk storage only)

---

## 🔧 Troubleshooting

### Bot Not Starting

```bash
# Check logs
journalctl -u btc-trader.service -n 50

# Test manually
cd ~/btc-intelligent-trader
source venv/bin/activate
python main.py --mode test-apis
```

### Out of Memory (e2-micro)

Upgrade to larger VM:

```bash
# Stop VM first
gcloud compute instances stop btc-trader-vm --zone=us-central1-a

# Resize
gcloud compute instances set-machine-type btc-trader-vm \
  --machine-type=e2-small --zone=us-central1-a

# Start again
gcloud compute instances start btc-trader-vm --zone=us-central1-a
```

---

## ✅ Final Checklist

- [ ] GCP free trial activated ($300 credit)
- [ ] VM created (e2-small or e2-micro)
- [ ] Code uploaded
- [ ] .env configured
- [ ] Service running (`systemctl status btc-trader.service`)
- [ ] Telegram notifications working
- [ ] Logs visible (`tail -f logs/trading.log`)

---

## 📚 Next Steps

1. **Monitor first 24 hours**: Check logs hourly
2. **Set up cost alerts**: Billing → Budgets ($10/month)
3. **Enable backups**: Create VM snapshot weekly
4. **Review full guide**: [docs/GCP_DEPLOYMENT_GUIDE.md](docs/GCP_DEPLOYMENT_GUIDE.md)

---

## 🎯 Resources

- **Full Guide**: [GCP_DEPLOYMENT_GUIDE.md](docs/GCP_DEPLOYMENT_GUIDE.md)
- **GCP Console**: https://console.cloud.google.com/
- **GCP Free Tier**: https://cloud.google.com/free
- **gcloud CLI Docs**: https://cloud.google.com/sdk/docs

**Happy Trading! 🚀**
