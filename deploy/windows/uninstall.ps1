<#
.SYNOPSIS
    Safely removes a native Windows Jarvis installation.

.DESCRIPTION
    Removes only the resolved Jarvis installation root, its user PATH entry,
    and the optional OpenJarvis scheduled task. External tools such as Python,
    Git, uv and Ollama are intentionally preserved.
#>

[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'High')]
param(
    [string] $InstallRoot,
    [switch] $KeepData,
    [switch] $Force
)

$ErrorActionPreference = 'Stop'

function Write-Info($Message) {
    Write-Host "[info] $Message" -ForegroundColor Cyan
}

if (-not $InstallRoot) {
    $InstallRoot = if ($env:OPENJARVIS_HOME) {
        $env:OPENJARVIS_HOME
    } else {
        Join-Path $env:LOCALAPPDATA 'OpenJarvis'
    }
}

$resolvedRoot = [System.IO.Path]::GetFullPath($InstallRoot)
$profileRoot = [System.IO.Path]::GetFullPath($env:USERPROFILE)
$localRoot = [System.IO.Path]::GetFullPath($env:LOCALAPPDATA)

if (
    $resolvedRoot -eq $profileRoot -or
    $resolvedRoot -eq $localRoot -or
    $resolvedRoot.Length -le 3
) {
    throw "Unsafe install root refused: $resolvedRoot"
}

$serviceScript = Join-Path $resolvedRoot 'src\deploy\windows\jarvis-service.ps1'
if (Test-Path $serviceScript) {
    Write-Info "Removing the optional scheduled task..."
    & powershell -ExecutionPolicy Bypass -File $serviceScript uninstall
}

$binDir = Join-Path $resolvedRoot 'bin'
$userPath = [System.Environment]::GetEnvironmentVariable('Path', 'User')
if ($userPath) {
    $kept = @(
        $userPath -split ';' | Where-Object {
            if (-not $_) { return $false }
            $expanded = [System.Environment]::ExpandEnvironmentVariables($_)
            -not ([System.IO.Path]::GetFullPath($expanded) -ieq $binDir)
        }
    )
    [System.Environment]::SetEnvironmentVariable(
        'Path',
        ($kept -join ';'),
        'User'
    )
}

if ($KeepData) {
    $dataDir = Join-Path $resolvedRoot 'data'
    $backupDir = Join-Path $env:LOCALAPPDATA (
        'JarvisBackup-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
    )
    if (Test-Path $dataDir) {
        Copy-Item -Recurse -Force $dataDir $backupDir
        Write-Info "Data backup created at $backupDir"
    }
}

$shouldRemove = $Force -or $PSCmdlet.ShouldProcess(
    $resolvedRoot,
    'Remove the Jarvis installation directory'
)
if ($shouldRemove -and (Test-Path $resolvedRoot)) {
    Remove-Item -LiteralPath $resolvedRoot -Recurse -Force
}

Write-Host "[ok] Jarvis installation removed." -ForegroundColor Green
Write-Host "Python, Git, uv and Ollama were preserved."
