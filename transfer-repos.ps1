# GitHub Repository Transfer Script
# Transfers all repos from source owner to target owner

param(
    [string]$SourceOwner = "go4garage2026",
    [string]$TargetOwner = "bisug4g",
    [string]$GitHubToken = $env:GITHUB_TOKEN
)

# Validate inputs
if (-not $GitHubToken) {
    Write-Error "GitHub token not found. Set GITHUB_TOKEN environment variable or pass -GitHubToken parameter"
    exit 1
}

# GitHub API headers
$headers = @{
    "Authorization" = "token $GitHubToken"
    "Accept" = "application/vnd.github.v3+json"
}

Write-Host "🔍 Fetching repositories for owner: $SourceOwner" -ForegroundColor Cyan

# Get all repos owned by source owner
$page = 1
$repos = @()

do {
    $response = Invoke-RestMethod -Uri "https://api.github.com/users/$SourceOwner/repos?type=owner&per_page=100&page=$page" `
        -Headers $headers -ErrorAction Stop
    
    if ($response.Count -eq 0) { break }
    
    $repos += $response
    $page++
} while ($response.Count -eq 100)

if ($repos.Count -eq 0) {
    Write-Host "❌ No repositories found for owner: $SourceOwner" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Found $($repos.Count) repository(ies)" -ForegroundColor Green
Write-Host ""

# Display repos to transfer
Write-Host "📋 Repositories to transfer:" -ForegroundColor Yellow
$repos | ForEach-Object { Write-Host "   - $($_.name)" }
Write-Host ""

# Confirm before transferring
$confirmation = Read-Host "⚠️  Proceed with transferring these repos to $TargetOwner ? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "❌ Transfer cancelled" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "🚀 Starting transfer..." -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failureCount = 0

# Transfer each repo
foreach ($repo in $repos) {
    $repoName = $repo.name
    Write-Host "Transferring: $repoName..." -NoNewline
    
    try {
        $transferUrl = "https://api.github.com/repos/$SourceOwner/$repoName/transfer"
        $body = @{
            "new_owner" = $TargetOwner
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri $transferUrl `
            -Method POST `
            -Headers $headers `
            -Body $body `
            -ErrorAction Stop
        
        Write-Host " ✅ Success" -ForegroundColor Green
        $successCount++
    }
    catch {
        Write-Host " ❌ Failed" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
        $failureCount++
    }
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "📊 Transfer Summary:" -ForegroundColor Cyan
Write-Host "   ✅ Successful: $successCount" -ForegroundColor Green
Write-Host "   ❌ Failed: $failureCount" -ForegroundColor Red
Write-Host "================================" -ForegroundColor Cyan
