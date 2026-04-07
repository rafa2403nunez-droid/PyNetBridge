# PyNet Bridge - Installer for Claude Desktop & Claude Code (VS Code)
# Installs pynet-mcp-bridge and configures both clients automatically

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

# --- Step 1: Check Python ---
Write-Host "Checking Python installation..." -ForegroundColor Yellow
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python not found. Install Python 3.10+ from https://python.org and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
$pythonVersion = python --version
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# --- Step 2: Install package ---
Write-Host ""
Write-Host "Installing pynet-mcp-bridge from PyPI..." -ForegroundColor Yellow
pip install pynet-mcp-bridge --upgrade --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Installation failed. Check your internet connection and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "Package installed successfully." -ForegroundColor Green

# --- Step 3: Configure Claude Desktop ---
Write-Host ""
Write-Host "Configuring Claude Desktop..." -ForegroundColor Yellow

$storePkg = Get-ChildItem "$env:LOCALAPPDATA\Packages" -Filter "Claude_*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($storePkg) {
    $desktopConfig = "$($storePkg.FullName)\LocalCache\Roaming\Claude\claude_desktop_config.json"
} elseif (Test-Path "$env:APPDATA\Claude") {
    $desktopConfig = "$env:APPDATA\Claude\claude_desktop_config.json"
} else {
    Write-Host "  Could not find Claude Desktop automatically." -ForegroundColor DarkYellow
    $desktopConfig = Read-Host "  Enter the full path to claude_desktop_config.json (or leave blank to skip)"
}

if ($desktopConfig) {
    $ok = Add-McpServer $desktopConfig $true
    if ($ok) { Write-Host "  Configured: $desktopConfig" -ForegroundColor Green }
}

# --- Step 4: Configure Claude Code (VS Code extension) ---
Write-Host ""
Write-Host "Configuring Claude Code (VS Code extension)..." -ForegroundColor Yellow

$claudeJson = "$env:USERPROFILE\.claude.json"
$ok = Add-McpServer $claudeJson $true
if ($ok) { Write-Host "  Configured: $claudeJson" -ForegroundColor Green }

# --- Done ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Installation complete!" -ForegroundColor Green
Write-Host "   Restart Claude Desktop and VS Code"  -ForegroundColor Cyan
Write-Host "   to apply changes."                   -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
