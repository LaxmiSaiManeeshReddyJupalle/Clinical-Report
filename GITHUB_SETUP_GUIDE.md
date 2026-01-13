# GitHub Repository Setup Guide

## Overview

This guide walks you through creating a new GitHub repository and pushing your Clinical Report Generator code to it.

---

## Prerequisites

- [x] GitHub account (with your new account)
- [x] Git installed on your machine
- [x] VSCode with new GitHub account configured

---

## Step-by-Step Instructions

### Step 1: Create New GitHub Repository

#### Option A: Via GitHub Website (Recommended)

1. **Go to GitHub:**
   - Navigate to: https://github.com
   - Sign in with your new account

2. **Create new repository:**
   - Click the **"+"** icon (top right)
   - Select **"New repository"**

3. **Repository settings:**
   ```
   Repository name: clinical-report-generator
   Description: HIPAA-compliant RAG system for clinical report generation

   Visibility:
     ○ Public
     ● Private  ← RECOMMENDED (contains healthcare code)

   Initialize repository:
     ☐ Add a README file (we already have one)
     ☐ Add .gitignore (we already have one)
     ☐ Choose a license (optional)
   ```

4. **Click "Create repository"**

5. **Copy the repository URL:**
   ```
   Example: https://github.com/YOUR_USERNAME/clinical-report-generator.git
   ```

#### Option B: Via GitHub CLI (Alternative)

```bash
# Install GitHub CLI if not already installed
# macOS: brew install gh

# Authenticate
gh auth login

# Create repository
gh repo create clinical-report-generator --private --source=. --remote=origin
```

---

### Step 2: Verify .env is NOT Tracked

**CRITICAL SECURITY CHECK:**

```bash
cd "/Users/saimanish/Documents/Clinical report"

# Check if .env is listed in .gitignore
grep "^\.env$" .gitignore
# Should output: .env

# Verify .env is NOT staged for commit
git status | grep .env
# Should NOT see .env in the output (it should be ignored)
```

**If .env appears in git status:**
```bash
# Remove from git tracking (keeps the file, just untracks it)
git rm --cached .env
```

---

### Step 3: Configure Git User (Your New Account)

```bash
cd "/Users/saimanish/Documents/Clinical report"

# Set your new GitHub username and email for this repo
git config user.name "Your New GitHub Username"
git config user.email "your-new-email@example.com"

# Verify configuration
git config user.name
git config user.email
```

**Optional: Set globally for all repos**
```bash
git config --global user.name "Your New GitHub Username"
git config --global user.email "your-new-email@example.com"
```

---

### Step 4: Update Remote Repository

```bash
cd "/Users/saimanish/Documents/Clinical report"

# Check current remote
git remote -v
# Shows: origin  https://github.com/ManeeshJupalle/Clinical-Report-.git

# Remove old remote
git remote remove origin

# Add new remote (replace with YOUR repository URL from Step 1)
git remote add origin https://github.com/YOUR_USERNAME/clinical-report-generator.git

# Verify new remote
git remote -v
# Should show your new repository URL
```

---

### Step 5: Stage All New Files

```bash
cd "/Users/saimanish/Documents/Clinical report"

# Add all new documentation files
git add GETTING_STARTED_REAL_DATA.md
git add READONLY_QUICK_CHECK.md
git add READ_ONLY_VERIFICATION.md
git add SAFETY_SUMMARY.md
git add UICFS_CONNECTION_GUIDE.md
git add GITHUB_SETUP_GUIDE.md

# Add utility scripts
git add switch_data_source.py
git add test_smb_connection.py
git add verify_readonly.py

# Check what will be committed
git status
```

**Should see:**
```
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        new file:   GETTING_STARTED_REAL_DATA.md
        new file:   GITHUB_SETUP_GUIDE.md
        new file:   READONLY_QUICK_CHECK.md
        new file:   READ_ONLY_VERIFICATION.md
        new file:   SAFETY_SUMMARY.md
        new file:   UICFS_CONNECTION_GUIDE.md
        new file:   switch_data_source.py
        new file:   test_smb_connection.py
        new file:   verify_readonly.py
```

---

### Step 6: Commit Your Changes

```bash
cd "/Users/saimanish/Documents/Clinical report"

# Create commit
git commit -m "Add comprehensive documentation and security verification

- Add UICFS connection guide with SMB setup instructions
- Add read-only verification tools and documentation
- Add GitHub setup guide
- Add utility scripts for testing and data source switching
- Verified application operates in strict read-only mode

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Verify commit was created
git log -1 --oneline
```

---

### Step 7: Push to GitHub

```bash
cd "/Users/saimanish/Documents/Clinical report"

# Push to new repository
git push -u origin main

# If you get authentication error, you may need to authenticate
```

