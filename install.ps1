# PyNet Bridge - MCP Server Installer
# Installs pynet-mcp-bridge and configures all detected AI clients:
#   Claude Desktop, Claude Code (VS Code), Cline, Roo Code

function Format-Json([string]$json) {
    $indent = 0
    $result = [System.Text.StringBuilder]::new()
    $inString = $false
    for ($i = 0; $i -lt $json.Length; $i++) {
        $char = $json[$i]
        if ($char -eq '"' -and ($i -eq 0 -or $json[$i - 1] -ne '\')) { $inString = !$inString }
        if ($inString) { [void]$result.Append($char); continue }
        switch ($char) {
            '{' { [void]$result.Append($char); [void]$result.Append("`n"); $indent++; [void]$result.Append(' ' * (2 * $indent)) }
            '}' { [void]$result.Append("`n"); $indent--; [void]$result.Append(' ' * (2 * $indent)); [void]$result.Append($char) }
            '[' { [void]$result.Append($char); [void]$result.Append("`n"); $indent++; [void]$result.Append(' ' * (2 * $indent)) }
            ']' { [void]$result.Append("`n"); $indent--; [void]$result.Append(' ' * (2 * $indent)); [void]$result.Append($char) }
            ',' { [void]$result.Append($char); [void]$result.Append("`n"); [void]$result.Append(' ' * (2 * $indent)) }
            ':' { [void]$result.Append($char); [void]$result.Append(' ') }
            default { if ($char -notin ' ', "`t", "`n", "`r") { [void]$result.Append($char) } }
        }
    }
    return $result.ToString()
}

function Add-McpServer($configPath, $createEmpty) {
    if (Test-Path $configPath) {
        try {
            $config = [System.IO.File]::ReadAllText($configPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
        } catch {
            Write-Host "  WARNING: Existing config is invalid. Creating a new one." -ForegroundColor DarkYellow
            $config = [PSCustomObject]@{ mcpServers = [PSCustomObject]@{} }
        }
    } else {
        if (-not $createEmpty) { return $false }
        $config = [PSCustomObject]@{ mcpServers = [PSCustomObject]@{} }
    }

    if (-not $config.PSObject.Properties['mcpServers']) {
        $config | Add-Member -MemberType NoteProperty -Name mcpServers -Value ([PSCustomObject]@{})
    }

    $entry = [PSCustomObject]@{ type = "stdio"; command = "pynet-bridge"; args = @() }
    if ($config.mcpServers.PSObject.Properties['pynet-bridge']) {
        $config.mcpServers.'pynet-bridge' = $entry
    } else {
        $config.mcpServers | Add-Member -MemberType NoteProperty -Name 'pynet-bridge' -Value $entry
    }

    $configDir = Split-Path $configPath
    if (-not (Test-Path $configDir)) { New-Item -ItemType Directory -Path $configDir | Out-Null }

    $compact = $config | ConvertTo-Json -Depth 10 -Compress
    $compact = $compact -replace '"args":null', '"args":[]'
    $pretty  = Format-Json $compact
    [System.IO.File]::WriteAllText($configPath, $pretty, [System.Text.UTF8Encoding]::new($false))
    return $true
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   PyNet Bridge - MCP Server Installer  " -ForegroundColor Cyan
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

# --- Step 2: Ensure uv is installed ---
Write-Host ""
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

# --- Step 3: Install package ---
$hasUv = [bool](Get-Command uv -ErrorAction SilentlyContinue)

if ($hasUv) {
    Write-Host "Installing pynet-mcp-bridge via uv..." -ForegroundColor Yellow
    uv tool install pynet-mcp-bridge --upgrade --quiet
} else {
    Write-Host "Installing pynet-mcp-bridge via pip..." -ForegroundColor DarkYellow
    pip install pynet-mcp-bridge --upgrade --quiet
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Installation failed. Check your internet connection and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "Package installed successfully." -ForegroundColor Green

# --- Step 3: Auto-detect and configure AI clients ---
Write-Host ""
Write-Host "Detecting installed AI clients..." -ForegroundColor Yellow

$configured = 0

# -- Claude Desktop --
$storePkg = Get-ChildItem "$env:LOCALAPPDATA\Packages" -Filter "Claude_*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($storePkg) {
    $desktopConfig = "$($storePkg.FullName)\LocalCache\Roaming\Claude\claude_desktop_config.json"
} elseif (Test-Path "$env:APPDATA\Claude") {
    $desktopConfig = "$env:APPDATA\Claude\claude_desktop_config.json"
} else {
    $desktopConfig = $null
}

if ($desktopConfig) {
    $ok = Add-McpServer $desktopConfig $true
    if ($ok) {
        Write-Host "  [OK] Claude Desktop: $desktopConfig" -ForegroundColor Green
        $configured++
    }
} else {
    Write-Host "  [--] Claude Desktop: not found, skipping" -ForegroundColor DarkGray
}

# -- Claude Code (VS Code extension / CLI) --
$claudeJson = "$env:USERPROFILE\.claude.json"
$ok = Add-McpServer $claudeJson $true
if ($ok) {
    Write-Host "  [OK] Claude Code:    $claudeJson" -ForegroundColor Green
    $configured++
}

# -- Cline --
$clinePath = "$env:APPDATA\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json"
if (Test-Path (Split-Path $clinePath)) {
    $ok = Add-McpServer $clinePath $true
    if ($ok) {
        Write-Host "  [OK] Cline:          $clinePath" -ForegroundColor Green
        $configured++
    }
} else {
    Write-Host "  [--] Cline:          not found, skipping" -ForegroundColor DarkGray
}

# -- Roo Code --
$rooPath = "$env:APPDATA\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\mcp_settings.json"
if (Test-Path (Split-Path $rooPath)) {
    $ok = Add-McpServer $rooPath $true
    if ($ok) {
        Write-Host "  [OK] Roo Code:       $rooPath" -ForegroundColor Green
        $configured++
    }
} else {
    Write-Host "  [--] Roo Code:       not found, skipping" -ForegroundColor DarkGray
}

# --- Done ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($configured -eq 0) {
    Write-Host "   Installation complete!" -ForegroundColor Green
    Write-Host "   No AI clients were detected."       -ForegroundColor DarkYellow
    Write-Host "   Configure manually if needed."      -ForegroundColor DarkYellow
} else {
    Write-Host "   Installation complete!" -ForegroundColor Green
    Write-Host "   Configured $configured client(s)."  -ForegroundColor Green
    Write-Host "   Restart your AI client(s) to"       -ForegroundColor Cyan
    Write-Host "   apply changes."                     -ForegroundColor Cyan
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
