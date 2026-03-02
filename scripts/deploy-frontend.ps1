# Build and upload frontend, then reload nginx
# Usage:
#   .\deploy-frontend.ps1                    # 完整执行
#   .\deploy-frontend.ps1 -SkipBuild         # 跳过打包
#   .\deploy-frontend.ps1 -SkipBuild -SkipUpload    # 只重启
#   .\deploy-frontend.ps1 -SkipBuild -SkipRestart   # 只上传
#   .\deploy-frontend.ps1 -SkipRestart       # 打包+上传
param(
    [switch]$SkipBuild,
    [switch]$SkipUpload,
    [switch]$SkipRestart
)

$ErrorActionPreference = "Stop"

# Load config
$cfg = @{}
Get-Content "$(Split-Path $PSScriptRoot)\.deploy.env" | Where-Object { $_ -match '^\w+=' } | ForEach-Object {
    $k, $v = $_ -split '=', 2
    $cfg[$k.Trim()] = $v.Trim()
}

$bash = "C:\Program Files\Git\bin\bash.exe"
if (-not (Test-Path $bash)) { $bash = "bash.exe" }

Set-Location (Split-Path $PSScriptRoot)

# 1. Build
if (-not $SkipBuild) {
    Write-Host "[1/3] Building..." -ForegroundColor Cyan
    Set-Location frontend
    pnpm run build
    Set-Location ..
} else {
    Write-Host "[1/3] Building... (skipped)" -ForegroundColor Gray
}

# 2. Upload
if (-not $SkipUpload) {
    Write-Host "[2/3] Uploading..." -ForegroundColor Cyan
    $localPath = $cfg.LOCAL_DIST.Replace('\', '/')
    $remote = "$($cfg.SERVER_USER)@$($cfg.SERVER_IP):$($cfg.REMOTE_DIR)/"
    & $bash -c "ssh -o StrictHostKeyChecking=no $($cfg.SERVER_USER)@$($cfg.SERVER_IP) 'mkdir -p $($cfg.REMOTE_DIR)' && scp -r -o StrictHostKeyChecking=no ${localPath}/* $remote"
} else {
    Write-Host "[2/3] Uploading... (skipped)" -ForegroundColor Gray
}

# 3. Reload nginx
if (-not $SkipRestart) {
    Write-Host "[3/3] Reloading nginx ($($cfg.NGINX_CONTAINER))..." -ForegroundColor Cyan
    & $bash -c "ssh -o StrictHostKeyChecking=no $($cfg.SERVER_USER)@$($cfg.SERVER_IP) 'docker restart $($cfg.NGINX_CONTAINER)'"
} else {
    Write-Host "[3/3] Reloading nginx... (skipped)" -ForegroundColor Gray
}

Write-Host "[OK] Done" -ForegroundColor Green
