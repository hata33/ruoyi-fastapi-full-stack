Write-Host "Starting build process..." -ForegroundColor Cyan
cd ./frontend
pnpm build

# Check if build succeeded
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed! Please check for errors." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Build succeeded. Starting to pack the 'dist' directory..." -ForegroundColor Cyan
tar -czvf dist.tgz dist

# Check if packaging succeeded
if ($LASTEXITCODE -eq 0) {
    Write-Host "Packaging completed! 'dist.tgz' has been generated." -ForegroundColor Green
} else {
    Write-Host "Packaging failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}