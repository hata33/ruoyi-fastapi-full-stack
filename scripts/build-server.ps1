<#
.SYNOPSIS
    hata Server Docker Image Build Script (PowerShell)

.DESCRIPTION
    Build Docker image and export as tar file
    Output: hata-server-latest.tar
    Image name: hata-server:latest

.PARAMETER Clean
    Clean old images and files before building

.PARAMETER NoColor
    Disable colored output

.EXAMPLE
    .\build-server.ps1
    Basic build

.EXAMPLE
    .\build-server.ps1 -Clean
    Build with cleanup

.EXAMPLE
    .\build-server.ps1 -NoColor
    Build without colored output

.NOTES
    Requires Docker Desktop and PowerShell 5.1+
#>

[CmdletBinding()]
param(
    [switch]$Clean,
    [switch]$NoColor
)

# =============================================================================
# Configuration and Initialization
# =============================================================================

# Error handling preferences
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Configuration variables
$Script:Config = @{
    ImageName = "hata-server"
    ImageTag = "latest"
    DockerfilePath = "./fastapi-dockerfile"
    OutputTarFile = "hata-server-latest.tar"
    BuildContext = "."
}

# Color configuration
$Script:Colors = @{
    Red = if ($NoColor) { "" } else { "Red" }
    Green = if ($NoColor) { "" } else { "Green" }
    Yellow = if ($NoColor) { "" } else { "Yellow" }
    Blue = if ($NoColor) { "" } else { "Blue" }
    Cyan = if ($NoColor) { "" } else { "Cyan" }
    White = if ($NoColor) { "" } else { "White" }
    Reset = if ($NoColor) { "" } else { "White" }
}

# =============================================================================
# Utility Functions
# =============================================================================

function Write-ColorMessage {
    param(
        [string]$Message,
        [string]$Color = "White",
        [switch]$NoNewline
    )

    $colorValue = $Script:Colors[$Color]
    if ($colorValue -and -not $NoColor) {
        Write-Host $Message -ForegroundColor $colorValue -NoNewline:$NoNewline
    } else {
        Write-Host $Message -NoNewline:$NoNewline
    }
}

function Write-Step {
    param([string]$Message)

    Write-Host ""
    Write-ColorMessage "==== $Message ====" "Blue"
    Write-Host ""
}

function Write-Info {
    param([string]$Message)
    Write-ColorMessage "[INFO] " "Blue" -NoNewline
    Write-Host $Message
}

function Write-Success {
    param([string]$Message)
    Write-ColorMessage "[SUCCESS] " "Green" -NoNewline
    Write-Host $Message
}

function Write-Warn {
    param([string]$Message)
    Write-ColorMessage "[WARN] " "Yellow" -NoNewline
    Write-Host $Message
}

function Write-Error-Msg {
    param([string]$Message)
    Write-ColorMessage "[ERROR] " "Red" -NoNewline
    Write-Host $Message
}

