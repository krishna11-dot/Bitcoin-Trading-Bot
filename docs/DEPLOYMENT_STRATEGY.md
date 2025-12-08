# Deployment Strategy - Local First, Cloud Later

**Purpose:** Understanding deployment fundamentals before cloud

**Last Updated:** 2025-11-30

---

## Core Concept: Your Computer = CPU Entity

> "Understand that your computer is a CPU entity and whatever you're creating needs to be lodged to it in order to perform."

**What this means:**
- Your code doesn't run by itself
- It needs a CPU (processor) to execute
- Deployment = Making code run on a CPU continuously

---

## ARCHITECTURE: WITHOUT vs WITH NSSM

### WITHOUT NSSM (Manual Running)

```
USER
  ↓
Opens PowerShell Terminal
  ↓
Types: python main.py --mode live
  ↓
┌─────────────────────────────────────────┐
│  PYTHON PROCESS (Foreground)            │
│  - Visible terminal window              │
│  - Stops when you close terminal        │
│  - Stops when you log off               │
│  - Stops when computer restarts         │
│  - You must manually start it           │
└─────────────────────────────────────────┘
  ↓
main.py → live_trader.py → Trading Loop
```

**Problems:**
- ❌ Terminal must stay open
- ❌ Stops if you close terminal
- ❌ Stops if you log off Windows
- ❌ Doesn't auto-start on reboot
- ❌ Manual start every time

---

### WITH NSSM (Service Running)

```
WINDOWS BOOTS
  ↓
Windows Service Manager starts
  ↓
┌─────────────────────────────────────────────────────────────┐
│  NSSM (Windows Service Wrapper)                             │
│  - Registered as "BTCTradingBot" service                    │
│  - Auto-starts on boot                                      │
│  - Runs in background (no terminal window)                  │
│  - Survives logoff                                          │
│  - Auto-restarts on crash                                   │
│                                                             │
│  NSSM Configuration:                                        │
│  ├─ Application: C:\...\venv\Scripts\python.exe           │
│  ├─ Arguments: C:\...\main.py --mode live                 │
│  ├─ Startup: Automatic                                     │
│  └─ AppDirectory: C:\Users\krish\btc-intelligent-trader   │
└─────────────────────────────────────────────────────────────┘
  ↓
NSSM spawns → python.exe main.py --mode live
  ↓
┌─────────────────────────────────────────┐
│  PYTHON PROCESS (Background)            │
│  - No visible window                    │
│  - Managed by NSSM                      │
│  - Auto-restarts if crashes             │
│  - Logs to file (not terminal)          │
└─────────────────────────────────────────┘
  ↓
main.py → live_trader.py → Trading Loop (same as before)
```

**Benefits:**
- ✅ Auto-starts on boot
- ✅ Runs in background (no window)
- ✅ Survives logoff
- ✅ Auto-restarts on crash
- ✅ Controlled via Windows Services

---

### NSSM WRAPPING: Complete Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    WINDOWS OPERATING SYSTEM                  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Windows Service Manager (services.msc)         │ │
│  │                                                        │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  NSSM Service: "BTCTradingBot"                   │ │ │
│  │  │  Status: RUNNING                                 │ │ │
│  │  │  Startup Type: Automatic                         │ │ │
│  │  │                                                  │ │ │
│  │  │  ┌────────────────────────────────────────────┐ │ │ │
│  │  │  │  NSSM.EXE (Wrapper Process)                │ │ │ │
│  │  │  │  - Monitors child process                  │ │ │ │
│  │  │  │  - Restarts on crash                       │ │ │ │
│  │  │  │  - Captures stdout/stderr to logs          │ │ │ │
│  │  │  │  - Passes environment variables            │ │ │ │
│  │  │  │                                            │ │ │ │
│  │  │  │  ┌──────────────────────────────────────┐ │ │ │ │
│  │  │  │  │  PYTHON.EXE (Your Bot)               │ │ │ │ │
│  │  │  │  │  Command: python main.py --mode live │ │ │ │ │
│  │  │  │  │                                      │ │ │ │ │
│  │  │  │  │  ┌────────────────────────────────┐ │ │ │ │ │
│  │  │  │  │  │  MAIN.PY                       │ │ │ │ │ │
│  │  │  │  │  │  - Routes to live mode        │ │ │ │ │ │
│  │  │  │  │  │                               │ │ │ │ │ │
│  │  │  │  │  │  ┌─────────────────────────┐ │ │ │ │ │ │
│  │  │  │  │  │  │  LIVE_TRADER.PY         │ │ │ │ │ │ │
│  │  │  │  │  │  │  - Runs every 5 min    │ │ │ │ │ │ │
│  │  │  │  │  │  │  - Fetches BTC price   │ │ │ │ │ │ │
│  │  │  │  │  │  │  - Makes trades        │ │ │ │ │ │ │
│  │  │  │  │  │  │  - Sends Telegram      │ │ │ │ │ │ │
│  │  │  │  │  │  │  - Sends Gmail (8 PM)  │ │ │ │ │ │ │
│  │  │  │  │  │  └─────────────────────────┘ │ │ │ │ │ │
│  │  │  │  │  └────────────────────────────────┘ │ │ │ │ │
│  │  │  │  └──────────────────────────────────────┘ │ │ │ │
│  │  │  └────────────────────────────────────────────┘ │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**NSSM's Role (The Wrapper):**
1. **Service Registration:** Tells Windows this is a service
2. **Process Management:** Launches python.exe with your script
3. **Monitoring:** Watches if process crashes
4. **Auto-Restart:** Restarts Python if it dies
5. **Environment:** Passes API keys and variables
6. **Logging:** Captures all output to log files
7. **Lifecycle:** Handles start/stop/restart commands

