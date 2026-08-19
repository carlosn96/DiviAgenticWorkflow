param(
    [Parameter(Mandatory=$true)] [string]$Slug,
    [Parameter(Mandatory=$false)] [string]$Title = "",
    [Parameter(Mandatory=$false)] [string]$Site = "",
    [Parameter(Mandatory=$false)] [switch]$SkipCache,
    [Parameter(Mandatory=$false)] [switch]$SkipVerify
)

# publish.ps1 — un solo comando: combine + deploy + flush + verify.
# Uso:  powershell -File workspace/publish.ps1 -Slug inicio -Title "Inicio"
#       (o desde la raíz del proyecto:  .\DiviAgenticWorkflow\workspace\publish.ps1 -Slug inicio)

$ErrorActionPreference = "Stop"

# Resolver DawRoot/WpRoot desde cualquier cwd
$DawRoot     = Resolve-Path (Split-Path $PSScriptRoot -Parent)
$WpRoot      = Resolve-Path (Split-Path $DawRoot -Parent)

# Resolver Site desde .env o parámetro
if (-not $Site) {
    $envFile = Join-Path $DawRoot ".env"
    if (Test-Path $envFile) {
        $line = (Get-Content $envFile | Where-Object { $_ -match "^DAW_SITE=" } | Select-Object -First 1)
        if ($line) { $Site = ($line -split "=",2)[1].Trim() }
    }
}
if (-not $Site) { throw "No se pudo resolver DAW_SITE. Pasalo con -Site o define el .env." }

if (-not $Title) { $Title = $Slug }

Write-Host "=== Publish: $Title ($Slug) | site: $Site ===" -ForegroundColor Cyan

# 1. Deploy (combine + deploy_page + flush) — usa el wrapper oficial (regla #5)
$deployArgs = @{ Slug = $Slug; Title = $Title; Site = $Site }
if ($SkipCache) { $deployArgs.SkipCache = $true }
Push-Location $DawRoot
try {
    & (Join-Path $DawRoot "workspace\deploy.ps1") @deployArgs
    if ($LASTEXITCODE -ne 0) { throw "deploy.ps1 failed" }
} finally {
    Pop-Location
}

# 2. Verificación post-deploy
if (-not $SkipVerify) {
    Write-Host "[VERIFY] Comprobando..." -ForegroundColor Yellow
    Push-Location $DawRoot
    try {
        $verify = & php (Join-Path $DawRoot "divi-agentic-core\bin\verify_page.php") --slug=$Slug 2>&1
        $verify | Out-String | Write-Host
        $frontend = & php (Join-Path $DawRoot "divi-agentic-core\bin\check_frontend.php") $Slug 2>&1
        $frontend | Out-String | Write-Host
    } finally {
        Pop-Location
    }
}

Write-Host "=== Publish complete: $Title ===" -ForegroundColor Green