function Test-Command {
    param([string]$Command)

    try {
        $null = Get-Command $Command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Format-FileSize {
    param([long]$Size)

    $units = @("B", "KB", "MB", "GB", "TB")
    $size = [double]$Size
    $unitIndex = 0

    while ($size -ge 1024 -and $unitIndex -lt $units.Count - 1) {
        $size /= 1024
        $unitIndex++
    }

    return "{0:N2} {1}" -f $size, $units[$unitIndex]
}

# =============================================================================
# Main Functions
# =============================================================================

function Test-DockerEnvironment {
    Write-Step "Checking Docker Environment"

    # Check if Docker command is available
    if (-not (Test-Command "docker")) {
        Write-Error-Msg "Docker is not installed or not in PATH"
        Write-Info "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
        exit 1
    }

    # Display Docker version info (this also confirms Docker is working)
    try {
        $dockerVersion = docker --version 2>&1
        if ($dockerVersion) {
            Write-Success "Docker environment check passed"
            Write-Info "Docker version: $dockerVersion"
        } else {
            Write-Error-Msg "Cannot get Docker version"
            exit 1
        }
    } catch {
        Write-Error-Msg "Docker command failed: $($_.Exception.Message)"
        exit 1
    }
}

function Remove-OldArtifacts {
    Write-Step "Cleaning Old Files"

    $imageName = $Script:Config.ImageName
    $imageTag = $Script:Config.ImageTag
    $fullImageName = "$imageName`:$imageTag"
    $outputTarFile = $Script:Config.OutputTarFile

    # Clean old images
    try {
        $imageId = docker images -q "$fullImageName" 2>$null
        if ($imageId) {
            Write-Warn "Found old image $fullImageName, deleting..."
            docker rmi "$fullImageName" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Old image deleted successfully"
            } else {
                Write-Warn "Warning: Cannot delete old image, may be in use"
            }
        }
    } catch {
        Write-Warn "Warning while cleaning old image"
    }

    # Clean old tar file
    if (Test-Path $outputTarFile) {
        Write-Warn "Found old tar file $outputTarFile, deleting..."
        try {
            Remove-Item $outputTarFile -Force
            Write-Success "Old tar file deleted successfully"
        } catch {
            Write-Warn "Cannot delete old tar file: $($_.Exception.Message)"
        }
    }

    # Clean dangling images (optional)
    if ($Clean) {
        Write-Info "Cleaning dangling images..."
        try {
            docker image prune -f >$null
            Write-Success "Dangling images cleanup completed"
        } catch {
            Write-Warn "Warning while cleaning dangling images"
        }
    }
}

function Build-DockerImage {
    Write-Step "Building Docker Image"

    $imageName = $Script:Config.ImageName
    $imageTag = $Script:Config.ImageTag
    $dockerfilePath = $Script:Config.DockerfilePath
    $buildContext = $Script:Config.BuildContext
    $fullImageName = "$imageName`:$imageTag"

    Write-Info "Image name: $fullImageName"
    Write-Info "Dockerfile path: $dockerfilePath"
    Write-Info "Build context: $buildContext"

    # Check if Dockerfile exists
    if (-not (Test-Path $dockerfilePath)) {
        Write-Error-Msg "Dockerfile not found: $dockerfilePath"
        exit 1
    }

    try {
        Write-Info "Starting image build..."
        $buildArgs = @(
            "build",
            "-f", $dockerfilePath,
            "-t", $fullImageName,
            $buildContext
        )

        & docker $buildArgs

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Image built successfully!"

            # Display image info
            Write-Info "Image info:"
            docker images "$fullImageName"
        } else {
            Write-Error-Msg "Image build failed!"
            exit 1
        }
    } catch {
        Write-Error-Msg "Error during build: $($_.Exception.Message)"
        exit 1
    }
}

function Export-DockerImage {
    Write-Step "Exporting Image to tar File"

    $imageName = $Script:Config.ImageName
    $imageTag = $Script:Config.ImageTag
    $outputTarFile = $Script:Config.OutputTarFile
    $fullImageName = "$imageName`:$imageTag"

    try {
        Write-Info "Exporting image: $fullImageName"
        Write-Info "Output file: $outputTarFile"

        docker save -o $outputTarFile $fullImageName

        if ($LASTEXITCODE -eq 0 -and (Test-Path $outputTarFile)) {
            $fileSize = (Get-Item $outputTarFile).Length
            $formattedSize = Format-FileSize $fileSize
            Write-Success "Image exported successfully!"
            Write-Info "File name: $outputTarFile"
            Write-Info "File size: $formattedSize"
        } else {
            Write-Error-Msg "Image export failed!"
            exit 1
        }
    } catch {
        Write-Error-Msg "Error during export: $($_.Exception.Message)"
        exit 1
    }
}

