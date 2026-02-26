# Build and upload frontend, then reload nginx
# Usage: .\deploy-frontend.ps1 [--skip-build]
$ErrorActionPreference = "Stop"

# Parse args
$skipBuild = $args -contains '--skip-build'

# Load config
$envFile = Join-Path $PSScriptRoot "..\.deploy.env"
if (-not (Test-Path $envFile)) { exit "Error: .deploy.env not found" }

$cfg = @{}
Get-Content $envFile | Where-Object { $_ -match '^\w+=' } | ForEach-Object {
    $k, $v = $_ -split '=', 2
    $cfg[$k.Trim()] = $v.Trim()
}

$nginxContainer = $cfg.NGINX_CONTAINER
if (-not $nginxContainer) { $nginxContainer = "hata-nginx" }

Set-Location (Split-Path $PSScriptRoot)

# Build
if (-not $skipBuild) {
    Write-Host "[1/3] Building..." -ForegroundColor Cyan
    Set-Location frontend
    pnpm run build
    if ($LASTEXITCODE -ne 0) { exit "Build failed" }
    Set-Location ..
} else {
    Write-Host "[1/3] Building... (skipped)" -ForegroundColor Gray
}

# Upload
Write-Host "[2/3] Uploading..." -ForegroundColor Cyan
if (-not (Test-Path $cfg.LOCAL_DIST)) {
    exit "Error: $($cfg.LOCAL_DIST) not found"
}

$bash = "C:\Program Files\Git\bin\bash.exe"
if (-not (Test-Path $bash)) { $bash = "bash.exe" }

$localPath = $cfg.LOCAL_DIST.Replace('\', '/')
$cmd = "scp -r -o StrictHostKeyChecking=no ${localPath}/* $($cfg.SERVER_USER)@$($cfg.SERVER_IP):$($cfg.REMOTE_DIR)/"
& $bash -c "ssh -o StrictHostKeyChecking=no $($cfg.SERVER_USER)@$($cfg.SERVER_IP) 'mkdir -p $($cfg.REMOTE_DIR)' && $cmd"

if ($LASTEXITCODE -ne 0) { exit "Error: Upload failed" }

# Reload nginx
Write-Host "[3/3] Reloading nginx ($nginxContainer)..." -ForegroundColor Cyan
& $bash -c "ssh -o StrictHostKeyChecking=no $($cfg.SERVER_USER)@$($cfg.SERVER_IP) 'docker restart $nginxContainer'"

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Deploy complete" -ForegroundColor Green
} else {
    Write-Host "[Warning] Nginx reload failed, but files uploaded" -ForegroundColor Yellow
}
