# DEPRECATED — use the official wrapper instead:
#   .\workspace\deploy.ps1 -Slug <slug> -Title "<title>"
# This script is kept as a compatibility shim and delegates to workspace/deploy.ps1.
# It does combine + deploy_page + cache flush, exactly like the official wrapper.

param(
    [Parameter(Mandatory=$true)] [string]$Title,
    [Parameter(Mandatory=$true)] [string]$Slug,
    [Parameter(Mandatory=$true)] [string]$SchemaPath,
    [switch]$ClearCache
)

$ErrorActionPreference = "Stop"

$DawRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ProjectRoot = (Resolve-Path (Join-Path $DawRoot "..")).Path
$WpCli = Join-Path $ProjectRoot "wp.bat"

Write-Host "NOTE: daw-skill/scripts/deploy_page.ps1 is deprecated." -ForegroundColor Yellow
Write-Host "      Prefer: .\workspace\deploy.ps1 -Slug <slug> -Title <title>" -ForegroundColor Yellow

# 1. Combine manifest + sections (SchemaPath is the combined output target)
if ($SchemaPath -like "*-combined.json") {
    $Manifest = $SchemaPath -replace "-combined\.json$", "\manifest.json"
    if (Test-Path $Manifest) {
        Write-Host "Combining: $Manifest" -ForegroundColor DarkGray
        python "$DawRoot\workspace\combine.py" $Manifest --out $SchemaPath
        if ($LASTEXITCODE -ne 0) { throw "combine.py failed." }
    }
}

# 2. Deploy via wp agentic deploy_page
$deployCmd = "$WpCli agentic deploy_page --title=`"$Title`" --slug=`"$Slug`" --schema=`"$SchemaPath`""
Write-Host ">> $deployCmd" -ForegroundColor Yellow
Invoke-Expression $deployCmd
if ($LASTEXITCODE -ne 0) { throw "Error: WP-CLI deployment failed." }

# 3. Cache clearing
if ($ClearCache) {
    Write-Host "Clearing Divi cache..." -ForegroundColor Yellow
    Invoke-Expression "$WpCli cache flush"
    $EtCache = Join-Path $ProjectRoot "wp-content\et-cache"
    if (Test-Path $EtCache) {
        Remove-Item -Path "$EtCache\*" -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Success: Page '$Title' deployed." -ForegroundColor Green