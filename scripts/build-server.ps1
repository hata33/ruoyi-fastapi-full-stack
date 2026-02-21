<#
.SYNOPSIS
    TCM Server Docker 镜像构建脚本 (PowerShell版本)

.DESCRIPTION
    构建 Docker 镜像并导出为 tar 文件
    输出: tcm-server-latest.tar
    镜像名称: tcm-server:latest

.PARAMETER Clean
    在构建前清理旧镜像和文件

.PARAMETER NoColor
    禁用彩色输出

.EXAMPLE
    .\build-server.ps1
    基本构建

.EXAMPLE
    .\build-server.ps1 -Clean
    构建前清理

.EXAMPLE
    .\build-server.ps1 -NoColor
    无彩色输出

.NOTES
    需要安装 Docker Desktop 和 PowerShell 5.1+
#>

[CmdletBinding()]
param(
    [switch]$Clean,
    [switch]$NoColor
)

# =============================================================================
# 配置和初始化
# =============================================================================

# 设置错误处理首选项
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# 配置变量
$Script:Config = @{
    ImageName = "tcm-server"
    ImageTag = "latest"
    DockerfilePath = "./fastapi-dockerfile"
    OutputTarFile = "tcm-server-latest.tar"
    BuildContext = "."
}

# 颜色配置
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
# 工具函数
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
    Write-ColorMessage "==================== $Message ====================" "Blue"
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

function Write-Error {
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

function Invoke-CommandWithOutput {
    param(
        [string]$Command,
        [string]$Arguments = "",
        [switch]$Silent,
        [switch]$NoError
    )

    $fullCommand = "$Command $Arguments".Trim()
    Write-Info "执行命令: $fullCommand"

    try {
        if ($Silent) {
            $result = & $Command $Arguments.Split(" ") 2>&1
            if ($LASTEXITCODE -ne 0 -and -not $NoError) {
                throw "命令执行失败，退出码: $LASTEXITCODE"
            }
            return $result
        } else {
            & $Command $Arguments.Split(" ")
            if ($LASTEXITCODE -ne 0 -and -not $NoError) {
                throw "命令执行失败，退出码: $LASTEXITCODE"
            }
        }
    } catch {
        if (-not $NoError) {
            throw
        }
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
# 主要功能函数
# =============================================================================

function Test-DockerEnvironment {
    Write-Step "检查 Docker 环境"

    # 检查Docker命令是否可用
    if (-not (Test-Command "docker")) {
        Write-Error "Docker 未安装或未在 PATH 中"
        Write-Info "请安装 Docker Desktop: https://www.docker.com/products/docker-desktop"
        exit 1
    }

    # 检查Docker服务是否运行
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Docker 服务未运行或权限不足"
            Write-Info "请确保 Docker Desktop 正在运行"
            exit 1
        }
    } catch {
        Write-Error "无法连接到 Docker 服务"
        Write-Info "请启动 Docker Desktop 并重试"
        exit 1
    }

    # 显示Docker版本信息
    try {
        $dockerVersion = docker --version
        Write-Success "Docker 环境检查通过"
        Write-Info "Docker 版本: $dockerVersion"
    } catch {
        Write-Warn "无法获取Docker版本信息"
    }
}

function Remove-OldArtifacts {
    Write-Step "清理旧文件"

    $imageName = $Script:Config.ImageName
    $imageTag = $Script:Config.ImageTag
    $fullImageName = "$imageName`:$imageTag"
    $outputTarFile = $Script:Config.OutputTarFile

    # 清理旧镜像
    try {
        $imageId = docker images -q "$fullImageName" 2>$null
        if ($imageId) {
            Write-Warn "发现旧镜像 $fullImageName，正在删除..."
            docker rmi "$fullImageName" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "旧镜像删除成功"
            } else {
                Write-Warn "警告: 无法删除旧镜像，可能正在被使用"
            }
        }
    } catch {
        Write-Warn "清理旧镜像时出现警告"
    }

    # 清理旧tar文件
    if (Test-Path $outputTarFile) {
        Write-Warn "发现旧tar文件 $outputTarFile，正在删除..."
        try {
            Remove-Item $outputTarFile -Force
            Write-Success "旧tar文件删除成功"
        } catch {
            Write-Warn "无法删除旧tar文件: $($_.Exception.Message)"
        }
    }

    # 清理悬空镜像（可选）
    if ($Clean) {
        Write-Info "清理悬空镜像..."
        try {
            docker image prune -f >$null
            Write-Success "悬空镜像清理完成"
        } catch {
            Write-Warn "清理悬空镜像时出现警告"
        }
    }
}

function Build-DockerImage {
    Write-Step "构建 Docker 镜像"

    $imageName = $Script:Config.ImageName
    $imageTag = $Script:Config.ImageTag
    $dockerfilePath = $Script:Config.DockerfilePath
    $buildContext = $Script:Config.BuildContext
    $fullImageName = "$imageName`:$imageTag"

    Write-Info "镜像名称: $fullImageName"
    Write-Info "Dockerfile 路径: $dockerfilePath"
    Write-Info "构建上下文: $buildContext"

    # 检查Dockerfile是否存在
    if (-not (Test-Path $dockerfilePath)) {
        Write-Error "Dockerfile 不存在: $dockerfilePath"
        exit 1
    }

    try {
        Write-Info "开始构建镜像..."
        $buildArgs = @(
            "build",
            "-f", $dockerfilePath,
            "-t", $fullImageName,
            $buildContext
        )

        & docker $buildArgs

        if ($LASTEXITCODE -eq 0) {
            Write-Success "镜像构建成功!"

            # 显示镜像信息
            Write-Info "镜像信息:"
            docker images "$fullImageName"
        } else {
            Write-Error "镜像构建失败!"
            exit 1
        }
    } catch {
        Write-Error "构建过程中发生错误: $($_.Exception.Message)"
        exit 1
    }
}

