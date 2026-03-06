$imageName = "hata-server"
$imageTag = "latest"
$dockerfile = "./fastapi-dockerfile"
$outputTar = "./images/hata-server-latest.tar"
$remoteDir = "/data/images/ruoyi-fastapi-full-stack/images"

# Load deploy config
if (Test-Path ".deploy.env") {
    Get-Content ".deploy.env" | ForEach-Object {
        if ($_ -match '^SERVER_IP=(.+)$') { $serverIp = $matches[1].Trim() }
        elseif ($_ -match '^SERVER_USER=(.+)$') { $serverUser = $matches[1].Trim() }
    }
}

# Build & Save
New-Item -ItemType Directory -Path "./images" -Force | Out-Null
if (Test-Path $outputTar) { Copy-Item -Path $outputTar -Destination "./images/hata-server-$(Get-Date -Format 'yyyyMMdd-HHmmss').tar" -Force }

Write-Host "Building $imageName`:$imageTag..." -ForegroundColor Cyan
docker build -f $dockerfile -t "$imageName`:$imageTag" .
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Saving to $outputTar..." -ForegroundColor Cyan
docker save -o $outputTar "$imageName`:$imageTag"
if ($LASTEXITCODE -ne 0) { exit 1 }

$fileSize = [math]::Round((Get-Item $outputTar).Length / 1MB, 2)
Write-Host "Build completed: $($fileSize)MB" -ForegroundColor Green

# Upload to server
if ($serverIp -and $serverUser) {
    Write-Host "Uploading to $serverUser@$serverIp..." -ForegroundColor Cyan

    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL ${serverUser}@${serverIp} "mkdir -p $remoteDir" 2>&1 | Out-Null
    scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $outputTar ${serverUser}@${serverIp}:${remoteDir}/ 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Uploaded to: ${remoteDir}/hata-server-latest.tar" -ForegroundColor Green

        # 执行服务器上的部署脚本
        Write-Host "Executing deploy script on server..." -ForegroundColor Cyan
        ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL ${serverUser}@${serverIp} "cd /data/images/ruoyi-fastapi-full-stack/scripts && bash deploy-server.sh"

        if ($LASTEXITCODE -eq 0) {
            Write-Host "Deploy script executed successfully" -ForegroundColor Green
        } else {
            Write-Host "Deploy script execution failed" -ForegroundColor Red
        }
    }
}
