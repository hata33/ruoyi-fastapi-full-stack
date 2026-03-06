param([switch]$SkipBuild, [switch]$SkipUpload, [switch]$SkipRestart)

Set-Location (Split-Path $PSScriptRoot)

# Load config
$cfg = @{}
Get-Content ".deploy.env" | ForEach-Object {
    if ($_ -match '^(.+?)=(.+)$') { $cfg[$matches[1]] = $matches[2] }
}

$tar = "./frontend-dist.tar"
$sshUser = "$($cfg.SERVER_USER)@$($cfg.SERVER_IP)"

# Build
if (-not $SkipBuild) {
    Write-Host "Building..." -ForegroundColor Cyan
    Set-Location frontend; pnpm build; Set-Location ..
}

# Pack, Upload & Deploy
if (-not $SkipUpload) {
    Write-Host "Deploying..." -ForegroundColor Cyan
    if (Test-Path $tar) { Remove-Item $tar -Force }
    tar -cf $tar -C frontend/dist .
    scp -o StrictHostKeyChecking=no $tar "${sshUser}:/tmp/"
    ssh -o StrictHostKeyChecking=no $sshUser "cd $($cfg.REMOTE_DIR)/.. && rm -rf html.bak && mv html html.bak 2>/dev/null; mkdir -p /tmp/deploy && tar -xf /tmp/frontend-dist.tar -C /tmp/deploy && mv /tmp/deploy $($cfg.REMOTE_DIR) && rm -f /tmp/frontend-dist.tar && rm -rf html.bak"
}

# Reload nginx
if (-not $SkipRestart) {
    Write-Host "Reloading nginx..." -ForegroundColor Cyan
    ssh -o StrictHostKeyChecking=no $sshUser "docker restart $($cfg.NGINX_CONTAINER)"
}

if (Test-Path $tar) { Remove-Item $tar -Force }
Write-Host "Done!" -ForegroundColor Green
