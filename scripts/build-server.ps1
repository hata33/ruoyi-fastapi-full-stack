$imageName = "hata-server"
$imageTag = "latest"
$dockerfile = "./fastapi-dockerfile"
$imagesDir = "./images"
$outputTar = "$imagesDir/hata-server-latest.tar"

# 确保 images 目录存在
if (-not (Test-Path $imagesDir)) {
    New-Item -ItemType Directory -Path $imagesDir -Force | Out-Null
    Write-Host "Created directory: $imagesDir" -ForegroundColor Cyan
}

# 处理已存在的镜像包
if (Test-Path $outputTar) {
    $backupPath = "$outputTar.backup"
    Write-Host "Found existing image: $outputTar" -ForegroundColor Yellow
    Write-Host "Backing up to: $backupPath" -ForegroundColor Yellow

    try {
        Move-Item -Path $outputTar -Destination $backupPath -Force
        Write-Host "Backup created" -ForegroundColor Green
    }
    catch {
        Write-Host "Backup failed, removing old file..." -ForegroundColor Red
        Remove-Item -Path $outputTar -Force
    }
}

# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker not found" -ForegroundColor Red
    exit 1
}
Write-Host "Docker: $(docker --version)" -ForegroundColor Green

# Build image
Write-Host ""
Write-Host "Building Docker image..." -ForegroundColor Cyan
docker build -f $dockerfile -t "$imageName`:$imageTag" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed" -ForegroundColor Red
    exit 1
}

# Save image
Write-Host ""
Write-Host "Saving image to $outputTar..." -ForegroundColor Cyan
docker save -o $outputTar "$imageName`:$imageTag"

if ($LASTEXITCODE -eq 0 -and (Test-Path $outputTar)) {
    $fileSize = (Get-Item $outputTar).Length / 1MB
    Write-Host ""
    Write-Host "==== Build Completed ====" -ForegroundColor Green
    Write-Host "Image: ${imageName}:${imageTag}" -ForegroundColor White
    Write-Host "File:  $outputTar" -ForegroundColor White
    Write-Host "Size:  $([math]::Round($fileSize, 2)) MB" -ForegroundColor White
} else {
    Write-Host "Save failed" -ForegroundColor Red
    exit 1
}
