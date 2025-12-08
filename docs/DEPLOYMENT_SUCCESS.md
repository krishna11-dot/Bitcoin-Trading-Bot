# GCP Cloud Deployment - SUCCESS! 

**Deployment Date**: December 8, 2025
**Author**: Krishna Nair
**Platform**: Google Cloud Platform (GCP)
**VM Instance**: btc-trader-vm (us-central1-a)
**OS**: Ubuntu 22.04 LTS (Linux)
**Status**:  DEPLOYED & RUNNING 24/7

**Repository**: https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System

---

## Deployment Summary

| Component | Status | Details |
|-----------|--------|---------|
| **VM Instance** |  Running | e2-small (2 vCPUs, 2 GB RAM) |
| **Operating System** |  Linux | Ubuntu 22.04 LTS Minimal |
| **Python Version** |  3.10.12 | With venv virtual environment |
| **Bot Mode** |  Chat | Natural language interface |
| **Background Process** |  tmux | Persistent session "trading-bot" |
| **Data Loaded** |  2,686 rows | Bitcoin historical data (2018-2025) |
| **APIs Connected** |  Working | CoinGecko MCP, Fear & Greed Index |
| **Cost** |  Free tier | Using $300 GCP credit (~$0.02/hour) |

---

## Complete SSH Command History (Step-by-Step)

This is the **exact sequence of Linux commands** used to deploy the bot to GCP.

---

### **Step 1: Connect to GCP VM via SSH**

**Action**: Opened GCP Console in browser and clicked SSH button

**Location**: https://console.cloud.google.com/compute/instances

**Result**: Terminal opened with:
```
krishnanair041@btc-trader-vm:~$
```

**What this means**: Connected to Ubuntu Linux VM in the cloud (NOT local machine!)

**Verification command**:
```bash
curl ifconfig.me
```
**Output**: Shows VM's public IP (proves you're on GCP cloud server)

---

### **Step 2: Update System Packages (Linux Package Manager)**

```bash
# Command 1: Update package list
sudo apt update
```
**What this does**: Checks for new versions of software packages
**Output**: `Reading package lists... Done`

```bash
# Command 2: Upgrade installed packages
sudo apt upgrade -y
```
**What this does**: Installs security updates and bug fixes
**The `-y` flag**: Auto-confirms "yes" to all prompts

```bash
# Command 3: Install Python, Git, and tools
sudo apt install python3.11 python3.11-venv python3-pip git nano -y
```
**What this does**:
- `python3.11`: Programming language
- `python3.11-venv`: Virtual environment tool
- `python3-pip`: Package installer for Python
- `git`: Version control system
- `nano`: Text editor for Linux
- `-y`: Auto-confirm installation

**Verify Python installed**:
```bash
python3 --version
```
**Output**: `Python 3.10.12` (Ubuntu 22.04 default)

---

### **Step 3: Clone GitHub Repository (Git Command)**

```bash
# Command 1: Navigate to home directory
cd ~
```
**What this does**: Moves to `/home/krishnanair041/`
**The `~` symbol**: Shortcut for home directory

```bash
# Command 2: Clone repository from GitHub
git clone https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System.git
```
**What this does**: Downloads entire repository from GitHub to VM
**Output**:
```
Cloning into 'Bitcoin-Trading-Bot-System'...
remote: Enumerating objects: 150, done.
Receiving objects: 100% (150/150), done.
```

```bash
# Command 3: Enter project directory
cd Bitcoin-Trading-Bot-System
```
**What this does**: Changes working directory to project folder

```bash
# Command 4: Verify files downloaded
ls -la
```
**What this does**:
- `ls`: List files
- `-l`: Long format (shows permissions, size, date)
- `-a`: Show all files (including hidden files like `.gitignore`)

**Output**: Shows `README.md`, `main.py`, `src/`, `tests/`, `.gitignore`, etc.

---

### **Step 4: Create Python Virtual Environment**

