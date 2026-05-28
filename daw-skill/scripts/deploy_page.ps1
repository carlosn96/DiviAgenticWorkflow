param (
    [Parameter(Mandatory=$true)]
    [string]$Title,

    [Parameter(Mandatory=$true)]
    [string]$Slug,

    [Parameter(Mandatory=$true)]
    [string]$SchemaPath,

    [switch]$ClearCache
)

$ErrorActionPreference = "Stop"

# Default configuration
$WPCLI = "DAW_bundle\wp.bat"
$ProjectRoot = $PWD.Path

# Resolve project root (DAW_bundle is one level below project root)
$DAWRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ProjectRoot = (Resolve-Path (Join-Path $DAWRoot "..")).Path
$EnvFile = Join-Path $ProjectRoot ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | Where-Object { $_ -match '^\s*([^#]+?)\s*=\s*(.*)$' } | ForEach-Object {
        $varName = $Matches[1].Trim()
        $varValue = ($Matches[2].Trim() -replace '^"|"$', '') -replace "^'|'$", ""
        if ($varName -eq "WP_CLI_COMMAND") { $WPCLI = $varValue }
        if ($varName -eq "PROJECT_ROOT" -and $varValue -ne ".") { $ProjectRoot = Resolve-Path $varValue }
    }
} else {
    Write-Host "NOTE: No .env found at $EnvFile. Using defaults ($WPCLI and PWD)." -ForegroundColor Yellow
}

Write-Host "--- DAW Execution: Deploying Page '$Title' ---" -ForegroundColor Cyan
Write-Host "Environment: WP_CLI = $WPCLI | Root = $ProjectRoot"

# 1. Validate Schema file exists
if (-not (Test-Path $SchemaPath)) {
    # Attempt to resolve considering it relative
    $TryRelative = Join-Path $ProjectRoot $SchemaPath
    if (Test-Path $TryRelative) {
        $SchemaPath = $TryRelative
    } else {
        throw "Error: Schema file not found at '$SchemaPath'."
    }
}

# 2. Execute via configured WP-CLI
Write-Host "Running command..." -ForegroundColor DarkGray
$deployCmd = "$WPCLI agentic deploy_page --title=`"$Title`" --slug=`"$Slug`" --schema=`"$SchemaPath`""
Write-Host ">> $deployCmd" -ForegroundColor Yellow

Invoke-Expression $deployCmd
if ($LASTEXITCODE -ne 0) {
    throw "Error: WP-CLI deployment failed."
}

# 3. Optional Cache Clearing
if ($ClearCache) {
    Write-Host "Clearing Divi 5 cache..." -ForegroundColor Yellow
    Invoke-Expression "$WPCLI eval `"et_core_clear_wp_cache();`""
    Write-Host "Cache cleared." -ForegroundColor Green
}

# 4. Final Verification
Write-Host "Verifying deployment..." -ForegroundColor Yellow
$postCount = Invoke-Expression "$WPCLI post list --name=`"$Slug`" --format=count" 2>$null
if ([int]$postCount -eq 0) {
    throw "Error: Verification failed. Post not found in DB."
}

Write-Host "Success: Page '$Title' deployed." -ForegroundColor Green