**Expected output:**
```
Enumerating objects: 15, done.
Counting objects: 100% (15/15), done.
Delta compression using up to 8 threads
Compressing objects: 100% (12/12), done.
Writing objects: 100% (12/12), 75.23 KiB | 7.52 MiB/s, done.
Total 12 (delta 8), reused 0 (delta 0), pack-reused 0
To https://github.com/YOUR_USERNAME/clinical-report-generator.git
   fe28114..abc1234  main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

## Authentication Issues

### If you get "Authentication failed"

#### Method 1: Personal Access Token (Recommended)

1. **Create token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Name: `clinical-report-generator-push`
   - Scopes: Select **`repo`** (full control of private repositories)
   - Click "Generate token"
   - **COPY THE TOKEN** (you won't see it again!)

2. **Use token as password:**
   ```bash
   git push -u origin main
   # Username: your-github-username
   # Password: [paste your token here]
   ```

3. **Save credentials (optional):**
   ```bash
   # macOS - store in Keychain
   git config --global credential.helper osxkeychain

   # Then push again (credentials will be saved)
   git push -u origin main
   ```

#### Method 2: SSH Key (Alternative)

1. **Generate SSH key:**
   ```bash
   ssh-keygen -t ed25519 -C "your-email@example.com"
   # Press Enter to accept default location
   # Enter passphrase (optional)
   ```

2. **Add SSH key to GitHub:**
   ```bash
   # Copy public key to clipboard
   cat ~/.ssh/id_ed25519.pub | pbcopy
   ```

   - Go to: https://github.com/settings/keys
   - Click "New SSH key"
   - Title: `Mac - Clinical Report Generator`
   - Key: Paste from clipboard
   - Click "Add SSH key"

3. **Update remote to use SSH:**
   ```bash
   git remote set-url origin git@github.com:YOUR_USERNAME/clinical-report-generator.git

   # Test connection
   ssh -T git@github.com
   # Should see: "Hi YOUR_USERNAME! You've successfully authenticated..."

   # Push
   git push -u origin main
   ```

---

## Verification

### After successful push:

1. **Check GitHub:**
   - Go to: `https://github.com/YOUR_USERNAME/clinical-report-generator`
   - Verify all files are present
   - Check README.md is displayed

2. **Verify .env is NOT on GitHub:**
   - Search repository for ".env"
   - Should NOT see .env file (it should be ignored)
   - **If you see .env:** Contact me immediately - we need to remove it and rotate credentials!

3. **Check commit history:**
   ```bash
   git log --oneline -5
   ```

---

## Future Workflow

### Making changes and pushing:

```bash
cd "/Users/saimanish/Documents/Clinical report"

# Make your changes to files...

# Check what changed
git status
git diff

# Stage changes
git add <files>
# or add all:
git add .

# Commit
git commit -m "Describe your changes here"

# Push to GitHub
git push

# Or push with co-author attribution:
git commit -m "Your change description

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push
```

### Pulling latest changes:

```bash
cd "/Users/saimanish/Documents/Clinical report"

# Pull latest from GitHub
git pull

# Or if you have local changes:
git stash           # Save local changes
git pull            # Pull remote changes
git stash pop       # Restore local changes
```

---

## Security Checklist

Before every push, verify:

- [ ] `.env` is in `.gitignore`
- [ ] `.env` does NOT appear in `git status`
- [ ] No credentials in source code
- [ ] No patient data in repository
- [ ] No PHI in commit messages

**Check now:**
```bash
# Should output: .env
grep "^\.env$" .gitignore

# Should be empty (no output)
git ls-files | grep "\.env$"

# Search for potential credentials in staged files
git diff --staged | grep -i "password\|secret\|key"
```

---

## Troubleshooting

### Issue: "Permission denied"

**Solution:**
```bash
# Check authentication method
git remote -v

# If using HTTPS, make sure you have valid token
# If using SSH, verify SSH key is added to GitHub
ssh -T git@github.com
```

### Issue: "Updates were rejected"

**Solution:**
```bash
# Pull first, then push
git pull --rebase origin main
git push
```

### Issue: "Remote contains work that you do not have locally"

**Solution:**
```bash
# Force push (CAREFUL - overwrites remote)
git push -f origin main

# Or merge remote changes first
git pull origin main
# Resolve any conflicts
git push origin main
```

### Issue: ".env appears in repository"

**CRITICAL - Remove immediately:**
```bash
# Remove from git tracking
git rm --cached .env

# Commit removal
git commit -m "Remove .env from tracking (should be ignored)"

# Push
git push

# Verify it's gone
# Check GitHub - .env should not be visible

# If .env was previously committed, you need to remove it from history:
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push to rewrite history
git push --force --all
```

**Then:** Immediately change all passwords/credentials in the .env file!

---

## GitHub Repository Settings

### Recommended settings for your new repository:

1. **Access:**
   - Settings → Manage access
   - Keep private (unless you want public)
   - Add collaborators if needed

2. **Branch protection (optional but recommended):**
   - Settings → Branches
   - Add rule for `main` branch:
     - ☑ Require pull request reviews before merging
     - ☑ Require status checks to pass

3. **Security:**
   - Settings → Security & analysis
   - Enable: Dependabot alerts
   - Enable: Secret scanning (if available)

---

## Quick Command Reference

```bash
# Check status
git status

# Add files
git add <file>
git add .

# Commit
git commit -m "message"

# Push
git push

# Pull
git pull

# View history
git log --oneline

# Check remote
git remote -v

# Check what's ignored
git status --ignored
```

---

## Next Steps

After pushing to GitHub:

1. **Add repository description** (on GitHub)
2. **Add topics/tags:** `python`, `healthcare`, `hipaa`, `rag`, `streamlit`, `ollama`
3. **Update README** with your GitHub username/links
4. **Consider:** Adding GitHub Actions for CI/CD (optional)
5. **Share** repository link with collaborators (if private)

---

## Support

If you encounter issues:

1. **Check Git docs:** https://git-scm.com/doc
2. **GitHub docs:** https://docs.github.com
3. **VSCode Git guide:** https://code.visualstudio.com/docs/sourcecontrol/overview

---

**You're ready to push your code to GitHub!** 🚀

Follow the steps above, and your code will be safely backed up and version-controlled.