function Export-DockerImage {
    Write-Step "导出镜像为 tar 文件"

    $imageName = $Script:Config.ImageName
    $imageTag = $Script:Config.ImageTag
    $outputTarFile = $Script:Config.OutputTarFile
    $fullImageName = "$imageName`:$imageTag"

    try {
        Write-Info "导出镜像: $fullImageName"
        Write-Info "输出文件: $outputTarFile"

        docker save -o $outputTarFile $fullImageName

        if ($LASTEXITCODE -eq 0 -and (Test-Path $outputTarFile)) {
            $fileSize = (Get-Item $outputTarFile).Length
            $formattedSize = Format-FileSize $fileSize
            Write-Success "镜像导出成功!"
            Write-Info "文件名: $outputTarFile"
            Write-Info "文件大小: $formattedSize"
        } else {
            Write-Error "镜像导出失败!"
            exit 1
        }
    } catch {
        Write-Error "导出过程中发生错误: $($_.Exception.Message)"
        exit 1
    }
}

function Test-TarFile {
    Write-Step "验证 tar 文件"

    $outputTarFile = $Script:Config.OutputTarFile

    if (-not (Test-Path $outputTarFile)) {
        Write-Error "tar 文件不存在: $outputTarFile"
        exit 1
    }

    try {
        Write-Info "验证文件完整性..."

        # 检查是否为有效的tar文件
        if (Test-Command "tar") {
            $result = tar -tf $outputTarFile 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "tar 文件验证通过!"
            } else {
                Write-Error "tar 文件格式无效!"
                exit 1
            }
        } else {
            Write-Warn "tar 命令不可用，跳过文件格式验证"
        }

        # 显示文件信息
        $fileInfo = Get-Item $outputTarFile
        $formattedSize = Format-FileSize $fileInfo.Length
        Write-Info "文件路径: $($fileInfo.FullName)"
        Write-Info "文件大小: $formattedSize"
        Write-Info "创建时间: $($fileInfo.CreationTime)"
        Write-Info "修改时间: $($fileInfo.LastWriteTime)"

    } catch {
        Write-Error "验证过程中发生错误: $($_.Exception.Message)"
        exit 1
    }
}

function Show-BuildInfo {
    Write-Step "构建完成"

    $imageName = $Script:Config.ImageName
    $imageTag = $Script:Config.ImageTag
    $outputTarFile = $Script:Config.OutputTarFile
    $fullImageName = "$imageName`:$imageTag"

    Write-ColorMessage "镜像名称: " "Green" -NoNewline
    Write-Host $fullImageName

    Write-ColorMessage "输出文件: " "Green" -NoNewline
    Write-Host $outputTarFile

    if (Test-Path $outputTarFile) {
        $filePath = (Resolve-Path $outputTarFile).Path
        Write-ColorMessage "文件路径: " "Green" -NoNewline
        Write-Host $filePath
    }

    Write-Host ""
    Write-ColorMessage "使用方法:" "Cyan"
    Write-ColorMessage "1. 加载镜像: " "White" -NoNewline
    Write-Host "docker load -i $outputTarFile"
    Write-ColorMessage "2. 运行容器: " "White" -NoNewline
    Write-Host "docker run -d -p 9099:9099 --name tcm-server $fullImageName"
    Write-Host ""
}

function Invoke-CleanupOnFailure {
    Write-Warn "构建失败，正在清理..."

    $imageName = $Script:Config.ImageName
    $imageTag = $Script:Config.ImageTag
    $outputTarFile = $Script:Config.OutputTarFile
    $fullImageName = "$imageName`:$imageTag"

    # 清理镜像
    try {
        docker rmi "$fullImageName" 2>$null
    } catch {
        # 忽略删除错误
    }

    # 清理tar文件
    if (Test-Path $outputTarFile) {
        try {
            Remove-Item $outputTarFile -Force -ErrorAction SilentlyContinue
        } catch {
            # 忽略删除错误
        }
    }
}

# =============================================================================
# 主函数
# =============================================================================

function Start-BuildProcess {
    [CmdletBinding()]
    param()

    Write-ColorMessage "==================== TCM Server 构建脚本 (PowerShell) ====================" "Green"
    Write-ColorMessage "开始时间: " "Blue" -NoNewline
    Write-Host $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

    try {
        # 执行构建流程
        Test-DockerEnvironment
        Remove-OldArtifacts
        Build-DockerImage
        Export-DockerImage
        Test-TarFile
        Show-BuildInfo

        Write-ColorMessage "`n构建完成! 结束时间: " "Green" -NoNewline
        Write-Host $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

    } catch {
        Write-Error "构建过程中发生错误: $($_.Exception.Message)"
        Invoke-CleanupOnFailure
        exit 1
    }
}

# =============================================================================
# 脚本入口
# =============================================================================

# 检查PowerShell版本
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Error "需要 PowerShell 5.1 或更高版本"
    exit 1
}

# 检查是否以管理员权限运行（可选）
# $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
# if ($isAdmin) {
#     Write-Warn "检测到管理员权限，构建过程中请谨慎操作"
# }

# 显示帮助信息
if ($args -contains "-h" -or $args -contains "--help" -or $args -contains "help") {
    Get-Help $MyInvocation.MyCommand.Path -Full
    exit 0
}

# 启动构建流程
Start-BuildProcess