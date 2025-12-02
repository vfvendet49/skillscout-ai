# GitHub Authentication Fix

The push failed because Git is using the wrong GitHub account credentials. Here are the solutions:

## Option 1: Use Personal Access Token (Recommended)

1. **Create a Personal Access Token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Name it: "skillscout-ai-push"
   - Select scope: `repo` (full control of private repositories)
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again!)

2. **Push using the token:**
   ```powershell
   git push -u origin main
   ```
   - When prompted for username: enter `vfvendet49`
   - When prompted for password: paste your **Personal Access Token** (not your GitHub password)

## Option 2: Update Git Credentials

Clear stored credentials and re-authenticate:

```powershell
# Clear stored credentials
git credential-manager-core erase
# Or on Windows:
cmdkey /list
cmdkey /delete:git:https://github.com
```

Then try pushing again - it will prompt for new credentials.

## Option 3: Use SSH Instead of HTTPS

1. **Generate SSH key** (if you don't have one):
   ```powershell
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. **Add SSH key to GitHub:**
   - Copy the public key: `cat ~/.ssh/id_ed25519.pub`
   - Go to: https://github.com/settings/keys
   - Click "New SSH key" and paste it

3. **Change remote to SSH:**
   ```powershell
   git remote set-url origin git@github.com:vfvendet49/skillscout-ai.git
   git push -u origin main
   ```

## Quick Fix (Try This First)

Run this command and when prompted, use:
- Username: `vfvendet49`
- Password: Your Personal Access Token (from Option 1)

```powershell
git push -u origin main
```