---

### Control Flow Comparison

**Manual (Without NSSM):**
```
User → Terminal → python.exe → main.py → live_trader.py
       (closes)   (stops)     (stops)    (stops)
```

**Service (With NSSM):**
```
Boot → Service Manager → NSSM → python.exe → main.py → live_trader.py
       (persistent)     (wrapper) (monitored) (keeps running)
                          ↓
                     (if crash)
                          ↓
                    Auto-restart
```

---

## The Fundamental Understanding

### What is Deployment?

**Simple definition:**
```
Deployment = Making your bot run 24/7 on a computer
```

**Current state:**
- You run: `python main.py`
- Bot runs while terminal is open
- You close terminal → Bot stops

**Deployed state:**
- Bot runs automatically
- Runs 24/7 (even when you're offline)
- Restarts if it crashes
- Runs on a dedicated computer/server

---

### The Learning Path

```
Step 1: Local Deployment (Your Computer)
   ↓
Understand the fundamentals:
- How to run bot continuously
- How to manage processes
- How to handle restarts
   ↓
Step 2: Cloud Deployment (AWS/etc)
   ↓
Same concepts, different machine
```

**Quote:**
> "Learn the fundamental of how to figure out... your computer as a server. Once you get that clearly, then it doesn't, you will find it easy to use AWS."

---

## Two Things in Deployment (This Project)

### 1. Local Server (Your Computer as Server)

**Goal:** Make your computer run the bot 24/7

**What you'll learn:**
- Process management (keep bot running)
- Automatic restarts (if crash)
- Background processes (terminal can close)
- Logging (track what happens)
- Error handling (graceful failures)

**Why local first:**
- Free (your computer)
- Easy to debug (you can see what happens)
- Learn fundamentals without cloud complexity
- Understand the concepts before paying for AWS

---

### 2. Cloud Deployment (AWS/Cloud)

**Goal:** Move bot to a server that runs 24/7

**What changes:**
- Computer = AWS EC2 instance
- Same code, different machine
- Pay for server time (~$5-20/month)

**What stays the same:**
- Bot logic (identical code)
- Process management (same tools)
- Concepts you learned locally

**Why cloud eventually:**
- Runs even when your computer is off
- More reliable uptime
- Professional solution
- Can scale if needed

---

## Your Current Project: What Needs Deployment?

### Option 1: Backtest Mode (No Deployment Needed)

**Current use case:**
```bash
python main.py --mode backtest
```

**What happens:**
- Runs once on historical data
- Generates results
- Exits

**Deployment needed?** NO
- This is a one-time script
- Run manually when you want results
- Like running any Python script

---

### Option 2: Live Trading Mode (Needs Deployment)

**Future use case:**
```bash
python main.py --mode live
```

**What should happen:**
- Runs continuously 24/7
- Monitors BTC price every hour
- Executes trades automatically
- Sends notifications (Telegram/Gmail)
- Runs forever (until you stop it)

**Deployment needed?** YES
- Needs to run 24/7
- Can't keep terminal open forever
- Need automatic restarts
- Need process management

---

## Local Deployment: Step-by-Step

### Phase 1: Understand Process Management

**Concept:** Keep bot running in background

**Windows approach:**
```bash
# Option 1: Windows Task Scheduler
# Schedule Python script to run at startup
# Automatically restarts if crash

# Option 2: NSSM (Non-Sucking Service Manager)
# Turn Python script into Windows service
# Runs in background, auto-restarts
```

**Linux/Mac approach:**
```bash
# Option 1: systemd (Linux)
# Create service that runs bot
# Auto-start on boot, auto-restart on crash

# Option 2: screen/tmux
# Run in detached terminal session
# Terminal can close, bot keeps running
```

---

### Phase 2: Make Bot Run Continuously

**Add to your code:**

```python
# main.py
import time
import signal
import sys

def signal_handler(sig, frame):
    """Handle graceful shutdown"""
    print('\n[SHUTDOWN] Stopping bot gracefully...')
    # Clean up resources
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    if args.mode == 'live':
        print("[LIVE] Starting 24/7 trading bot...")

        while True:  # Run forever
            try:
                # Check BTC price
                # Make trading decision
                # Execute if needed
                # Send notifications

                # Wait 1 hour
                time.sleep(3600)

            except Exception as e:
                print(f"[ERROR] {e}")
                # Log error
                # Continue running (don't crash)
                time.sleep(60)  # Wait 1 min, retry
```

**Key concepts:**
- `while True`: Infinite loop (runs forever)
- Try/except: Catch errors, don't crash
- Signal handler: Graceful shutdown on Ctrl+C
- Sleep: Wait between checks

---

### Phase 3: Process Management Tools

**Windows:**

1. **NSSM (Recommended)**
```bash
# Install NSSM
# Download from nssm.cc

# Create service
nssm install BTCTradingBot "C:\Python\python.exe" "C:\path\to\main.py --mode live"

# Start service
nssm start BTCTradingBot

# Bot now runs 24/7, auto-restarts
```

2. **Task Scheduler**
```
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At startup
4. Action: Start program (python.exe)
5. Arguments: C:\path\to\main.py --mode live
```

**Linux:**

1. **systemd (Recommended)**
```bash
# Create service file: /etc/systemd/system/btc-trader.service
[Unit]
Description=BTC Trading Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/btc-intelligent-trader
ExecStart=/usr/bin/python3 main.py --mode live
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable service
sudo systemctl enable btc-trader
sudo systemctl start btc-trader

# Bot runs 24/7, auto-restarts
```

---

### Phase 4: Logging & Monitoring

**Add logging:**

```python
# main.py
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/bot_{datetime.now():%Y%m%d}.log'),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger(__name__)

# Use in code:
logger.info("[LIVE] Bot started")
logger.info(f"[TRADE] Bought 0.01 BTC at ${price}")
logger.error(f"[ERROR] API failed: {error}")
```

**Why logging:**
- See what bot did while you were away
- Debug issues
- Track trades
- Monitor health

---

## Cloud Deployment (AWS): Later Stage

### When to Move to Cloud

**Stay local if:**
- Still testing/learning
- Computer runs 24/7 anyway
- Want to save money ($0 cost)
- Comfortable with local setup

**Move to cloud when:**
- Need 99.9% uptime
- Want professional setup
- Computer not always on
- Ready to pay ~$10/month

---

### AWS EC2 Deployment (Future)

**Concept:** Same local setup, different computer

```
Your Computer (Local)         AWS EC2 (Cloud)
 Python installed    →      Python installed
 Bot code            →      Bot code (upload)
 systemd/NSSM        →      systemd (Linux)
 Runs 24/7           →      Runs 24/7 (cloud)
```

**Steps (when ready):**
1. Launch EC2 instance (Linux server)
2. Install Python
3. Upload your code
4. Install dependencies
5. Setup systemd (same as local Linux)
6. Run bot 24/7

**Cost:** ~$5-20/month (t2.micro free tier)

---

## The Learning Sequence

### Now (Local Deployment)

```
1. Understand process management
   → How to keep bot running 24/7

2. Implement continuous loop
   → while True with error handling

3. Setup NSSM/systemd
   → Auto-start, auto-restart

4. Add logging
   → Track what happens

5. Test locally
   → Let it run for days, verify stability
```

**Time investment:** 1-2 days

**Cost:** $0 (your computer)

**Learning outcome:** Understand deployment fundamentals

---

### Later (Cloud Deployment)

```
1. Create AWS account
   → Free tier available

2. Launch EC2 instance
   → t2.micro (free tier)

3. SSH into instance
   → Remote terminal access

4. Upload code
   → git clone or scp

5. Setup same as local
   → systemd, logging, etc.

6. Run bot in cloud
   → 24/7 uptime
```

**Time investment:** 1-2 days (after understanding local)

**Cost:** ~$0-10/month (free tier first year)

**Learning outcome:** Professional deployment

---

## Key Understanding: The Fundamental

### Your Computer = Server = AWS EC2

**All are the same concept:**

```
Computer (CPU Entity)
   ↓
Needs code to run on it
   ↓
Process management keeps it running
   ↓
Runs 24/7
```

**Only difference:**
- Your computer = You own it, free, at home
- AWS EC2 = Amazon owns it, paid, in cloud

**Same code. Same concepts. Different machine.**

---

## Current Recommendation

### For Now: Local Deployment

**Why:**
1. Learn fundamentals (process management)
2. Free (no AWS cost)
3. Easy to debug (physical access)
4. Understand concepts before cloud
5. Test stability before paying

**How:**
```bash
# Windows:
1. Install NSSM
2. Create service: python main.py --mode live
3. Let it run for a week
4. Verify stability

# Linux:
1. Create systemd service
2. Enable: sudo systemctl enable btc-trader
3. Let it run for a week
4. Verify stability
```

---

### Later: Cloud Deployment (When Ready)

**When:**
- After local works perfectly for 1+ week
- When you understand process management
- When ready to pay ~$10/month
- When you want 99.9% uptime

**How:**
1. Same code, upload to AWS
2. Same systemd setup
3. Same logging
4. Runs in cloud instead of home

---

## Summary

### The Fundamental Concept

**Quote:**
> "Your computer is a CPU entity and whatever you're creating needs to be lodged to it in order to perform."

**Translation:**
- Code doesn't run by itself
- Needs a computer (CPU) to execute
- Deployment = Making code run on CPU 24/7

---

### The Two-Stage Approach

**Stage 1: Local (Your Computer)**
- Learn fundamentals
- Free
- Easy to debug
- Understand concepts

**Stage 2: Cloud (AWS)**
- Same concepts
- Different machine
- Professional setup
- Paid but reliable

---

### Key Takeaway

**Quote:**
> "Once you get that [local deployment] clearly, then you will find it easy to use AWS."

**Why this approach works:**
1. Learn fundamentals locally (free, easy)
2. Understand: process management, logging, restarts
3. Apply same concepts to cloud (just different machine)
4. AWS becomes easy because you know the fundamentals

---

## Next Steps

### Immediate (This Week)

1. **Read this guide** 
2. **Understand the concept:** Computer = CPU entity
3. **Test local deployment:**
   - Make bot run in infinite loop
   - Add error handling
   - Test for 24 hours

---

### Short-term (Next 2 Weeks)

4. **Setup process management:**
   - Windows: NSSM
   - Linux: systemd
5. **Add logging**
6. **Test stability:** Let run for 1 week

---

### Long-term (When Ready)

7. **Learn AWS basics**
8. **Launch EC2 instance**
9. **Deploy to cloud**
10. **Monitor 99.9% uptime**

---

**Status:** Local deployment understanding 

**Cloud deployment:** After local works perfectly 

**Cost:** $0 now, ~$10/month later 

**Last Updated:** 2025-11-30

---

# PART 2: ACTUAL IMPLEMENTATION COMPLETED

**Date:** 2025-12-04
**Status:** Successfully Deployed Locally
**Environment:** Windows 11 with NSSM Service

---

## What We Actually Did: Complete Guide

### The Goal

**Before:** Bot only runs when PowerShell is open
**After:** Bot runs 24/7 as a Windows Service, survives reboots, auto-restarts

### What We Achieved

```
[SUCCESS] Bot runs in background 24/7
[SUCCESS] Auto-starts on computer boot
[SUCCESS] Auto-restarts if crashes
[SUCCESS] Logs all activity to files
[SUCCESS] Successfully executing trades
[SUCCESS] 100% signal execution rate
[SUCCESS] Survives terminal closing
[SUCCESS] Survives user logout
```

---

## Core Tools Explained (Simple Clarity)

### 1. PowerShell as Administrator

**What it is:**
```
PowerShell = Windows command-line interface (like Command Prompt, but more powerful)
Administrator = Running with full system permissions
```

**Why Administrator?**
```
Normal PowerShell:
- Can't install system-wide programs
- Can't create Windows Services
- Limited to your user account

Administrator PowerShell:
- Can install programs for all users
- Can create/manage Windows Services
- Full system access
```

**How to open:**
```
1. Press Windows Key
2. Type "PowerShell"
3. Right-click "Windows PowerShell"
4. Click "Run as Administrator"
5. Click "Yes" on UAC prompt
```

**Real-world analogy:**
```
Normal PowerShell = Regular user on a computer
Administrator PowerShell = System admin with master key
```

---

### 2. Chocolatey (Package Manager)

**What it is:**
```
Chocolatey = App store for Windows command-line programs

Think of it like:
- Google Play Store (for Android apps)
- App Store (for iOS apps)
- apt-get (for Linux)
- npm (for JavaScript packages)

But for Windows programs.
```

**Why we need it:**
```
WITHOUT Chocolatey:
1. Google "download NSSM"
2. Find correct website
3. Download ZIP file
4. Extract files
5. Copy to Program Files
6. Add to PATH manually
7. Configure environment
Result: 15-20 minutes, error-prone

WITH Chocolatey:
1. Run: choco install nssm -y
Result: 30 seconds, automated```

**What it does behind the scenes:**
```
1. Downloads program from official source
2. Verifies it's safe (checksum validation)
3. Installs to correct location
4. Adds to system PATH automatically
5. Configures environment variables
6. Makes program available system-wide
```

**Real-world analogy:**
```
Chocolatey = Personal assistant who:
- Knows where to buy everything
- Gets it for you automatically
- Sets it up perfectly
- You just say what you need
```

---

### 3. NSSM (Non-Sucking Service Manager)

**What it is:**
```
NSSM = Tool that converts ANY program into a Windows Service

Full name: Non-Sucking Service Manager
Why "Non-Sucking"? Microsoft's built-in service tools are complex
NSSM makes it simple (doesn't suck!)
```

**What is a Windows Service?**
```
Regular Program:
- You start it manually
- Runs while you're logged in
- Stops when you close terminal
- Doesn't auto-restart if crashes

Windows Service:
- Windows starts it automatically
- Runs even when no user logged in
- Survives terminal closing
- Auto-restarts on crash
- Starts on computer boot
- Runs in background 24/7
```

**Real-world analogy:**
```
Regular Program = You manually driving a car
Windows Service = Self-driving car that:
  - Starts automatically when you turn key
  - Keeps running without your attention
  - Restarts itself if engine stalls
  - Runs 24/7 without you in the car
```

**What NSSM does:**
```
Your Python Script (main.py)
   ↓
NSSM wraps it in protective shell
   ↓
Windows Service
   ↓
Benefits:
- Auto-start on boot
- Auto-restart on crash
- Background execution
- Log file management
- Survives user logout
```

---

### 4. Windows Service (Concept)

**What it is:**
```
Windows Service = Background program that Windows manages automatically

Examples of Windows Services you already use:
- Windows Update (updates Windows in background)
- Windows Defender (scans for viruses 24/7)
- Print Spooler (manages printers)
- Windows Time (keeps clock synchronized)
```

**Your bot as a service:**
```
Before (Manual):
You → Open PowerShell → Run python main.py → Bot runs
Close PowerShell → Bot stops
After (Service):
Computer boots → Windows starts BTCTradingBot service automatically
Bot runs 24/7 in backgroundYou can log off, close terminals, restart → Bot keeps running```

**Service vs Regular Program:**
```

 Feature              Regular Prog  Service      

 Starts on boot       No            Yes       
 Runs in background   No            Yes       
 Auto-restart crash   No            Yes       
 Survives logout      No            Yes       
 Requires terminal    Yes           No        
 24/7 operation       No            Yes       

```

---

## All Commands We Used (Step-by-Step)

### Step 1: Install Chocolatey

**Command:**
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

**What each part does:**

```
Set-ExecutionPolicy Bypass -Scope Process -Force
↓
Temporarily allows PowerShell to run downloaded scripts
(Windows blocks external scripts by default for security)
-Scope Process = Only this PowerShell window
-Force = Don't ask for confirmation

iex (...)
↓
"iex" = Invoke-Expression = Run the downloaded script

New-Object System.Net.WebClient
↓
Create a web downloader tool

DownloadString('https://...')
↓
Download Chocolatey installer script from official website

Complete flow:
1. Allow scripts to run
2. Download Chocolatey installer
3. Run installer
4. Chocolatey installed```

**What you saw:**
```
Getting latest version of Chocolatey...
Extracting C:\ProgramData\chocolatey\choco.exe...
Chocolatey (choco.exe) is now ready.
```

**Verification:**
```powershell
choco --version
# Output: 2.6.0
```

---

### Step 2: Install NSSM via Chocolatey

**Command:**
```powershell
choco install nssm -y
```

**What each part does:**

```
choco
↓
Run the Chocolatey program (installed in Step 1)

install
↓
Command: Download and install a package

nssm
↓
Package name (from Chocolatey repository)

-y
↓
Auto-confirm (skip "Are you sure? [Y/N]" prompts)

Complete flow:
1. Chocolatey connects to chocolatey.org
2. Searches for "nssm" package
3. Downloads latest version (2.24-101)
4. Extracts to C:\ProgramData\chocolatey\lib\NSSM\
5. Creates shortcut in C:\ProgramData\chocolatey\bin\
6. Adds to system PATH
7. NSSM ready to use```

**What you saw:**
```
Downloading package from source...
nssm v2.24.101.20180116 [Approved]
Installing 64 bit version
ShimGen has successfully created a shim for nssm.exe
The install of nssm was successful.
```

**Verification:**
```powershell
nssm
# Output: NSSM: The non-sucking service manager
```

---

### Step 3: Create Logs Directory

**Command:**
```powershell
cd C:\Users\krish\btc-intelligent-trader
mkdir logs
```

**What each part does:**

```
cd C:\Users\krish\btc-intelligent-trader
↓
"cd" = Change Directory
Navigate to your project folder

mkdir logs
↓
"mkdir" = Make Directory
Create a folder called "logs"

Why we need this:
- NSSM will write bot output to log files
- Needs directory to exist before starting service
- logs/bot.log = Normal output (print statements)
- logs/bot_error.log = Errors (exceptions)
```

---

### Step 4: Create Windows Service with NSSM

**Command:**
```powershell
nssm install BTCTradingBot
```

**What this does:**
```
nssm install BTCTradingBot
↓
Opens a GUI window to configure the service

You filled in:

 Application Tab:                            
 - Path: C:\...\\.venv\Scripts\python.exe   
 - Startup directory: C:\...\btc-...trader  
 - Arguments: main.py --mode live            
                                             
 Details Tab:                                 
 - Display name: BTC Trading Bot             
 - Startup type: Automatic                   
                                             
 I/O Tab:                                     
 - Output: C:\...\\logs\bot.log             
 - Error: C:\...\\logs\bot_error.log        
                                             
 Environment Tab:                             
 - BINANCE_TESTNET_API_KEY=your_key          
 - BINANCE_TESTNET_SECRET_KEY=your_secret    


After clicking "Install service":
- Windows registers new service
- Service appears in Windows Services Manager
- Not running yet (just registered)
```

---

### Step 5: Set Environment Variables (Critical!)

**Commands:**
```powershell
nssm set BTCTradingBot AppEnvironmentExtra 
"BINANCE_TESTNET_API_KEY= 
"BINANCE_TESTNET_SECRET_KEY=
```

**What this does:**
```
nssm set BTCTradingBot AppEnvironmentExtra
↓
Set environment variables for the service

Why this is needed:
1. Service runs in different "context" than your user
2. Can't automatically find .env file
3. Must tell service explicitly where API keys are

Critical nuances:
WRONG: "BINANCE_TESTNET_API_KEY= value" (space after =)
CORRECT: "BINANCE_TESTNET_API_KEY=value" (no space)

WRONG: BINANCE_API_KEY (wrong variable name)
CORRECT: BINANCE_TESTNET_API_KEY (matches code)
```

**Verification:**
```powershell
nssm get BTCTradingBot AppEnvironmentExtra
# Output: Shows your environment variables
```

---

### Step 6: Sync System Time (Critical for API)

**Commands:**
```powershell
w32tm /resync
w32tm /query /status
```

**What each does:**

```
w32tm /resync
↓
"w32tm" = Windows Time service
"/resync" = Synchronize with internet time servers

Why this matters:
- Binance validates request timestamps
- If your clock is >1000ms off → Rejected- Syncing ensures clock matches Binance servers
w32tm /query /status
↓
Check time synchronization status
Shows: Last sync time, time source, accuracy
```

**What you saw:**
```
Sending resync command to local computer
The command completed successfully.
```

---

### Step 7: Start the Service

**Command:**
```powershell
nssm start BTCTradingBot
```

**What this does:**
```
1. Windows Service Manager receives command
2. Launches: C:\...\.venv\Scripts\python.exe main.py --mode live
3. Bot starts running in background
4. Writes output to logs/bot.log
5. Service status: SERVICE_RUNNING
Bot is now:
- Running in background (no terminal needed)
- Will survive terminal closing
- Will survive user logout
- Will auto-restart on crash
- Will auto-start on computer boot
```

**What you saw:**
```
BTCTradingBot: START: The operation completed successfully.
```

---

### Step 8: Check Service Status

**Command:**
```powershell
nssm status BTCTradingBot
```

**Possible outputs:**
```
SERVICE_RUNNING    Bot is active
SERVICE_STOPPED    Bot not running
SERVICE_PAUSED     [PAUSED]Bot paused
SERVICE_START_PENDING  [PENDING]Bot starting up (wait)
SERVICE_STOP_PENDING   [PENDING]Bot shutting down (wait)
```

---

### Step 9: Monitor Bot Activity

**Command:**
```powershell
Get-Content logs\bot.log -Wait -Tail 30
```

**What each part does:**

```
Get-Content logs\bot.log
↓
Read the log file (like "cat" on Linux)

-Tail 30
↓
Show last 30 lines only

-Wait
↓
Keep watching for new lines (live updates)
Like "tail -f" on Linux

Press Ctrl+C to stop watching (doesn't stop bot)
```

**What you saw:**
```
[SUCCESS] Bought 0.000320 BTC @ $93,122.39
Trades Executed: 1
Signal Execution Rate: 100.0%
```

---

## The Nuances We Encountered (Critical Learnings)

### Nuance 1: Environment Variable Names Must Match Exactly

**The Problem:**
```
NSSM had:  BINANCE_API_KEY
Code expects: BINANCE_TESTNET_API_KEY
Result: Code can't find key → Authentication fails```

**The Lesson:**
```
Variable names are case-sensitive and must match EXACTLY
Code looks for specific name
If name different → Variable not found
Like calling someone "John" when their name is "Jonathan"
```

---

### Nuance 2: Whitespace Breaks API Headers

**The Problem:**
```
Set: BINANCE_TESTNET_API_KEY= 5AVipy...
                              ↑ Space here
API header becomes: " 5AVipy..." (space before value)
Binance rejects: "Invalid leading whitespace"```

**The Lesson:**
```
NO space after = sign
API_KEY= value
API_KEY=value

Why it breaks:
API sends header: "X-MBX-APIKEY: 5AVipy..."
With space: "X-MBX-APIKEY:  5AVipy..."
Binance validation fails on space
```

**How we fixed:**
```powershell
# Use command-line (no GUI to add accidental spaces)
nssm set BTCTradingBot AppEnvironmentExtra "KEY=value"
```

---

### Nuance 3: Services Run in Different Context

**The Problem:**
```
When YOU run manually:
PowerShell → Loads your user environment → Finds .env file → Works
When SERVICE runs:
Windows Service Manager → Different environment → Can't find .env → Fails```

**Why this happens:**
```
Services run as "Local System" account:
- Different home directory
- Different PATH
- Different environment variables
- Different working directory

Your user account:
- Has access to .env file
- Knows where project is
- Environment configured
```

**The Solution:**
```
Tell NSSM explicitly:
1. Working directory (where project is)
2. Environment variables (API keys)
3. Python path (UV virtual environment)

NSSM passes these to service
Service now has same context as manual run```

---

### Nuance 4: Time Synchronization Matters

**The Problem:**
```
Your computer clock: 12:00:01.500
Binance server clock: 12:00:00.000
Difference: 1500ms

Binance validation:
If difference > 1000ms → Reject request"Timestamp for this request is outside the recvWindow"
```

**Why this matters:**
```
API security feature:
- Prevents replay attacks
- Ensures requests are fresh
- Validates you're in sync with reality

If clock drifts over time:
- Requests start failing
- Random 400 errors appear
```

**The Solution:**
```powershell
w32tm /resync
# Syncs your clock with internet time servers
# Ensures <100ms difference
# Binance accepts requests```

---

### Nuance 5: First Cycle Behavior

**What we saw:**
```
Cycle 1: Portfolio loaded correctly ($104,400)
Cycle 1: Order failed
Cycle 2-3: Portfolio failed to load
Cycle 2-3: Orders failed
After restart:
Cycle 1: Portfolio loaded correctly
Cycle 1: Order SUCCEEDED```

**Why this happened:**
```
Service loads environment variables on START
If you change variables mid-session:
- Old variables cached in memory
- New variables not loaded yet
- Inconsistent behavior

Solution: Full restart
nssm stop BTCTradingBot
nssm start BTCTradingBot
(Clears cache, loads fresh variables)
```

---

## What We Achieved: Before vs After

### Before Deployment

```
Manual Execution Only:
 Open PowerShell
 Navigate to project folder
 Activate virtual environment
 Run: python main.py --mode live
 Bot runs while PowerShell open
 Close PowerShell → Bot stops Computer restarts → Bot doesn't start Bot crashes → Stays crashed No background operation```

### After Deployment

```
Fully Automated Service:
 Computer boots → Service auto-starts Bot runs in background 24/7 Close terminal → Bot keeps running User logs off → Bot keeps running Bot crashes → Service auto-restarts All output logged to files Successfully executing trades 100% signal execution rate
Proven Results:
- Portfolio: $104,400.67
- Trades Executed: 1
- Execution Rate: 100.0%
- Errors: 0
```

---

## How to Use It Now (Reference Guide)

### Check if Bot is Running

```powershell
nssm status BTCTradingBot
```

**Expected:** `SERVICE_RUNNING`

---

### View Live Trading Activity

```powershell
Get-Content logs\bot.log -Wait -Tail 30
```

**Press Ctrl+C to stop watching (bot keeps running)**

---

### Start the Bot

```powershell
nssm start BTCTradingBot
```

**Use when:** After stopping for maintenance

---

### Stop the Bot

```powershell
nssm stop BTCTradingBot
```

**Use when:** Need to update code, change settings

---

### Restart the Bot

```powershell
nssm restart BTCTradingBot
```

**Use when:** After changing environment variables, updating code

---

### View Recent Logs (Last 50 Lines)

```powershell
Get-Content logs\bot.log -Tail 50
```

**Use when:** Want to see what happened without live watching

---

### Check Error Log

```powershell
Get-Content logs\bot_error.log -Tail 50
```

**Use when:** Bot had issues, troubleshooting

---

### Edit Service Configuration

```powershell
nssm edit BTCTradingBot
```

**Opens GUI to change:** Paths, arguments, environment variables

**After editing:** Run `nssm restart BTCTradingBot`

---

### View All Service Settings

```powershell
nssm dump BTCTradingBot
```

**Shows:** Complete configuration as commands

**Use when:** Want to backup config, troubleshoot

---

### Remove Service (When Moving to Cloud)

```powershell
nssm stop BTCTradingBot
nssm remove BTCTradingBot confirm
```

**Warning:** This deletes the service (use when migrating)

---

## Next Time You Boot Your Computer

**What happens automatically:**
```
1. Windows starts
2. Services Manager loads
3. BTCTradingBot service auto-starts
4. Bot begins trading
5. No action needed from you```

**To verify it's running:**
```powershell
# Open PowerShell (doesn't need to be Administrator for checking)
nssm status BTCTradingBot
Get-Content C:\Users\krish\btc-intelligent-trader\logs\bot.log -Tail 20
```

---

## Next Time You Close PowerShell

**What happens:**
```
You close PowerShell → Bot keeps runningService runs independently of terminals
Only way to stop: nssm stop BTCTradingBot
```

---

## Common Management Tasks

### Daily Check

```powershell
# Quick status check
nssm status BTCTradingBot

# See today's activity
Get-Content logs\bot.log -Tail 50
```

---

### Weekly Maintenance

```powershell
# Check for errors
Get-Content logs\bot_error.log

# Verify time sync
w32tm /query /status

# Check disk space (logs grow over time)
Get-ChildItem logs\ | Measure-Object -Property Length -Sum
```

---

### Monthly Cleanup

```powershell
# Archive old logs (if files get large)
Compress-Archive -Path logs\*.log -DestinationPath logs\archive_$(Get-Date -Format yyyyMMdd).zip

# Clear old logs after archiving
Remove-Item logs\bot.log, logs\bot_error.log
nssm restart BTCTradingBot
```

---

## The Cloud Connection (What's Next)

### What We Learned Locally Applies to Cloud

**Local (Windows + NSSM):**
```powershell
nssm install BTCTradingBot
nssm set BTCTradingBot AppEnvironmentExtra "API_KEY=..."
nssm start BTCTradingBot
```

**Cloud (Linux + systemd):**
```bash
sudo systemctl enable btc-trader
Environment="API_KEY=..."
sudo systemctl start btc-trader
```

**Same Concepts:**
- Service creation
- Environment variables
- Auto-start on boot
- Auto-restart on crash
- Log management
- Start/stop/restart commands

**Only Difference:** Command syntax (NSSM vs systemd)

---

### When to Move to Cloud

**Stay Local If:**
- Testing strategy performance
- Computer runs 24/7 anyway
- Want $0 cost
- Learning deployment

**Move to Cloud When:**
- Strategy proven profitable (3+ months)
- Want 99.9% uptime
- Computer not always on
- Ready for ~$10/month cost

---

### Cloud Deployment Preview (Future)

**AWS EC2 Steps (will be similar to local):**

```bash
# 1. Launch EC2 instance (Ubuntu Linux)
# 2. Connect via SSH

# 3. Install Python and UV
sudo apt update
sudo apt install python3 python3-pip
pip install uv

# 4. Clone your code
git clone <your-repo>
cd btc-intelligent-trader

# 5. Setup UV environment (SAME as local)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# 6. Create systemd service (like NSSM, but Linux)
sudo nano /etc/systemd/system/btc-trader.service

# Paste:
[Unit]
Description=BTC Trading Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/btc-intelligent-trader
ExecStart=/home/ubuntu/btc-intelligent-trader/.venv/bin/python main.py --mode live
Environment="BINANCE_TESTNET_API_KEY=your_key"
Environment="BINANCE_TESTNET_SECRET_KEY=your_secret"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# 7. Enable and start (SAME commands as NSSM!)
sudo systemctl enable btc-trader
sudo systemctl start btc-trader

# 8. Check status (SAME concept!)
sudo systemctl status btc-trader

# 9. View logs (SAME concept!)
sudo journalctl -u btc-trader -f
```

**You'll recognize everything because you learned it locally!**
---

## Purpose and Success Summary

### Purpose (Why We Did This)

**Immediate Goal:**
```
Make bot run 24/7 without manual intervention
Learn deployment fundamentals before cloud
Test trading strategy over weeks/months
```

**Educational Goal:**
```
Understand:
- What services are
- How process management works
- Why environment variables matter
- How to troubleshoot deployment issues
```

**Strategic Goal:**
```
Prepare for cloud deployment with:
- Same concepts
- Same logic
- Just different commands
```

---

### Success (What We Achieved)

**Technical Success:**
```
Bot deployed as Windows Service
Auto-starts on boot
Auto-restarts on crash
Logs all activity
Environment variables configured
API authentication working
100% trade execution rate
```

**Practical Success:**
```
First trading cycle:
- Portfolio: $104,400.67
- Signal: BUY $30 (DCA)
- Execution: SUCCESSFUL
- Bought: 0.000320 BTC @ $93,122.39
- Execution Rate: 100.0%
- Errors: 0
```

**Educational Success:**
```
Learned:
Service management (NSSM)
Package management (Chocolatey)
Environment variables (critical nuances)
Time synchronization (API requirements)
Log monitoring (troubleshooting)
Windows administration (PowerShell)
```

---

## Key Learnings (Nuances & Concepts)

### 1. Services vs Programs

**Concept:** Services run independently of user sessions

**Nuance:** Can't just "run Python script" - need service wrapper

**Why:** Background operation, auto-restart, boot-on-start

---

### 2. Environment Variables

**Concept:** Settings that programs read (like API keys)

**Nuance:** Services don't inherit user environment - must set explicitly

**Why:** Security isolation, different execution context

---

### 3. Variable Names & Whitespace

**Concept:** Variables must match EXACTLY what code expects

**Nuance:** One space or wrong name = complete failure

**Why:** String matching is literal, no fuzzy matching

---

### 4. Time Synchronization

**Concept:** API requests must have accurate timestamps

**Nuance:** >1000ms clock difference = rejected

**Why:** Security (prevent replay attacks)

---

### 5. Fresh Starts vs Restarts

**Concept:** Service caches environment on start

**Nuance:** Changing variables mid-session doesn't always work

**Why:** Memory caching for performance

---

## Complete Command Reference

### Installation Commands
```powershell
# Install Chocolatey
Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install NSSM
choco install nssm -y

# Verify installations
choco --version
nssm
```

### Setup Commands
```powershell
# Navigate to project
cd C:\Users\krish\btc-intelligent-trader

# Create logs directory
mkdir logs

# Create service (opens GUI)
nssm install BTCTradingBot

# Set environment variables
nssm set BTCTradingBot AppEnvironmentExtra "BINANCE_TESTNET_API_KEY=your_key" "BINANCE_TESTNET_SECRET_KEY=your_secret"

# Sync system time
w32tm /resync
```

### Management Commands
```powershell
# Start service
nssm start BTCTradingBot

# Stop service
nssm stop BTCTradingBot

# Restart service
nssm restart BTCTradingBot

# Check status
nssm status BTCTradingBot

# View configuration
nssm dump BTCTradingBot

# Edit configuration
nssm edit BTCTradingBot

# Get specific setting
nssm get BTCTradingBot AppEnvironmentExtra

# Remove service
nssm remove BTCTradingBot confirm
```

### Monitoring Commands
```powershell
# Watch live logs
Get-Content logs\bot.log -Wait -Tail 30

# View last 50 lines
Get-Content logs\bot.log -Tail 50

# Check error log
Get-Content logs\bot_error.log -Tail 50

# View log file sizes
Get-ChildItem logs\ | Format-Table Name, Length
```

### Troubleshooting Commands
```powershell
# Check time sync
w32tm /query /status

# Re-sync time
w32tm /resync

# Test API manually
python -c "from src.execution.binance_executor import BinanceExecutor; executor = BinanceExecutor(use_testnet=True); print(executor.get_account_info())"

# Check Python path
Get-Command python

# Verify virtual environment
.\.venv\Scripts\python.exe --version
```

---

**Last Updated:** 2025-12-04
