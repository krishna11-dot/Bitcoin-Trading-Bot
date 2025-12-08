# Git Commands Reference - Complete GitHub Upload Process

**Date**: 2025-12-07
**Task**: Upload BTC Intelligent Trading Bot to GitHub
**Repository**: https://github.com/krishna11-dot/Bitcoin-Trading-Bot
**Status**: ✅ Successfully Completed

---

## Table of Contents

1. [Repository Initialization](#1-repository-initialization)
2. [Staging Files](#2-staging-files)
3. [Creating Commits](#3-creating-commits)
4. [Security Fixes](#4-security-fixes)
5. [Connecting to GitHub](#5-connecting-to-github)
6. [Pushing to Remote](#6-pushing-to-remote)
7. [Handling Merge Conflicts](#7-handling-merge-conflicts)
8. [Updating Repository](#8-updating-repository)
9. [Verification Commands](#9-verification-commands)

---

## 1. Repository Initialization

### Command: `git init`

**What It Does:**
Creates a new Git repository in the current directory by initializing a hidden `.git` folder.

**Purpose:**
Transform your project folder into a Git-tracked repository so you can save version history.

**Command:**
```bash
git init
```

**Expected Output:**
```
Initialized empty Git repository in C:/Users/krish/btc-intelligent-trader/.git/
```

**Success Criteria:**
- ✅ `.git` folder created (hidden folder)
- ✅ Your folder is now a Git repository
- ✅ Git can now track changes

**What Happened:**
- Git created a `.git` folder containing:
  - `objects/` - Stores all file versions
  - `refs/` - Stores branch pointers
  - `config` - Repository configuration
  - `HEAD` - Points to current branch

---

## 2. Staging Files

### Command: `git add .`

**What It Does:**
Adds all files in the current directory to the staging area (preparing them for commit).

**Purpose:**
Select which files you want to include in the next snapshot (commit). The `.` means "add everything in current directory."

**Command:**
```bash
git add .
```

**Expected Output:**
```
warning: in the working copy of '.env.example', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of '.gitignore', LF will be replaced by CRLF the next time Git touches it
[... more warnings about line endings ...]
```

**Success Criteria:**
- ✅ Files moved to staging area
- ⚠️ Line ending warnings are normal (Git auto-converts LF ↔ CRLF)
- ✅ `.gitignore` is respected (ignored files NOT added)

**What Happened:**
- Git scanned all files in the folder
- Added them to "staging area" (preparing for commit)
- **Respected `.gitignore`** - did NOT add:
  - `.env` (actual API keys)
  - `venv/` (virtual environment)
  - `config/*.json` (credentials)
  - `logs/` (log files)

**Important Notes:**
- Line ending warnings (LF/CRLF) are HARMLESS
- Git auto-converts between Unix (LF) and Windows (CRLF) line endings
- You can safely ignore these warnings

---

### Command: `git add <specific-file>`

**What It Does:**
Adds only the specified file(s) to staging area.

**Purpose:**
When you want to selectively add files instead of everything.

**Example:**
```bash
git add README.md FINAL_GITHUB_STEP.md
```

**Success Criteria:**
- ✅ Only specified files added to staging
- ✅ Other changed files remain unstaged

**Use Cases:**
- Adding files one-by-one for better commit organization
- Adding resolved merge conflict files
- Staging specific changes while keeping others uncommitted

---

## 3. Creating Commits

### Command: `git commit -m "message"`

**What It Does:**
Saves a snapshot of all staged files with a descriptive message.

**Purpose:**
Create a checkpoint in your project's history that you can return to later.

**Command:**
```bash
git commit -m "Initial commit: BTC Intelligent Trading Bot with ML, technical analysis, and automated risk management. Includes DCA/Swing strategies, Telegram/Gmail notifications, RAG system, and comprehensive documentation."
```

**Breaking Down the Command:**
- `git commit` - Create a snapshot
- `-m` - Message flag (what changed)
- `"..."` - Your commit message (be descriptive!)

**Expected Output:**
```
[main (root-commit) abc1234] Initial commit: BTC Intelligent Trading Bot...
 87 files changed, 12458 insertions(+)
 create mode 100644 .gitignore
 create mode 100644 README.md
 create mode 100644 main.py
 [... list of all files ...]
```

**Success Criteria:**
- ✅ Commit created with unique ID (abc1234)
- ✅ Shows number of files changed (87 files)
- ✅ Shows total lines added (12458 insertions)
- ✅ Lists all files included in commit

**What Happened:**
- Git saved a snapshot of all staged files
- Assigned unique commit ID (e.g., `abc1234`)
- Stored commit message for future reference
- **Snapshot saved to LOCAL repository** (not yet on GitHub)

**Good Commit Message Example:**
```bash
git commit -m "Add RandomForest ML model with 10 essential features for price prediction"
```

**Bad Commit Message Examples:**
```bash
git commit -m "changes"           # Too vague
git commit -m "fix"               # What was fixed?
git commit -m "asdfasdf"          # Meaningless
```

---

### Command: `git commit --amend -m "new message"`

**What It Does:**
Modifies the most recent commit (changes files or message).

**Purpose:**
Fix mistakes in the last commit before pushing to GitHub.

**Command:**
```bash
git commit --amend -m "Initial commit: BTC Intelligent Trading Bot (sensitive files removed)"
```

**Expected Output:**
```
[main abc1235] Initial commit: BTC Intelligent Trading Bot (sensitive files removed)
 Date: Sat Dec 7 15:30:45 2025 +0530
 86 files changed, 12458 insertions(+)
```

**Success Criteria:**
- ✅ Commit ID changed (abc1234 → abc1235)
- ✅ New message applied
- ✅ Previous commit replaced (not duplicated)

**When to Use:**
- Remove accidentally committed files
- Fix typos in commit message
- Add forgotten files to last commit

**⚠️ WARNING:**
- **ONLY use on commits not yet pushed to GitHub**
- Never amend commits that others have pulled
- Never amend commits on shared branches

---

## 4. Security Fixes

### Command: `git rm --cached <file>`

**What It Does:**
Removes file from Git tracking (staging area) but keeps it on your computer.

**Purpose:**
Remove sensitive files that were accidentally staged without deleting them from disk.

**Command:**
```bash
git rm --cached config/gmail_token.pickle
```

**Breaking Down the Command:**
- `git rm` - Remove file
- `--cached` - From staging area only (keep local copy)
- `config/gmail_token.pickle` - File to remove

**Expected Output:**
```
rm 'config/gmail_token.pickle'
```

**Success Criteria:**
- ✅ File removed from staging area
- ✅ File still exists on your computer
- ✅ Git will no longer track this file

**What Happened:**
- File removed from Git's tracking index
- Local file remains untouched
- Next commit will NOT include this file

**Common Use Case:**
```bash
# Accidentally added .env file
git add .env

# Remove it from staging
git rm --cached .env

# Verify it's gone from staging
git status
```

---

### Command: `git ls-files | grep -E "pattern"`

**What It Does:**
Lists all files tracked by Git and filters for specific patterns.

**Purpose:**
Security check - verify sensitive files are NOT being tracked.

**Command:**
```bash
git ls-files | grep -E "(\.env$|gmail_credentials\.json|token\.pickle|gmail_token\.pickle|service_account\.json)"
```

**Breaking Down the Command:**
- `git ls-files` - List all files Git is tracking
- `|` - Pipe (send output to next command)
- `grep -E` - Search for patterns (extended regex)
- `"pattern"` - Files to search for

**Expected Output (Good):**
```
# No output = no sensitive files found ✅
```

**Expected Output (Bad):**
```
.env                           # ❌ BAD - Remove this!
config/gmail_credentials.json  # ❌ BAD - Remove this!
```

**Success Criteria:**
- ✅ No sensitive files listed
- ✅ Only safe files (.env.example, .env.template) are tracked

**Security Patterns to Check:**
```bash
# Check for environment files
git ls-files | grep -E "\.env$"

# Check for credential files
git ls-files | grep -E "credentials\.json|token\.pickle|service_account\.json"

# Check for all sensitive patterns at once
git ls-files | grep -E "(\.env$|credentials|token|secret|password)"
```

---

## 5. Connecting to GitHub

### Command: `git remote add origin <URL>`

**What It Does:**
Connects your local Git repository to a remote GitHub repository.

**Purpose:**
Tell Git where to upload (push) your code on GitHub.

**Command:**
```bash
git remote add origin https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git
```

**Breaking Down the Command:**
- `git remote add` - Add a remote server
- `origin` - Name for this remote (standard name)
- `https://...` - Your GitHub repository URL

**Expected Output:**
```
# No output = success ✅
```

**Success Criteria:**
- ✅ Remote "origin" added
- ✅ Git knows where to push code

**Verification:**
```bash
git remote -v
```

**Expected Verification Output:**
```
origin  https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git (fetch)
origin  https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git (push)
```

**What Happened:**
- Git saved GitHub URL as "origin"
- "origin" is the default name for the main remote
- Git now knows where to push/pull code

**Common Remote Names:**
- `origin` - Your main GitHub repository
- `upstream` - Original repository (if you forked)
- `backup` - Backup remote server

---

### Command: `git branch -M main`

**What It Does:**
Renames the current branch to "main" (or creates it if it doesn't exist).

**Purpose:**
Ensure your default branch matches GitHub's standard ("main" instead of "master").

**Command:**
```bash
git branch -M main
```

**Breaking Down the Command:**
- `git branch` - Branch management command
- `-M` - Move/rename branch (force)
- `main` - New branch name

**Expected Output:**
```
# No output = success ✅
```

**Success Criteria:**
- ✅ Current branch renamed to "main"
- ✅ Matches GitHub's default branch name

**Why This Matters:**
- GitHub uses "main" as default branch
- Git (older versions) uses "master" as default
- Renaming prevents branch mismatch errors

**Verification:**
```bash
git branch
```

**Expected Verification Output:**
```
* main
```

---

## 6. Pushing to Remote

### Command: `git push -u origin main`

**What It Does:**
Uploads your commits to GitHub and sets "origin/main" as the default upstream branch.

**Purpose:**
Upload your code to GitHub for backup and sharing.

**Command:**
```bash
git push -u origin main
```

**Breaking Down the Command:**
- `git push` - Upload commits to remote
- `-u` - Set upstream (remember this branch)
- `origin` - Remote name (GitHub)
- `main` - Branch to push

**Expected Output (Success):**
```
Enumerating objects: 135, done.
Counting objects: 100% (135/135), done.
Delta compression using up to 8 threads
Compressing objects: 100% (120/120), done.
Writing objects: 100% (135/135), 487.34 KiB | 5.12 MiB/s, done.
Total 135 (delta 38), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (38/38), done.
To https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

**Success Criteria:**
- ✅ Objects enumerated and compressed
- ✅ Writing objects: 100%
- ✅ `[new branch] main -> main` (branch created on GitHub)
- ✅ Branch tracking set up

**What Happened:**
- Git compressed your files
- Uploaded commits to GitHub
- Created "main" branch on GitHub
- Set "origin/main" as default upstream

**After First Push:**
Next time you can just use:
```bash
git push
```
Git remembers `origin main` because of `-u` flag.

---

### Command: `git push` (Subsequent Pushes)

**What It Does:**
Uploads commits to the default upstream branch (set by `-u` previously).

**Purpose:**
Quick push without specifying remote and branch.

**Command:**
```bash
git push
```

**Expected Output:**
```
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 8 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 1.24 KiB | 1.24 MiB/s, done.
Total 3 (delta 2), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (2/2), completed with 2 local objects.
To https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git
   d2da254..2fbd6f9  main -> main
```

**Success Criteria:**
- ✅ Commits uploaded
- ✅ Shows commit range (d2da254..2fbd6f9)
- ✅ `main -> main` (local to remote)

**Commit Range Explanation:**
- `d2da254` - Previous commit on GitHub
- `2fbd6f9` - New commit you just pushed
- `main -> main` - Local main → Remote main

---

## 7. Handling Merge Conflicts

### Issue: Push Rejected (Remote Has Different History)

**Error Message:**
```
! [rejected]        main -> main (fetch first)
error: failed to push some refs to 'https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git'
hint: Updates were rejected because the remote contains work that you do not
hint: have locally. This is usually caused by another repository pushing to
hint: the same ref. If you want to integrate the remote changes, use
hint: 'git pull' before pushing again.
```

**Cause:**
GitHub repository has a README.md created online that differs from your local README.md.

**Solution:**
Pull remote changes and merge them with your local changes.

---

### Command: `git pull origin main --allow-unrelated-histories --no-edit`

**What It Does:**
Downloads changes from GitHub and merges them with your local repository.

**Purpose:**
Combine GitHub's version with your local version.

**Command:**
```bash
git pull origin main --allow-unrelated-histories --no-edit
```

**Breaking Down the Command:**
- `git pull` - Download and merge
- `origin main` - From GitHub's main branch
- `--allow-unrelated-histories` - Merge different Git histories
- `--no-edit` - Use default merge message

**Expected Output (Merge Conflict):**
```
From https://github.com/krishna11-dot/Bitcoin-Trading-Bot
 * branch            main       -> FETCH_HEAD
Auto-merging README.md
CONFLICT (add/add): Merge conflict in README.md
Automatic merge failed; fix conflicts and then commit the result.
```

**Success Criteria:**
- ✅ Remote changes downloaded
- ⚠️ Merge conflict detected in README.md
- ➡️ Next step: Resolve conflict

**What Happened:**
- Git downloaded GitHub's README.md
- Tried to merge with your local README.md
- Found conflicts (different content)
- Stopped and asked you to resolve

---

### Command: `git checkout --ours <file>`

**What It Does:**
Resolves merge conflict by keeping YOUR version (local version).

**Purpose:**
Choose your local file over GitHub's version.

**Command:**
```bash
git checkout --ours README.md
```

**Breaking Down the Command:**
- `git checkout` - Switch versions
- `--ours` - Keep our version (local)
- `README.md` - File with conflict

**Alternative: `git checkout --theirs <file>`**
```bash
git checkout --theirs README.md  # Keep GitHub's version
```

**Expected Output:**
```
# No output = success ✅
```

**Success Criteria:**
- ✅ Conflict resolved
- ✅ Your local README.md kept
- ✅ GitHub's README.md discarded

**Verification:**
```bash
git status
```

**Expected Verification Output:**
```
On branch main
All conflicts fixed but you are still merging.
  (use "git commit" to conclude merge)

Changes to be committed:
        modified:   README.md
```

---

### Command: `git add <file>` (After Conflict Resolution)

**What It Does:**
Marks the conflict as resolved by staging the file.

**Purpose:**
Tell Git "I've resolved this conflict, ready to commit."

**Command:**
```bash
git add README.md
```

**Expected Output:**
```
# No output = success ✅
```

**Success Criteria:**
- ✅ File marked as resolved
- ✅ Ready for merge commit

---

### Command: `git commit -m "Merge message"`

**What It Does:**
Completes the merge by creating a merge commit.

**Purpose:**
Finalize the merge after resolving conflicts.

**Command:**
```bash
git commit -m "Merge remote README - using local comprehensive version"
```

**Expected Output:**
```
[main d2da254] Merge remote README - using local comprehensive version
```

**Success Criteria:**
- ✅ Merge commit created
- ✅ Conflict resolution complete
- ✅ Ready to push

**What Happened:**
- Git created a special "merge commit"
- Combined both histories (local + remote)
- Your README.md version kept
- Merge complete

---

## 8. Updating Repository

### Typical Update Workflow

After making changes to your code, follow this sequence:

**Step 1: Check what changed**
```bash
git status
```

**Expected Output:**
```
On branch main
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
        modified:   README.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        FINAL_GITHUB_STEP.md
```

**Step 2: Stage changes**
```bash
git add README.md FINAL_GITHUB_STEP.md
```

**Step 3: Commit changes**
```bash
git commit -m "Update README: Add natural language interface, ML limitations, and GCP deployment"
```

**Expected Output:**
```
[main 2fbd6f9] Update README: Add natural language interface, ML limitations, and GCP deployment
 2 files changed, 228 insertions(+), 13 deletions(-)
 create mode 100644 FINAL_GITHUB_STEP.md
```

**Step 4: Push to GitHub**
```bash
git push
```

**Expected Output:**
```
To https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git
   d2da254..2fbd6f9  main -> main
```

**Success Criteria:**
- ✅ Changes committed locally
- ✅ Changes uploaded to GitHub
- ✅ GitHub repository updated

---

## 9. Verification Commands

### Command: `git status`

**What It Does:**
Shows the current state of your working directory and staging area.

**Purpose:**
See what files have changed and what's ready to commit.

**Command:**
```bash
git status
```

**Expected Output (Clean):**
```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

**Expected Output (Changes):**
```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
        modified:   README.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        new_file.md
```

**What It Shows:**
- Current branch (main)
- Sync status with GitHub
- Modified files (red)
- Staged files (green)
- Untracked files (red)

**Use Cases:**
- Before committing (see what will be included)
- After making changes (verify what changed)
- Before pushing (ensure everything committed)

---

### Command: `git log --oneline -N`

**What It Does:**
Shows commit history in compact format.

**Purpose:**
View recent commits with their IDs and messages.

**Command:**
```bash
git log --oneline -2
```

**Breaking Down the Command:**
- `git log` - Show commit history
- `--oneline` - Compact format (one line per commit)
- `-2` - Show last 2 commits

**Expected Output:**
```
2fbd6f9 Update README: Add natural language interface, ML limitations, and GCP deployment
d2da254 Merge remote README - using local comprehensive version
```

**What It Shows:**
- `2fbd6f9` - Commit ID (first 7 characters)
- Message - What changed in this commit

**Full Log:**
```bash
git log
```

**Full Log Output:**
```
commit 2fbd6f9a3c5e7b9d1f2a4c6e8b0d2f4a6c8e0b2d
Author: krishna11-dot <email@example.com>
Date:   Sat Dec 7 16:45:30 2025 +0530

    Update README: Add natural language interface, ML limitations, and GCP deployment

commit d2da254b1a3c5e7b9d1f2a4c6e8b0d2f4a6c8e0
Author: krishna11-dot <email@example.com>
Date:   Sat Dec 7 15:30:45 2025 +0530

    Merge remote README - using local comprehensive version
```

---

### Command: `git remote -v`

**What It Does:**
Shows configured remote repositories with their URLs.

**Purpose:**
Verify which GitHub repository you're connected to.

**Command:**
```bash
git remote -v
```

**Expected Output:**
```
origin  https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git (fetch)
origin  https://github.com/krishna11-dot/Bitcoin-Trading-Bot.git (push)
```

**What It Shows:**
- `origin` - Remote name
- URL for fetching (downloading)
- URL for pushing (uploading)

**Verification:**
- ✅ Correct GitHub username
- ✅ Correct repository name
- ✅ HTTPS URL (not SSH)

---

### Command: `git ls-files | wc -l`

**What It Does:**
Counts how many files Git is tracking.

**Purpose:**
Verify total number of files in repository.

**Command:**
```bash
git ls-files | wc -l
```

**Breaking Down the Command:**
- `git ls-files` - List all tracked files
- `|` - Pipe output to next command
- `wc -l` - Count lines (each file = 1 line)

**Expected Output:**
```
88
```

**Success Criteria:**
- ✅ Shows total tracked files (88 in this case)

**Verification:**
```bash
# List all tracked files
git ls-files

# Count files in specific folder
git ls-files | grep "^docs/" | wc -l
```

---

### Command: `git diff`

**What It Does:**
Shows changes in files that are NOT yet staged.

**Purpose:**
Review what you changed before staging/committing.

**Command:**
```bash
git diff
```

**Expected Output:**
```diff
diff --git a/README.md b/README.md
index abc1234..def5678 100644
--- a/README.md
+++ b/README.md
@@ -1,5 +1,5 @@
 # BTC Intelligent Trader

-A simple Bitcoin trading bot.
+A sophisticated Bitcoin trading bot that uses machine learning.
```

**What It Shows:**
- `-` Red lines = Removed
- `+` Green lines = Added
- Context lines (unchanged)

**Variations:**
```bash
# Show staged changes
git diff --cached

# Show changes in specific file
git diff README.md

# Show changes between commits
git diff abc1234 def5678
```

---

## Quick Reference Cheat Sheet

### First-Time Upload to GitHub

```bash
# 1. Initialize repository
git init

# 2. Add all files
git add .

# 3. Check what will be committed
git status

# 4. Create first commit
git commit -m "Initial commit: Description of project"

# 5. Connect to GitHub
git remote add origin https://github.com/username/repository.git

# 6. Rename branch to main
git branch -M main

# 7. Push to GitHub
git push -u origin main
```

---

### Daily Workflow (After Initial Setup)

```bash
# 1. Check what changed
git status

# 2. Stage changes
git add .
# Or specific files:
git add file1.md file2.py

# 3. Commit with message
git commit -m "Descriptive message of what changed"

# 4. Push to GitHub
git push
```

---

### Security Check Before Pushing

```bash
# Check for sensitive files
git ls-files | grep -E "(\.env$|credentials|token|secret|password)"

# Should return nothing ✅

# If sensitive files found, remove them:
git rm --cached .env
git commit --amend -m "Remove sensitive files"
```

---

### Undoing Mistakes

```bash
# Unstage file (keep changes)
git reset HEAD <file>

# Discard local changes (DANGEROUS - cannot undo)
git checkout -- <file>

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) (DANGEROUS)
git reset --hard HEAD~1

# Amend last commit (before pushing)
git commit --amend -m "New message"
```

---

## Command Summary Table

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `git init` | Create repository | First time only |
| `git add .` | Stage all files | Before committing |
| `git add <file>` | Stage specific file | Selective staging |
| `git status` | Check status | Before every commit |
| `git commit -m "msg"` | Save snapshot | After staging |
| `git push` | Upload to GitHub | Share changes |
| `git pull` | Download from GitHub | Get updates |
| `git log` | View history | Check commits |
| `git remote -v` | Check remote | Verify GitHub URL |
| `git rm --cached <file>` | Untrack file | Remove from Git |
| `git checkout --ours <file>` | Keep local version | Resolve conflicts |
| `git diff` | Show changes | Review before commit |

---

## Success Criteria for GitHub Upload

### Before Pushing
- [ ] No sensitive files in staging (`git ls-files | grep -E "\.env"`)
- [ ] `.gitignore` properly configured
- [ ] Meaningful commit message written
- [ ] Changes reviewed (`git status`, `git diff`)

### After Pushing
- [ ] Push completed without errors
- [ ] GitHub shows all files
- [ ] README.md displayed correctly
- [ ] No `.env` or credentials visible on GitHub
- [ ] Commit history shows your commits (`git log`)

---

## Common Issues & Solutions

### Issue 1: "Permission denied (publickey)"

**Solution:** Use Personal Access Token
```bash
# When prompted for password, use your Personal Access Token
# Get token from: https://github.com/settings/tokens
```

---

### Issue 2: "Updates rejected (fetch first)"

**Solution:** Pull and merge
```bash
git pull origin main --allow-unrelated-histories --no-edit
# Resolve conflicts if any
git push
```

---

### Issue 3: ".env file was pushed!"

**Solution:** Remove and rotate keys
```bash
# Remove from Git
git rm --cached .env
git commit -m "Remove .env from version control"
git push -f origin main

# IMPORTANT: Rotate all API keys on respective platforms
# (.env contents are now public - keys compromised!)
```

---

### Issue 4: "Merge conflict in file"

**Solution:** Choose version to keep
```bash
# Keep your version
git checkout --ours <file>

# Or keep GitHub's version
git checkout --theirs <file>

# Then complete merge
git add <file>
git commit -m "Resolve merge conflict"
git push
```

---

## Your GitHub Upload Journey

### What We Did

1. ✅ **Initialized repository** (`git init`)
2. ✅ **Staged 87 files** (`git add .`)
3. ✅ **Created initial commit** (`git commit -m "..."`)
4. ✅ **Fixed security issue** (`git rm --cached gmail_token.pickle`)
5. ✅ **Connected to GitHub** (`git remote add origin ...`)
6. ✅ **Renamed branch** (`git branch -M main`)
7. ✅ **Pushed to GitHub** (`git push -u origin main`)
8. ✅ **Resolved merge conflict** (`git checkout --ours README.md`)
9. ✅ **Updated README** (`git commit -m "Update README..."`)
10. ✅ **Pushed updates** (`git push`)

### Final Result

- **Repository**: https://github.com/krishna11-dot/Bitcoin-Trading-Bot
- **Files Tracked**: 88 files
- **Commits**: 3 commits
- **Security**: All sensitive files excluded
- **Status**: ✅ Fully operational

---

## Learning Outcomes

### What You Learned

1. **Git Basics**: init, add, commit, push
2. **Security**: How to exclude sensitive files with `.gitignore`
3. **Remote Repositories**: Connecting to GitHub
4. **Merge Conflicts**: Resolving when local and remote differ
5. **Verification**: Checking what's being tracked
6. **Workflow**: Daily git usage for updates

### Skills Gained

- ✅ Version control with Git
- ✅ GitHub repository management
- ✅ Security best practices (never commit secrets)
- ✅ Conflict resolution
- ✅ Command line proficiency

---

**Last Updated**: 2025-12-07
**Status**: Complete Reference Guide
**Repository**: https://github.com/krishna11-dot/Bitcoin-Trading-Bot
