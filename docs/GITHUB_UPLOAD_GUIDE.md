# GitHub Upload Guide - Step by Step

## 🎯 Goal
Upload your BTC trading bot code to GitHub repository: `krishna11-dot/Bitcoin-Trading-Bot`

**Repository URL**: https://github.com/krishna11-dot/Bitcoin-Trading-Bot

---

## ⚠️ CRITICAL - Security First!

Before uploading, you MUST ensure sensitive data is NOT uploaded:

### ❌ NEVER Upload These Files:
- `.env` - Contains your actual API keys and tokens
- `config/gmail_credentials.json` - Gmail OAuth credentials
- `config/token.pickle` - Gmail access tokens
- `config/service_account.json` - Google Sheets credentials
- `logs/*` - May contain sensitive trading data
- `data/rag_vectordb/*` - Large vector database files
- `.venv/` or `venv/` - Python virtual environment (too large)

### ✅ SAFE to Upload:
- `.env.example` - Template with placeholder values
- `.env.template` - Template with placeholder values
- All `.py` source code files
- `requirements.txt` - Dependencies list
- `README.md` - Documentation
- `docs/` - All documentation
- `.gitignore` - Tells Git what NOT to upload

---

## 📋 What is Git and GitHub? (Simple Explanation)

### Git (Version Control System)
**What it is**: Like "Track Changes" in Microsoft Word, but for code.

**What it does**:
- Saves snapshots of your code (called "commits")
- Lets you go back to previous versions
- Tracks who changed what and when

**Think of it as**: A time machine for your code

### GitHub (Cloud Storage for Git)
**What it is**: Like Google Drive or Dropbox, but specifically for code.

**What it does**:
- Stores your Git snapshots online
- Backs up your code
- Lets others see your code (if public)
- Provides collaboration tools

**Think of it as**: Your code's cloud backup and portfolio

### Key Concepts

1. **Repository (Repo)**: A folder containing your project + Git history
   - You already created one: `Bitcoin-Trading-Bot`

2. **Commit**: A snapshot of your code at a specific time
   - Like saving a document, but with a description of changes
   - Example: "Added RandomForest ML model"

3. **Push**: Upload your local commits to GitHub
   - Like uploading files to Google Drive

4. **Pull**: Download changes from GitHub to your computer
   - Like downloading files from Google Drive

5. **Remote**: The GitHub server where your code lives
   - Usually called "origin"

6. **Branch**: A separate line of development
   - Default branch: "main" or "master"
   - Like having multiple drafts of the same document

---

## 🚀 Step-by-Step Upload Process

### Method 1: Using Git Command Line (Recommended)

#### Step 1: Install Git (If Not Installed)

**Check if Git is installed**:
```powershell
git --version
```

**If you see "command not found"**, install Git:
1. Download: https://git-scm.com/download/win
2. Run installer (accept all defaults)
3. Restart PowerShell
4. Verify: `git --version`

---

#### Step 2: Open PowerShell in Your Project

```powershell
# Navigate to your project
cd C:\Users\krish\btc-intelligent-trader
```

---

#### Step 3: Initialize Git Repository

**What this does**: Tells Git to start tracking changes in this folder.

```powershell
git init
```

**Expected output**:
```
Initialized empty Git repository in C:/Users/krish/btc-intelligent-trader/.git/
```

**What happened**:
- Created hidden `.git` folder
- This folder stores all version history
- Your folder is now a Git repository

---

#### Step 4: Check .gitignore File

**What .gitignore does**: Tells Git which files to NEVER upload (like .env with your secrets).

**Verify it exists**:
```powershell
cat .gitignore
```

**Expected content** (should already be there):
```
# Environment variables (NEVER upload!)
.env
.env.local

# Credentials (NEVER upload!)
config/gmail_credentials.json
config/token.pickle
config/service_account.json

# Logs (may contain sensitive data)
logs/
*.log

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
env/

# Data files
data/rag_vectordb/
*.db
*.sqlite

# IDE
.vscode/
.idea/
*.swp
```

**If .gitignore doesn't exist**, create it:
```powershell
# Create .gitignore
notepad .gitignore
```

Paste the content above, save, and close.

---

#### Step 5: Add Files to Git Staging Area

**What "staging" means**: Selecting which files to include in the next snapshot (commit).

**Think of it as**: Choosing which photos to add to an album before saving the album.

```powershell
# Add all files (respects .gitignore)
git add .
```

**What this does**:
- Scans all files in the folder
- Adds them to "staging area" (preparing for commit)
- **Ignores** files in .gitignore (like .env)

**Verify what's staged**:
```powershell
git status
```

