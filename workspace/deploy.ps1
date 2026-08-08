param(
    [Parameter(Mandatory=$true)] [string]$Slug,
    [Parameter(Mandatory=$true)] [string]$Title,
    [string]$Site = "",
    [switch]$SkipCache
)

$ErrorActionPreference = "Stop"

$DawRoot = Resolve-Path "$PSScriptRoot\.."
$WpRoot  = Resolve-Path "$PSScriptRoot\..\.."
$WpCli   = if (Test-Path "$WpRoot\wp.bat") { "$WpRoot\wp.bat" } elseif (Test-Path "$WpRoot/wp") { "$WpRoot/wp" } else { throw "wp wrapper no encontrado en $WpRoot. Crear wp.bat (Win) o wp (Unix) segun AGENTS.md §0.1." }

if (-not $Site) { $Site = $env:DAW_SITE }
if (-not $Site) { throw "DAW_SITE not set. Pass -Site or set DAW_SITE env." }

$PageDefDir = "$DawRoot\site\$Site\page-defs\$Slug"
$Manifest = "$PageDefDir\manifest.json"
$Combined = "$PageDefDir\$Slug-combined.json"
$DesignSystem = "$DawRoot\site\$Site\design-system\divitheme.json"
$EtCache = "$WpRoot\wp-content\et-cache"

if (-not (Test-Path $Manifest)) { throw "Manifest not found: $Manifest" }

Write-Host "=== Deploy page: $Title ($Slug) ===" -ForegroundColor Cyan

Write-Host "[1/3] Combining manifest..." -ForegroundColor Yellow
python "$PSScriptRoot\combine.py" $Manifest --out $Combined
if ($LASTEXITCODE -ne 0) { throw "combine.py failed" }
Write-Host "  -> $Combined" -ForegroundColor Green

Write-Host "[2/3] Deploying page..." -ForegroundColor Yellow
$schemaPath = "site/$Site/page-defs/$Slug/$Slug-combined.json"
$dsPath = "site/$Site/design-system/divitheme.json"
if (Test-Path $DesignSystem) {
    & $WpCli agentic deploy_page --title=$Title --slug=$Slug --schema=$schemaPath --design-system=$dsPath
} else {
    & $WpCli agentic deploy_page --title=$Title --slug=$Slug --schema=$schemaPath
}
if ($LASTEXITCODE -ne 0) { throw "deploy_page failed" }

if (-not $SkipCache) {
    Write-Host "[3/3] Clearing cache..." -ForegroundColor Yellow
    & $WpCli cache flush
    if (Test-Path $EtCache) {
        Remove-Item -Path "$EtCache\*" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  -> Static CSS cache flushed" -ForegroundColor Green
    }
}

Write-Host "=== Deploy complete: $Title ===" -ForegroundColor Cyan