```bash
# Command 1: Create virtual environment
python3 -m venv venv
```
**What this does**:
- `-m venv`: Run venv module
- `venv`: Name of virtual environment folder
- Creates isolated Python environment (doesn't affect system Python)

```bash
# Command 2: Activate virtual environment
source venv/bin/activate
```
**What this does**:
- `source`: Executes the activation script
- Switches to isolated Python environment
**Result**: Prompt changes to `(venv) krishnanair041@btc-trader-vm:~/Bitcoin-Trading-Bot-System$`
**The `(venv)` prefix**: Shows virtual environment is active

```bash
# Command 3: Upgrade pip (Python package installer)
pip install --upgrade pip
```
**What this does**: Updates pip to latest version
**Output**: `Successfully installed pip-24.x.x`

```bash
# Command 4: Install all Python dependencies
pip install -r requirements.txt
```
**What this does**: Reads `requirements.txt` and installs all packages
**Takes**: 2-3 minutes
**Installs**: pandas, numpy, scikit-learn, langgraph, chromadb, google-generativeai, sentence-transformers, etc.
**Output**: `Successfully installed [list of packages]`

---

### **Step 5: Upload CSV Dataset to VM**

**Method Used**: Transfer via GitHub (Option B)

#### **5.1: On Local Windows (PowerShell)**

```powershell
# Navigate to project on local machine
cd C:\Users\krish\btc-intelligent-trader

# Force-add CSV file (overrides .gitignore)
git add -f data/raw/btc_daily_data_2018_to_2025.csv
```
**What `-f` does**: Forces git to add file even though it's in `.gitignore`

```powershell
# Commit CSV to GitHub
git commit -m "Temporary: Add CSV for VM transfer"

# Push to GitHub
git push origin main
```
**Output**:
```
Enumerating objects: 7, done.
Writing objects: 100% (4/4), 397.02 KiB | 2.xx MiB/s, done.
To https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System.git
   109c347..9a10d72  main -> main
```

#### **5.2: On VM (SSH Terminal - Linux)**

```bash
# Create data directories
mkdir -p data/raw data/processed data/rag_vectordb
```
**What this does**:
- `mkdir`: Make directory
- `-p`: Create parent directories if needed (won't error if already exists)

```bash
# Pull CSV from GitHub
git pull origin main
```
**Output**:
```
remote: Enumerating objects: 7, done.
remote: Counting objects: 100% (7/7), done.
Unpacking objects: 100% (5/5), 397.02 KiB | 3.03 MiB/s, done.
From https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System
 * branch            main       -> FETCH_HEAD
   109c347..9a10d72  main       -> origin/main
Updating 109c347..9a10d72
Fast-forward
 data/raw/btc_daily_data_2018_to_2025.csv | 2686 ++++++++++++++++++++++++++
 1 file changed, 2686 insertions(+)
 create mode 100644 data/raw/btc_daily_data_2018_to_2025.csv
```

```bash
# Verify CSV file exists
ls -lh data/raw/btc_daily_data_2018_to_2025.csv
```
**What `-lh` does**:
- `-l`: Long format
- `-h`: Human-readable file sizes (KB, MB instead of bytes)

**Output**: `-rw-rw-r-- 1 krishnanair041 krishnanair041 910K Dec  8 04:55 btc_daily_data_2018_to_2025.csv`

```bash
# Count rows in CSV
wc -l data/raw/btc_daily_data_2018_to_2025.csv
```
**What `wc -l` does**: Word count with `-l` flag = line count
**Output**: `2686 data/raw/btc_daily_data_2018_to_2025.csv` (2,685 data rows + 1 header)

#### **5.3: Clean Up GitHub (Remove CSV)**

**Back to Local Windows (PowerShell)**:

```powershell
# Remove CSV from git tracking (keeps local file)
git rm --cached data/raw/btc_daily_data_2018_to_2025.csv

# Commit the removal
git commit -m "Remove CSV from tracking (file too large for repo)"

# Push to GitHub
git push origin main
```
**Result**: CSV now exists on both local machine and VM, but NOT on GitHub (too large for repo)

---

### **Step 6: Configure Environment Variables (.env File)**

```bash
# Copy example template
cp .env.example .env
```
**What `cp` does**: Copy file
**Result**: Creates `.env` from `.env.example` template

```bash
# Edit .env file with nano text editor
nano .env
```
**What this does**: Opens text editor in terminal

**Inside nano editor** (Linux text editor):

**Keyboard controls**:
- Arrow keys: Navigate
- Type normally to add text
- Delete key: Remove characters
- `Ctrl + O`: Save (WriteOut)
- `Enter`: Confirm filename
- `Ctrl + X`: Exit editor

**What was edited**:

** Added actual API keys (NOT shown here for security)**

**Keys added to `.env` file**:
- `GEMINI_API_KEY` - From Google AI Studio
- `TELEGRAM_BOT_TOKEN` - From @BotFather
- `TELEGRAM_CHAT_ID` - From @userinfobot
- Optional: Gmail credentials (left as placeholders)

**🔒 SECURITY: Real API keys are NEVER shown in documentation or committed to GitHub!**

See `.env.example` for the template structure.

**Save and exit**:
1. Pressed `Ctrl + O` (save)
2. Pressed `Enter` (confirm)
3. Pressed `Ctrl + X` (exit)

```bash
# Secure .env file (only owner can read/write)
chmod 600 .env
```
**What `chmod 600` does**:
- `6` (owner): Read + Write
- `0` (group): No access
- `0` (others): No access
- Prevents other users on VM from reading your API keys

```bash
# Verify permissions
ls -la .env
```
**Output**: `-rw------- 1 krishnanair041 krishnanair041 2847 Dec  8 10:30 .env`
**The `-rw-------` part**: Shows only owner can read/write

```bash
# Verify API key is set (shows first 35 chars only for security)
grep "GEMINI_API_KEY" .env | cut -c1-35
```
**What this does**:
- `grep`: Search for text
- `cut -c1-35`: Show only first 35 characters
**Output**: `GEMINI_API_KEY=[FIRST_35_CHARS]` (actual key is hidden for security)

---

### **Step 7: Upload service_account.json (Google Sheets - Optional)**

**Method Used**: Copy-paste via notepad (no file upload due to SSH authentication error)

#### **7.1: On Local Windows**

```powershell
# Open service_account.json in Notepad
notepad config\service_account.json
```
**Action**: Copied entire JSON content (Ctrl+A, Ctrl+C)

#### **7.2: On VM (SSH Terminal - Linux)**

```bash
# Create config directory
mkdir -p config
```

```bash
# Create file using cat command (accepts pasted input)
cat > config/service_account.json
```
**What this does**:
- `cat >`: Creates file and waits for input
- Cursor appears on blank line

**Action**: Right-clicked in SSH terminal (pastes clipboard content)

**Result**: JSON content appeared in terminal

**To save**: Pressed `Ctrl + D` (signals end of input)

```bash
# Verify file was created
ls -la config/service_account.json
```
**Output**: Shows file with correct size (~2-3 KB)

```bash
# View first 10 lines to verify it's valid JSON
head -10 config/service_account.json
```
**Output**:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "abc123...",
  ...
```

```bash
# Secure the file
chmod 600 config/service_account.json
```

---

### **Step 8: Install Missing Python Packages**

**Issue encountered**: Some packages weren't installed by `requirements.txt`

```bash
# Install google-generativeai
pip install google-generativeai
```
**Output**: `Successfully installed google-generativeai-0.x.x`

```bash
# Install chromadb
pip install chromadb
```
**Output**: `Successfully installed chromadb-0.x.x`

```bash
# Verify langgraph installed
python3 -c "from langgraph.graph import StateGraph; print(' langgraph working')"
```
**Output**: ` langgraph working`

---

### **Step 9: Run Backtest (Verify Deployment)**

```bash
# Make sure virtual environment is active
source venv/bin/activate
```
**Check**: Prompt shows `(venv)` prefix

```bash
# Run backtest
python3 main.py --mode backtest
```
**What this does**: Tests bot on 6 months of historical data (May-Nov 2025)

**Takes**: 1-2 minutes

**Output**:
```
🚀 Bitcoin Trading Bot - Backtesting Mode
======================================================================

📊 Loading historical data...
 Loaded 2685 rows (2018-07-19 to 2025-11-23)

🤖 Training ML model...
 Model trained - Accuracy: 0.89

💰 Running DCA Strategy...
 DCA complete - 2685 trades

💰 Running Swing Strategy...
 Swing complete - 156 trades

======================================================================
=== BACKTEST RESULTS ===
======================================================================

Initial Capital:  $10,000.00
Final Value:      $8,574.91
Total Return:     -14.25%
Sharpe Ratio:     -1.35
Max Drawdown:     -20.50%
Win Rate:         0.0%
Number of Trades: 19

Beat buy-and-hold by +5.83%!

📁 Results saved to: data/processed/backtest_results.json
```

**What this proves**: Bot works correctly on VM!

---

### **Step 10: Set Up 24/7 Background Execution (tmux)**

```bash
# Install tmux (terminal multiplexer)
sudo apt install tmux -y
```
**What tmux does**: Keeps programs running even when SSH disconnects

**Output**: `Setting up tmux ... done`

```bash
# Start new tmux session named "trading-bot"
tmux new -s trading-bot
```
**What this does**: Creates persistent background session
**Result**: New terminal screen appears with green bar at bottom

**Inside tmux (new screen)**:

```bash
# Navigate to project
cd ~/Bitcoin-Trading-Bot-System

# Activate virtual environment
source venv/bin/activate

# Start chat mode
python3 main.py --mode chat
```

**Output**:
```
[GEMINI] Smart rotation enabled: 4 models, 60 effective RPM
[RAG] System initialized with 0 patterns
[COINGECKO] Using Demo API (free tier)
[OK] Ready!

============================================================
BITCOIN TRADING ASSISTANT
============================================================

Ask me anything about your trading bot!

You:
```

**Bot is now running!**

**To detach from tmux (keep bot running in background)**:

1. Press `Ctrl + B` (hold both keys, release)
2. Press `D` (just press D once)

**Output**: `[detached (from session trading-bot)]`

**Result**: Bot keeps running 24/7 even if SSH closes!

---

### **Step 11: Verify Deployment (Post-Deployment Checks)**

```bash
# Check if tmux session is running
tmux ls
```
**Output**: `trading-bot: 1 windows (created Sun Dec  8 13:00:00 2025)`

```bash
# Check Python processes
ps aux | grep python3
```
**What this does**:
- `ps aux`: Show all processes
- `grep python3`: Filter for Python processes
**Output**: Shows `python3 main.py --mode chat` running

```bash
# Check system resources
htop
```
**What this does**: Shows CPU, memory, process monitor (like Task Manager on Windows)
**Exit**: Press `Q`

```bash
# Check disk usage
df -h
```
**Output**:
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        10G  3.2G  6.8G  32% /
```

```bash
# Check VM external IP
curl ifconfig.me
```
**Output**: `34.123.45.67` (example IP - shows VM is on cloud)

---

## Linux Commands Reference

### File & Directory Commands

| Command | What It Does | Example |
|---------|--------------|---------|
| `cd ~` | Change to home directory | `cd ~` |
| `cd Bitcoin-Trading-Bot-System` | Change directory | Navigate to folder |
| `ls -la` | List all files (long format) | See files with permissions |
| `mkdir -p data/raw` | Create directory | `-p` creates parents if needed |
| `cp .env.example .env` | Copy file | Duplicate file |
| `mv ~/file.csv data/raw/` | Move file | Transfer to another folder |
| `rm file.txt` | Remove file | Delete file |
| `cat file.txt` | View file contents | Print to terminal |
| `head -10 file.txt` | View first 10 lines | Quick preview |
| `tail -10 file.txt` | View last 10 lines | See end of file |
| `wc -l file.csv` | Count lines | How many rows |
| `chmod 600 .env` | Change permissions | Secure file |

### Package Management (apt)

| Command | What It Does |
|---------|--------------|
| `sudo apt update` | Update package list |
| `sudo apt upgrade -y` | Upgrade packages |
| `sudo apt install python3 -y` | Install package |

### Python Virtual Environment

| Command | What It Does |
|---------|--------------|
| `python3 -m venv venv` | Create virtual environment |
| `source venv/bin/activate` | Activate virtual environment |
| `pip install package` | Install Python package |
| `pip install -r requirements.txt` | Install all dependencies |

### Git Commands

| Command | What It Does |
|---------|--------------|
| `git clone URL` | Download repository |
| `git pull origin main` | Get latest changes |
| `git status` | Check what changed |
| `git add .` | Stage all changes |
| `git commit -m "message"` | Save changes |
| `git push origin main` | Upload to GitHub |

### tmux Commands

| Command | What It Does |
|---------|--------------|
| `tmux new -s name` | Create new session |
| `tmux ls` | List sessions |
| `tmux attach -t name` | Reconnect to session |
| `tmux kill-session -t name` | Stop session |
| `Ctrl + B, then D` | Detach (inside tmux) |

### System Monitoring

| Command | What It Does |
|---------|--------------|
| `ps aux | grep python` | Find Python processes |
| `htop` | Process monitor (press Q to exit) |
| `df -h` | Disk usage |
| `curl ifconfig.me` | Check external IP |
| `uptime` | How long VM has been running |

---

## What is Linux?

**Linux** = Open-source operating system (like Windows, but free)

**Ubuntu 22.04 LTS** = Popular Linux distribution (version of Linux)

**SSH (Secure Shell)** = Way to connect to remote Linux server via terminal

**Terminal/Shell** = Text-based interface to control Linux (like Command Prompt on Windows, but more powerful)

**Why Linux for servers?**
- Free and open-source
- Stable and secure
- Lightweight (uses less resources)
- Industry standard for cloud servers

---

## GCP vs Local Machine

| Aspect | Local Windows | GCP Linux VM |
|--------|---------------|--------------|
| **Location** | Your computer | Google's data center |
| **OS** | Windows 11 | Ubuntu 22.04 (Linux) |
| **Access** | Direct keyboard/mouse | SSH terminal (text only) |
| **File editing** | Notepad, VS Code | nano, vim (terminal editors) |
| **Always on?** | Only when PC is on | 24/7 (even when PC is off) |
| **Cost** | Free (your electricity) | ~$15/month (GCP charges) |
| **IP Address** | Changes (home network) | Static (cloud server) |

---

## Understanding the Deployment Flow

```
LOCAL WINDOWS (C:\Users\krish\btc-intelligent-trader)
    ↓ [Push to GitHub]
GITHUB (https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System)
    ↓ [Clone to VM]
GCP LINUX VM (krishnanair041@btc-trader-vm:~/Bitcoin-Trading-Bot-System)
    ↓ [Run in tmux]
BOT RUNNING 24/7 IN CLOUD
```

**Code lives in 3 places**:
1. **Local**: Where you develop/edit
2. **GitHub**: Version control & sharing
3. **GCP VM**: Where it runs 24/7

---

## Manual GitHub Push Commands

Use these commands to update GitHub with all the new changes to README.md and DEPLOYMENT_SUCCESS.md.

### **On Local Windows (PowerShell)**

```powershell
# Step 1: Navigate to project
cd C:\Users\krish\btc-intelligent-trader

# Step 2: Check what changed
git status
```
**Expected output**:
```
On branch main
Changes not staged for commit:
  modified:   README.md
  modified:   DEPLOYMENT_SUCCESS.md
```

```powershell
# Step 3: View the changes (optional - review before committing)
git diff README.md
git diff DEPLOYMENT_SUCCESS.md
```

```powershell
# Step 4: Stage the files
git add README.md
git add DEPLOYMENT_SUCCESS.md
```

```powershell
# Step 5: Commit with descriptive message
git commit -m "Update: Add ChromaDB/FAISS explanation and complete GCP deployment guide

Added to README.md:
- Detailed ChromaDB vs FAISS technology stack explanation
- How RAG system works with example flow
- ChromaDB vs Direct CSV access comparison
- Complete GCP deployment guide with all SSH/Linux commands
- Dataset upload methods (GCP Console + GitHub transfer)
- tmux setup for 24/7 bot operation
- Daily operations and monitoring commands
- Cost tracking and troubleshooting
- Manual GitHub push instructions

Updated DEPLOYMENT_SUCCESS.md:
- Complete SSH command history (step-by-step)
- All Linux commands used during deployment
- Explanations of what each command does
- service_account.json copy-paste method via notepad
- CSV file upload via GitHub clone method
- Linux commands reference table
- GCP vs Local machine comparison
- Deployment verification steps

Updated deployment status:
- GCP as primary deployment platform
- Bot running 24/7 in tmux session
- All APIs connected and verified
- Last updated: 2025-12-08

Developed by: Krishna Nair"
```

```powershell
# Step 6: Verify commit was created
git log -1 --pretty=format:"%an <%ae>%n%s%n%b"
```
**Expected output** (will show YOUR name and email):
```
Your Name <your_email@gmail.com>
Update: Add ChromaDB/FAISS explanation and complete GCP deployment guide
...
```

```powershell
# Step 7: Push to GitHub
git push origin main
```

**Expected output**:
```
Enumerating objects: 7, done.
Counting objects: 100% (7/7), done.
Delta compression using up to 8 threads
Compressing objects: 100% (4/4), done.
Writing objects: 100% (4/4), 12.34 KiB | 2.46 MiB/s, done.
Total 4 (delta 2), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (2/2), completed with 2 local objects.
To https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System.git
   9a10d72..abc1234  main -> main
```

** Success!** Your updates are now on GitHub.

---

### **Verification (Check GitHub)**

1. Go to: https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System
2. Click on **README.md** - should show updated content with ChromaDB section
3. Click on **DEPLOYMENT_SUCCESS.md** - should show complete SSH command history
4. Check **commit history** - should show your new commit with "Krishna Nair" as author

---

### **Security Checklist Before Pushing**

```powershell
# Check that .env is NOT staged
git status | Select-String ".env"
```
**Should show**: Nothing (or only `.env.example`)

```powershell
# Verify .gitignore is protecting .env
Get-Content .gitignore | Select-String "\.env"
```
**Should show**: `## Environment Variables` and `.env` lines

```powershell
# Check what will be pushed
git diff --cached
```
**Should show**: Only README.md and DEPLOYMENT_SUCCESS.md changes

** If all checks pass**: Safe to push!

---

## Files Updated

| File | Lines Added | What Was Added |
|------|-------------|----------------|
| **README.md** | ~450 lines | ChromaDB explanation, GCP deployment guide, cost tracking |
| **DEPLOYMENT_SUCCESS.md** | ~550 lines | Complete SSH command history, Linux reference, deployment flow |
| **Total** | ~1,000 lines | Comprehensive deployment documentation |

---

## Deployment Complete! 🎉

**What You Achieved**:

 Deployed Bitcoin Trading Bot to Google Cloud Platform
 Bot running 24/7 in tmux session
 All data and APIs connected
 Complete documentation of deployment process
 GitHub repository updated with deployment guide
 Learned Linux command line
 Mastered SSH and remote server management

**Bot Status**: ACTIVE & RUNNING 24/7 on GCP us-central1-a

**Access**: SSH to `btc-trader-vm` anytime from anywhere

**Cost**: ~$15/month from $300 free credit (20 months free!)

---

**Developed by: Krishna Nair**
**Repository**: https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System
**Date**: December 8, 2025