**Expected output** (example):
```
On branch main

No commits yet

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
        new file:   .gitignore
        new file:   README.md
        new file:   main.py
        new file:   requirements.txt
        new file:   src/modules/module1_technical.py
        ...

Untracked files not listed due to .gitignore
```

**⚠️ IMPORTANT CHECK**:
- Should see: `new file: .gitignore`, `new file: .env.example`
- Should NOT see: `.env`, `config/gmail_credentials.json`, `venv/`

**If you see .env listed**:
```powershell
# Remove it from staging
git rm --cached .env
```

---

#### Step 6: Create Your First Commit

**What a commit is**: A snapshot of your code with a description.

```powershell
git commit -m "Initial commit: BTC Intelligent Trading Bot"
```

**Breaking down the command**:
- `git commit`: Save a snapshot
- `-m`: Message flag (describes what changed)
- `"Initial commit..."`: Your message (be descriptive!)

**Expected output**:
```
[main (root-commit) abc1234] Initial commit: BTC Intelligent Trading Bot
 45 files changed, 3421 insertions(+)
 create mode 100644 .gitignore
 create mode 100644 README.md
 ...
```

**What happened**:
- Created snapshot of all staged files
- Assigned unique ID (abc1234)
- Saved to local Git history
- **NOT yet on GitHub** (still only on your computer)

---

#### Step 7: Connect to GitHub Repository

**What "remote" means**: The GitHub server where your code will live.

```powershell
git remote add origin https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git
```

**Breaking down the command**:
- `git remote add`: Connect to a remote server
- `origin`: Name for this remote (standard name)
- `https://github.com/...`: Your GitHub repository URL

**Verify connection**:
```powershell
git remote -v
```

**Expected output**:
```
origin  https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git (fetch)
origin  https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git (push)
```

**What happened**:
- Saved GitHub URL as "origin"
- Git now knows where to push/pull
- Like saving a cloud storage URL

---

#### Step 8: Rename Branch to "main" (GitHub Standard)

**Why**: GitHub uses "main" as default branch, Git might use "master".

```powershell
git branch -M main
```

**What this does**:
- Renames current branch to "main"
- Ensures compatibility with GitHub

---

#### Step 9: Push Code to GitHub (Upload!)

**What "push" means**: Upload your commits to GitHub.

```powershell
git push -u origin main
```

**Breaking down the command**:
- `git push`: Upload commits
- `-u origin main`: Set "origin/main" as default upstream
- Means: "Remember this, so next time I just type `git push`"

**First time, you'll be prompted for credentials**:

**Option A: GitHub asks for username/password**:
- **Username**: `krishna11-dot`
- **Password**: Use **Personal Access Token** (NOT your GitHub password)

