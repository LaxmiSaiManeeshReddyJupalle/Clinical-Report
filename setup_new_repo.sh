#!/bin/bash

# =============================================================================
# GitHub Repository Setup Script
# UIC Clinical Report Generator
# =============================================================================
# This script helps you set up a new GitHub repository and push your code
# =============================================================================

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}  GitHub Repository Setup${NC}"
echo -e "${BLUE}  UIC Clinical Report Generator${NC}"
echo -e "${BLUE}======================================================================${NC}\n"

# Step 1: Get user information
echo -e "${YELLOW}Step 1: Repository Information${NC}\n"

read -p "Enter your new GitHub username: " GITHUB_USERNAME
read -p "Enter your email for Git commits: " GIT_EMAIL
read -p "Enter new repository name (default: clinical-report-generator): " REPO_NAME
REPO_NAME=${REPO_NAME:-clinical-report-generator}

NEW_REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

echo -e "\n${BLUE}Repository will be:${NC} $NEW_REPO_URL\n"
read -p "Is this correct? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo -e "${RED}Setup cancelled.${NC}"
    exit 1
fi

# Step 2: Verify .env is ignored
echo -e "\n${YELLOW}Step 2: Security Check${NC}\n"

if ! grep -q "^\.env$" .gitignore; then
    echo -e "${RED}ERROR: .env is not in .gitignore!${NC}"
    echo "Adding .env to .gitignore..."
    echo ".env" >> .gitignore
fi

if git ls-files | grep -q "^\.env$"; then
    echo -e "${RED}WARNING: .env is tracked by git!${NC}"
    read -p "Remove .env from git tracking? (y/n): " REMOVE_ENV
    if [ "$REMOVE_ENV" = "y" ]; then
        git rm --cached .env
        echo -e "${GREEN}✓ .env removed from tracking${NC}"
    else
        echo -e "${RED}ERROR: Cannot proceed with .env tracked!${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Security check passed - .env is not tracked${NC}"

# Step 3: Configure Git user
echo -e "\n${YELLOW}Step 3: Configure Git User${NC}\n"

git config user.name "$GITHUB_USERNAME"
git config user.email "$GIT_EMAIL"

echo -e "${GREEN}✓ Git user configured:${NC}"
echo -e "  Name:  $(git config user.name)"
echo -e "  Email: $(git config user.email)"

# Step 4: Update remote
echo -e "\n${YELLOW}Step 4: Update Remote Repository${NC}\n"

echo "Current remote:"
git remote -v

echo -e "\nRemoving old remote..."
git remote remove origin || true

echo "Adding new remote: $NEW_REPO_URL"
git remote add origin "$NEW_REPO_URL"

echo -e "${GREEN}✓ Remote updated:${NC}"
git remote -v

# Step 5: Stage new files
echo -e "\n${YELLOW}Step 5: Stage New Files${NC}\n"

# Add documentation
git add -f GETTING_STARTED_REAL_DATA.md 2>/dev/null || true
git add -f READONLY_QUICK_CHECK.md 2>/dev/null || true
git add -f READ_ONLY_VERIFICATION.md 2>/dev/null || true
git add -f SAFETY_SUMMARY.md 2>/dev/null || true
git add -f UICFS_CONNECTION_GUIDE.md 2>/dev/null || true
git add -f GITHUB_SETUP_GUIDE.md 2>/dev/null || true

# Add scripts
git add -f switch_data_source.py 2>/dev/null || true
git add -f test_smb_connection.py 2>/dev/null || true
git add -f verify_readonly.py 2>/dev/null || true
git add -f setup_new_repo.sh 2>/dev/null || true

echo -e "${GREEN}✓ New files staged${NC}"
echo ""
git status --short

# Step 6: Commit
echo -e "\n${YELLOW}Step 6: Create Commit${NC}\n"

COMMIT_MESSAGE="Add comprehensive documentation and verification tools

- Add UICFS connection guide with SMB setup
- Add read-only security verification
- Add GitHub repository setup guide
- Add utility scripts for testing
- Verified strict read-only operation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git commit -m "$COMMIT_MESSAGE"

echo -e "${GREEN}✓ Commit created${NC}"
git log -1 --oneline

# Step 7: Ask about repository creation
echo -e "\n${YELLOW}Step 7: Create GitHub Repository${NC}\n"

echo -e "${BLUE}IMPORTANT: Before pushing, create the repository on GitHub:${NC}"
echo ""
echo "1. Go to: https://github.com/new"
echo "2. Repository name: ${REPO_NAME}"
echo "3. Visibility: Private (recommended for healthcare code)"
echo "4. DO NOT initialize with README, .gitignore, or license"
echo "5. Click 'Create repository'"
echo ""

read -p "Have you created the repository on GitHub? (y/n): " REPO_CREATED

if [ "$REPO_CREATED" != "y" ]; then
    echo -e "${YELLOW}Please create the repository first, then run:${NC}"
    echo -e "  git push -u origin main"
    exit 0
fi

# Step 8: Push
echo -e "\n${YELLOW}Step 8: Push to GitHub${NC}\n"

echo "Pushing to: $NEW_REPO_URL"
echo ""
echo -e "${YELLOW}Note: You may be prompted for your GitHub credentials.${NC}"
echo -e "${YELLOW}      If using HTTPS, use a Personal Access Token as password.${NC}"
echo ""

if git push -u origin main; then
    echo -e "\n${GREEN}======================================================================${NC}"
    echo -e "${GREEN}  ✓ SUCCESS!${NC}"
    echo -e "${GREEN}======================================================================${NC}\n"
    echo -e "${GREEN}Your code has been pushed to:${NC}"
    echo -e "  https://github.com/${GITHUB_USERNAME}/${REPO_NAME}\n"
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Visit your repository on GitHub"
    echo "  2. Verify .env is NOT visible (should be ignored)"
    echo "  3. Add repository description and topics"
    echo "  4. Configure branch protection (optional)"
    echo ""
else
    echo -e "\n${RED}======================================================================${NC}"
    echo -e "${RED}  Push failed${NC}"
    echo -e "${RED}======================================================================${NC}\n"
    echo -e "${YELLOW}Common issues:${NC}"
    echo ""
    echo "1. Authentication failed?"
    echo "   → Create Personal Access Token at: https://github.com/settings/tokens"
    echo "   → Use token as password when prompted"
    echo ""
    echo "2. Repository doesn't exist?"
    echo "   → Create it first at: https://github.com/new"
    echo ""
    echo "3. Wrong username/repo name?"
    echo "   → Check remote: git remote -v"
    echo ""
    echo "Try pushing manually:"
    echo "  git push -u origin main"
    echo ""
fi
