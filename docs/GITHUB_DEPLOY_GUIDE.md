# GitHub Deployment Guide - Bitcoin Trading Bot System

**Repository**: https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System

This guide helps you securely push your Bitcoin trading bot to GitHub with NO sensitive data exposed.

---

## Security Checklist

### What's Already Protected

 **API Keys**: All keys are in `.env` (excluded from git)
 **Tokens**: OAuth tokens in `config/*.pickle` (excluded from git)
 **Credentials**: Service account JSON files (excluded from git)
 **Personal Paths**: No hardcoded `C:\Users\krish` paths found
 **Email**: No personal email addresses in code
 **Large Files**: CSV data and models (excluded from git)

### What You MUST Check Before Pushing

- [ ] `.env` file is NOT staged (git status should NOT show .env)
- [ ] `config/` folder is NOT staged
- [ ] No `.pickle` or `.json` files in `config/`
- [ ] Logs folder is empty or excluded
- [ ] Data folder only has README, not actual CSV files

---

## Step-by-Step Deployment

### Step 1: Configure Git Authorship 

```bash
# Set YOUR name and email 
git config user.name "Krishna Nair"
git config user.email "krishnanair041@gmail.com"

# Verify configuration
git config user.name
git config user.email
```



---

### Step 2: Update Git Remote to Correct Repository

```bash
# Remove old remote
git remote remove origin

# Add correct repository
git remote add origin https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System.git

# Verify
git remote -v
```

**Expected output**:
```
origin  https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System.git (fetch)
origin  https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System.git (push)
```

---

### Step 3: Final Security Check

```bash
# Check what will be uploaded
git status

# Should NOT see:
# - .env
# - config/gmail_credentials.json
# - config/*.pickle
# - *.log files
# - Large .csv files
```

If you see any sensitive files, add them to `.gitignore` immediately:

```bash
echo "filename.ext" >> .gitignore
```

---

### Step 4: Create Clean Commit

```bash
# Stage all files
git add .

# Create commit (NO Claude references)
git commit -m "Bitcoin Trading Bot System - Complete Implementation

Features:
- ML-based trading with RandomForest predictions
- DCA and Swing trading strategies
- Natural language interface with Gemini AI
- MCP integration for live prices
- RAG system for pattern matching
- Multi-notification system (Telegram, Gmail, Sheets)
- Comprehensive backtesting engine

Developed by: Krishna Nair"
```

---

### Step 5: Push to GitHub

```bash
# Push to main branch
git push -u origin main

# If main doesn't exist, create it:
git branch -M main
git push -u origin main
```

---

### Step 6: Verify on GitHub

1. Go to: https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System
2. Check commit history:
   
3. Check files:
   - `.env` should NOT be visible
   - `config/` folder should only have README or be empty
   - No API keys visible in any file

---

## What Gets Uploaded vs Excluded

###  Uploaded to GitHub

```
✓ Source code (.py files)
✓ Documentation (.md files)
✓ Configuration examples (.env.example)
✓ Requirements (requirements.txt)
✓ Project structure folders
✓ Tests
✓ README and guides
```

###  Excluded from GitHub (Private)

```
✗ .env (API keys)
✗ config/*.json (credentials)
✗ config/*.pickle (OAuth tokens)
✗ data/raw/*.csv (large files)
✗ logs/*.log (execution logs)
✗ .venv/ (virtual environment)
✗ __pycache__/ (Python cache)
```

---

## Creating .env.example (Template for Others)

Create a template so others can use your bot:

```bash
# Create example environment file
cat > .env.example << 'EOF'
# API Keys (Get your own from respective platforms)
BINANCE_API_KEY=your_binance_key_here
BINANCE_SECRET_KEY=your_binance_secret_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
COINGECKO_DEMO_API_KEY=your_coingecko_key_here

# Google Configuration
GOOGLE_SHEET_ID=your_google_sheet_id_here

# Email Settings (optional)
GMAIL_USER=your_email@gmail.com

# Gemini Smart Rotation (optional)
GEMINI_USE_ROTATION=true
GEMINI_ROTATION_STRATEGY=round_robin
EOF

# Add to git
git add .env.example
git commit -m "Add environment template for setup"
git push
```

---

## Emergency: If You Accidentally Pushed Secrets

If you accidentally pushed API keys or tokens:

### 1. **Immediately Revoke All Keys**

- Binance: Regenerate API keys
- Telegram: Revoke bot token via @BotFather
- Gemini: Regenerate API key in Google AI Studio
- CoinGecko: Regenerate API key

### 2. **Remove from Git History**

```bash
# Install BFG Repo Cleaner
# Download from: https://rtyley.github.io/bfg-repo-cleaner/

# Remove sensitive file from ALL commits
java -jar bfg.jar --delete-files .env

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (DANGER!)
git push --force
```

### 3. **Update README with Warning**

Add to README:
```markdown
## Security Notice
Never commit your .env file. Always use .env.example as template.
```

---

## Post-Upload Checklist

After pushing to GitHub:

- [ ] Repository is public/private as intended
- [ ] README looks good on GitHub
- [ ] All documentation renders correctly
- [ ] No `.env` file visible
- [ ] No `config/*.json` files visible
- [ ] Commit author shows "Krishna Nair" (not Claude)
- [ ] No references to Claude Code in commits
- [ ] `.env.example` exists for others to use

---

## Maintaining the Repository

### Adding New Features

```bash
# Make changes to code
# ...

# Commit with YOUR authorship
git add .
git commit -m "Add new feature: XYZ

Implemented by: Krishna Nair"

# Push
git push
```

### Never Commit These

```bash
# Add to .gitignore if you create new sensitive files
echo "new_secret_file.json" >> .gitignore
```

---

## Summary

**Before Every Push**:
1. Check `git status` - ensure no `.env` or sensitive files
2. Review commit message
3. Verify authorship - should be "Krishna Nair"
4. Push with confidence!

**Your Repository**: https://github.com/krishna11-dot/Bitcoin-Trading-Bot-System

**Author**: Krishna Nair
**License**: MIT (or your choice)
**Contact**: krishnanair041@gmail.com (optional in README)

---

## Need Help?

If something goes wrong:
1. DON'T panic
2. DON'T force push without understanding
3. Check this guide first
4. Revoke any exposed API keys IMMEDIATELY
5. Ask for help if needed

**Remember**: Once something is on GitHub, assume it's public forever. Always double-check before pushing!