function Test-TarFile {
    Write-Step "Verifying tar File"

    $outputTarFile = $Script:Config.OutputTarFile

    if (-not (Test-Path $outputTarFile)) {
        Write-Error-Msg "tar file not found: $outputTarFile"
        exit 1
    }

    try {
        Write-Info "Verifying file integrity..."

        # Check if valid tar file
        if (Test-Command "tar") {
            $result = tar -tf $outputTarFile 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "tar file verification passed!"
            } else {
                Write-Error-Msg "Invalid tar file format!"
                exit 1
            }
        } else {
            Write-Warn "tar command not available, skipping file format verification"
        }

        # Display file info
        $fileInfo = Get-Item $outputTarFile
        $formattedSize = Format-FileSize $fileInfo.Length
        Write-Info "File path: $($fileInfo.FullName)"
        Write-Info "File size: $formattedSize"
        Write-Info "Created: $($fileInfo.CreationTime)"
        Write-Info "Modified: $($fileInfo.LastWriteTime)"

    } catch {
        Write-Error-Msg "Error during verification: $($_.Exception.Message)"
        exit 1
    }
}

function Show-BuildInfo {
    Write-Step "Build Completed"

    $imageName = $Script:Config.ImageName
    $imageTag = $Script:Config.ImageTag
    $outputTarFile = $Script:Config.OutputTarFile
    $fullImageName = "$imageName`:$imageTag"

    Write-ColorMessage "Image name: " "Green" -NoNewline
    Write-Host $fullImageName

    Write-ColorMessage "Output file: " "Green" -NoNewline
    Write-Host $outputTarFile

    if (Test-Path $outputTarFile) {
        $filePath = (Resolve-Path $outputTarFile).Path
        Write-ColorMessage "File path: " "Green" -NoNewline
        Write-Host $filePath
    }

    Write-Host ""
    Write-ColorMessage "Usage:" "Cyan"
    Write-ColorMessage "1. Load image: " "White" -NoNewline
    Write-Host "docker load -i $outputTarFile"
    Write-ColorMessage "2. Run container: " "White" -NoNewline
    Write-Host "docker run -d -p 9099:9099 --name hata-server $fullImageName"
    Write-Host ""
}

function Invoke-CleanupOnFailure {
    Write-Warn "Build failed, cleaning up..."

    $imageName = $Script:Config.ImageName
    $imageTag = $Script:Config.ImageTag
    $outputTarFile = $Script:Config.OutputTarFile
    $fullImageName = "$imageName`:$imageTag"

    # Clean image
    try {
        docker rmi "$fullImageName" 2>$null
    } catch {
        # Ignore deletion errors
    }

    # Clean tar file
    if (Test-Path $outputTarFile) {
        try {
            Remove-Item $outputTarFile -Force -ErrorAction SilentlyContinue
        } catch {
            # Ignore deletion errors
        }
    }
}

# =============================================================================
# Main Function
# =============================================================================

function Start-BuildProcess {
    [CmdletBinding()]
    param()

    Write-ColorMessage "==== hata Server Build Script (PowerShell) ====" "Green"
    Write-ColorMessage "Start time: " "Blue" -NoNewline
    Write-Host $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

    try {
        # Execute build process
        Test-DockerEnvironment
        Remove-OldArtifacts
        Build-DockerImage
        Export-DockerImage
        Test-TarFile
        Show-BuildInfo

        Write-ColorMessage "`nBuild completed! End time: " "Green" -NoNewline
        Write-Host $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

    } catch {
        Write-Error-Msg "Error during build: $($_.Exception.Message)"
        Invoke-CleanupOnFailure
        exit 1
    }
}

# =============================================================================
# Script Entry Point
# =============================================================================

# Check PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Error-Msg "PowerShell 5.1 or higher is required"
    exit 1
}

# Display help
if ($args -contains "-h" -or $args -contains "--help" -or $args -contains "help") {
    Get-Help $MyInvocation.MyCommand.Path -Full
    exit 0
}

# Start build process
Start-BuildProcess
