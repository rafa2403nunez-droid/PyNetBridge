# PyNet Bridge - Python Libraries Starter Pack
# Installs the recommended Python libraries for Navisworks scripting with PyNET:
#   pythonnet, pandas, plotly, matplotlib, dash

$libraries = @(
    @{ Name = "pandas";     Desc = "Data analysis and manipulation" },
    @{ Name = "plotly";     Desc = "Interactive charts and visualizations" },
    @{ Name = "matplotlib"; Desc = "Static plots and graphs" },
    @{ Name = "dash";       Desc = "Web dashboards from Python" }
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   PyNet Bridge - Starter Pack          " -ForegroundColor Cyan
Write-Host "   Python Libraries Installer           " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Step 1: Check Python >= 3.10 ---
Write-Host "Checking Python installation..." -ForegroundColor Yellow
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python not found. Install Python 3.10+ from https://python.org and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$pythonVersion = python --version
Write-Host "Found: $pythonVersion" -ForegroundColor Green

$versionMatch = [regex]::Match($pythonVersion, '(\d+)\.(\d+)')
if ($versionMatch.Success) {
    $major = [int]$versionMatch.Groups[1].Value
    $minor = [int]$versionMatch.Groups[2].Value
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
        Write-Host "ERROR: Python 3.10+ is required but found $major.$minor. Please upgrade." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "WARNING: Could not determine Python version. Proceeding anyway..." -ForegroundColor DarkYellow
}

# --- Step 2: Show what will be installed ---
Write-Host ""
Write-Host "The following libraries will be installed:" -ForegroundColor Yellow
Write-Host ""
foreach ($lib in $libraries) {
    Write-Host "  - $($lib.Name)" -ForegroundColor White -NoNewline
    Write-Host "  $($lib.Desc)" -ForegroundColor DarkGray
}
Write-Host ""

# --- Step 3: Ensure uv is installed ---
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found. Installing uv..." -ForegroundColor Yellow
    try {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        # Refresh PATH so uv is available in this session
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    } catch {
        Write-Host "WARNING: Could not install uv automatically. Falling back to pip." -ForegroundColor DarkYellow
    }
}

# --- Step 4: Install libraries ---
$hasUv = [bool](Get-Command uv -ErrorAction SilentlyContinue)
$installed = 0
$failed = 0

foreach ($lib in $libraries) {
    Write-Host "Installing $($lib.Name)..." -ForegroundColor Yellow -NoNewline

    if ($hasUv) {
        uv pip install $lib.Name --system --quiet 2>&1 | Out-Null
    } else {
        pip install $lib.Name --quiet 2>&1 | Out-Null
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
        $installed++
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        $failed++
    }
}

# --- Done ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($failed -eq 0) {
    Write-Host "   All $installed libraries installed!" -ForegroundColor Green
} else {
    Write-Host "   Installed: $installed  |  Failed: $failed" -ForegroundColor DarkYellow
    Write-Host "   Check errors above and retry." -ForegroundColor DarkYellow
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"