**How to create Personal Access Token**:
1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Name: `btc-trading-bot-upload`
4. Scopes: Check **`repo`** (full control of private repositories)
5. Click **"Generate token"**
6. **COPY THE TOKEN** (you won't see it again!)
7. Use this as your password

**Option B: GitHub Desktop Login**:
- Browser opens automatically
- Click **"Authorize"**

**Expected output** (after successful authentication):
```
Enumerating objects: 45, done.
Counting objects: 100% (45/45), done.
Delta compression using up to 8 threads
Compressing objects: 100% (40/40), done.
Writing objects: 100% (45/45), 125.34 KiB | 3.50 MiB/s, done.
Total 45 (delta 12), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (12/12), done.
To https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

**What happened**:
- ✅ Uploaded all commits to GitHub
- ✅ Created "main" branch on GitHub
- ✅ Your code is now backed up in the cloud!

---

#### Step 10: Verify Upload on GitHub

1. Go to: https://github.com/krishna11-dot/Bitcoin-Trading-Bot
2. Refresh the page
3. You should see:
   - ✅ All your files and folders
   - ✅ README.md displayed at the bottom
   - ✅ Commit message: "Initial commit: BTC Intelligent Trading Bot"
   - ❌ NO `.env` file (good!)
   - ❌ NO `config/gmail_credentials.json` (good!)

---

### Method 2: Using GitHub Desktop (GUI - Easier for Beginners)

**If you prefer a visual interface**:

#### Step 1: Install GitHub Desktop

1. Download: https://desktop.github.com/
2. Install and open
3. Sign in with your GitHub account

#### Step 2: Add Your Repository

1. Click **"Add"** → **"Add existing repository"**
2. Browse to: `C:\Users\krish\btc-intelligent-trader`
3. Click **"Add repository"**

#### Step 3: Make Initial Commit

1. You'll see all changed files
2. **⚠️ CHECK**: Make sure `.env` is NOT listed
3. Add commit message: "Initial commit: BTC Intelligent Trading Bot"
4. Click **"Commit to main"**

#### Step 4: Publish to GitHub

1. Click **"Publish repository"**
2. **Repository name**: `Bitcoin-Trading-Bot`
3. **⚠️ IMPORTANT**: Uncheck "Keep this code private" (if you want it public)
4. Click **"Publish repository"**

Done! Your code is on GitHub.

---

## 🔄 Making Changes Later (Workflow)

### After You Modify Code:

```powershell
# 1. Check what changed
git status

# 2. Stage all changes
git add .

# 3. Commit with message
git commit -m "Improved RandomForest features with lag features"

# 4. Push to GitHub
git push
```

**Each commit should**:
- Have a clear message describing WHAT changed
- Be a logical unit of work (one feature, one fix)

**Good commit messages**:
- ✅ "Added lag features to RandomForest model"
- ✅ "Fixed API key whitespace issue"
- ✅ "Updated README with GCP deployment guide"

**Bad commit messages**:
- ❌ "Updated files"
- ❌ "Changes"
- ❌ "asdfasdf"

---

## 🛡️ Security Checklist (Before Every Push)

**Before you push, ALWAYS check**:

```powershell
# See what files will be uploaded
git status

# See actual content of staged files
git diff --cached
```

**Red flags** (STOP and remove these):
- ❌ `.env` file listed
- ❌ Files in `config/` with credentials
- ❌ `token.pickle`
- ❌ Files with API keys/tokens/passwords

**How to remove accidentally staged file**:
```powershell
git rm --cached .env
git commit -m "Remove .env from tracking"
```

---

## 📊 Common Git Commands

| Command | What It Does | When to Use |
|---------|--------------|-------------|
| `git status` | Show changed files | Before every commit |
| `git add .` | Stage all changes | Preparing to commit |
| `git commit -m "msg"` | Save snapshot | After making changes |
| `git push` | Upload to GitHub | Share your changes |
| `git pull` | Download from GitHub | Get others' changes |
| `git log` | Show commit history | See what changed when |
| `git diff` | Show file changes | Review before commit |

---

## 🚨 Common Issues & Solutions

### Issue 1: "Permission denied (publickey)"

**Cause**: GitHub can't verify your identity.

**Solution**: Use Personal Access Token (see Step 9).

### Issue 2: ".env file was uploaded!"

**Panic mode** - Remove it immediately:

```powershell
# Remove from Git tracking
git rm --cached .env

# Commit the removal
git commit -m "Remove .env from version control"

# Force push (overwrites GitHub)
git push -f origin main
```

**Then**: Go to GitHub → Settings → Secrets → Rotate all API keys (they're compromised).

### Issue 3: "Repository already exists"

**Cause**: You already have a repo with that name on GitHub.

**Solution**: Either delete old repo or use different name.

### Issue 4: Upload is too slow / times out

**Cause**: Large files (like `venv/`, `data/rag_vectordb/`).

**Solution**: Ensure `.gitignore` excludes these.

---

## 🎯 Quick Reference Card

### First Time Setup
```powershell
cd C:\Users\krish\btc-intelligent-trader
git init
git add .
git commit -m "Initial commit: BTC Intelligent Trading Bot"
git remote add origin https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git
git branch -M main
git push -u origin main
```

### Regular Updates
```powershell
git status          # Check changes
git add .           # Stage changes
git commit -m "msg" # Commit changes
git push            # Upload to GitHub
```

### Undo Mistakes
```powershell
git reset HEAD <file>    # Unstage file
git checkout -- <file>   # Discard local changes
git reset --soft HEAD~1  # Undo last commit (keep changes)
```

---

## ✅ Success Criteria

You've successfully uploaded when:
- [ ] GitHub shows all your code files
- [ ] README.md is displayed correctly
- [ ] `.env` file is NOT visible on GitHub
- [ ] No credential files are visible
- [ ] Commit history shows your commits

---

## 📚 Next Steps After Upload

1. **Add a description** to your GitHub repo:
   - Go to repo page → Click "⚙️" → Add description
   - Example: "Intelligent Bitcoin trading bot using ML and technical analysis"

2. **Add topics** (tags for discoverability):
   - bitcoin, trading-bot, machine-learning, python, algorithmic-trading

3. **Star your own repo** (optional):
   - Shows confidence in your project

4. **Share the link**:
   - Add to your resume, LinkedIn, portfolio

---

## 🎓 Learning Resources

- **Git Tutorial**: https://git-scm.com/book/en/v2
- **GitHub Guides**: https://guides.github.com/
- **Interactive Git**: https://learngitbranching.js.org/

---

**You're ready to upload!** Follow the steps and you'll have your code on GitHub in 10 minutes. 🚀
