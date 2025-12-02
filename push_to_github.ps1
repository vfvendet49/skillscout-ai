# PowerShell script to push changes to GitHub
# Make sure Git is installed first: https://git-scm.com/download/win

Write-Host "Checking Git installation..." -ForegroundColor Yellow
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Git is not installed!" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Git is installed. Proceeding..." -ForegroundColor Green

# Check if this is already a git repository
if (-not (Test-Path .git)) {
    Write-Host "Initializing git repository..." -ForegroundColor Yellow
    git init
}

# Check if remote is already configured
$remoteUrl = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Adding remote repository..." -ForegroundColor Yellow
    git remote add origin https://github.com/vfvendet49/skillscout-ai.git
} else {
    Write-Host "Remote already configured: $remoteUrl" -ForegroundColor Green
    Write-Host "Updating remote URL..." -ForegroundColor Yellow
    git remote set-url origin https://github.com/vfvendet49/skillscout-ai.git
}

# Add all changes
Write-Host "Adding all changes..." -ForegroundColor Yellow
git add .

# Commit changes
Write-Host "Committing changes..." -ForegroundColor Yellow
git commit -m "Fix project structure: consolidate duplicate files, add missing functions, update dependencies and endpoints"

# Check current branch
$branch = git branch --show-current 2>$null
if (-not $branch) {
    Write-Host "Creating main branch..." -ForegroundColor Yellow
    git branch -M main
    $branch = "main"
}

Write-Host "Current branch: $branch" -ForegroundColor Green

# Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "Note: You may be prompted for GitHub credentials." -ForegroundColor Cyan
git push -u origin $branch

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully pushed to GitHub!" -ForegroundColor Green
} else {
    Write-Host "Push failed. You may need to:" -ForegroundColor Red
    Write-Host "1. Set up GitHub authentication (Personal Access Token)" -ForegroundColor Yellow
    Write-Host "2. Or use: git push -u origin $branch --force (if you need to overwrite remote)" -ForegroundColor Yellow
}

