# 本地打包前端为tar - 输出到frontend目录

Write-Host "start..." -ForegroundColor Green

# 构建
Set-Location frontend
pnpm build
Set-Location ..

# 打包
Set-Location frontend\dist
tar -cf ..\hata-frontend-latest.tar .
Set-Location ..\..

Write-Host "complete: frontend\hata-frontend-latest.tar" -ForegroundColor Cyan
Get-Item frontend\hata-frontend-latest.tar | Format-Table Name, @{Label="Size";Expression={"{0:N2} KB" -f ($_.Length/1KB)}}
