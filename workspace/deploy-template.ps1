param(
    [Parameter(Mandatory=$true)] [string]$Title,
    [string]$UseOn = "",
    [switch]$Default,
    [string]$Site = "",
    [string]$Mode = "create",
    [int]$TemplateId = 0,
    [string]$HeaderPath = "",
    [string]$FooterPath = "",
    [string]$BodyPath = "",
    [int]$HeaderId = 0,
    [int]$FooterId = 0,
    [int]$BodyId = 0,
    [int]$HeaderEnabled = 1,
    [int]$FooterEnabled = 1,
    [int]$BodyEnabled = 1,
    [int]$HeaderGlobal = 1,
    [int]$FooterGlobal = 1,
    [int]$BodyGlobal = 1,
    [switch]$SkipCombine,
    [switch]$SkipCache
)

$ErrorActionPreference = "Stop"

$DawRoot = Resolve-Path "$PSScriptRoot\.."
$WpRoot  = Resolve-Path "$PSScriptRoot\..\.."
$WpCli   = if (Test-Path "$WpRoot\wp.bat") { "$WpRoot\wp.bat" } elseif (Test-Path "$WpRoot/wp") { "$WpRoot/wp" } else { throw "wp wrapper no encontrado en $WpRoot. Crear wp.bat (Win) o wp (Unix) segun AGENTS.md §0.1." }

if (-not $Site) { $Site = $env:DAW_SITE }
if (-not $Site) { throw "DAW_SITE not set. Pass -Site or set DAW_SITE env." }

$SchemaBase = "site/$Site/page-defs"
$EtCache = "$WpRoot\wp-content\et-cache"
$DsPath = "$DawRoot\site\$Site\design-system\divitheme.json"
$DsArg = if (Test-Path $DsPath) { "--design-system=$DsPath" } else { "" }

# Component resolution:
# - If any -Path param is given, deploy ONLY those components
# - If no -Path param is given, use defaults for all three
$HasCustomPath = $HeaderPath -or $FooterPath -or $BodyPath
$Components = @()

function Add-Component($key, $path) {
    $manifest = "$DawRoot\$SchemaBase\$key\manifest.json"
    $script:Components += @{ key=$key; path=$path; manifest=$manifest }
}

if ($HasCustomPath) {
    if ($HeaderPath) { Add-Component "header" $HeaderPath }
    if ($FooterPath) { Add-Component "footer" $FooterPath }
    if ($BodyPath)   { Add-Component "body" $BodyPath }
} else {
    # Default global paths (all three)
    Add-Component "header" "$SchemaBase/header/header-combined.json"
    Add-Component "footer" "$SchemaBase/footer/footer-combined.json"
    Add-Component "body" "$SchemaBase/body/body-combined.json"
}

if ($Components.Count -eq 0) { throw "No components to deploy." }
Write-Host "=== Deploy template: $Title ($UseOn, mode=$Mode) ===" -ForegroundColor Cyan
Write-Host "  Components: $($Components.key -join ', ')" -ForegroundColor Gray

# Step 1: Combine manifests
if (-not $SkipCombine) {
    Write-Host "[1/4] Combining manifests..." -ForegroundColor Yellow
    foreach ($comp in $Components) {
        if (Test-Path $comp.manifest) {
            $out = "$DawRoot\$SchemaBase\$($comp.key)\$($comp.key)-combined.json"
            Write-Host "  -> $($comp.key)..."
            python "$PSScriptRoot\combine.py" $comp.manifest --out $out
            if ($LASTEXITCODE -ne 0) { throw "combine.py failed for $($comp.key)" }
        }
    }
    Write-Host "  Done." -ForegroundColor Green
}

# Step 2: Resolve template (global or custom)
Write-Host "[2/4] Resolving template..." -ForegroundColor Yellow
if ($Default) {
    # Global template: applies to all pages (default template, no use-on)
    if ($TemplateId -gt 0) {
        $tid = $TemplateId
    } else {
        $tid = & $WpCli agentic template_default --title="$Title" 2>&1 | Select-Object -Last 1
        if ($LASTEXITCODE -ne 0) { throw "template_default: $tid" }
    }
    Write-Host "  Global template ID: $tid" -ForegroundColor Green
} else {
    # Custom template: specific use-on conditions
    if (-not $UseOn) { throw "Use -UseOn or -Global is required." }
    if ($TemplateId -gt 0) {
        $tid = $TemplateId
    } elseif ($Mode -eq "create") {
        $tid = & $WpCli agentic template_create --use-on="$UseOn" --title="$Title" 2>&1 | Select-Object -Last 1
        if ($LASTEXITCODE -ne 0) { throw "template_create: $tid" }
    } elseif ($Mode -eq "update") {
        $tid = & $WpCli agentic template_find --use-on="$UseOn" 2>&1 | Select-Object -Last 1
        if ($LASTEXITCODE -ne 0 -or $tid -eq "0 (not found)") { throw "Template for '$UseOn' not found" }
    } else {
        $tid = & $WpCli agentic template_ensure --use-on="$UseOn" --title="$Title" 2>&1 | Select-Object -Last 1
        if ($LASTEXITCODE -ne 0) { throw "template_ensure: $tid" }
    }
    Write-Host "  Custom template ID: $tid" -ForegroundColor Green
}
$tid = $tid.Trim()

# Step 3: Resolve existing layout IDs from template, then deploy
Write-Host "[3/4] Deploying components..." -ForegroundColor Yellow
$wireArgs = @($tid)
foreach ($comp in $Components) {
    $schemaArg = "--schema=$($comp.path)"
    $idVar = "$($comp.key)Id"
    $lid = Get-Variable -Name $idVar -ValueOnly -ErrorAction SilentlyContinue

    # Resolve layout ID según modo
    if ($Mode -eq "create") {
        # Create: error si el template ya tiene un layout para este componente
        if (-not $lid -or $lid -le 0) {
            $existingId = & $wpCli post meta get $tid "_et_$($comp.key)_layout_id" 2>&1
            if ($LASTEXITCODE -eq 0 -and $existingId -match '^\d+$' -and $existingId -gt 0) {
                throw "$($comp.key) layout ID $existingId already exists on template $tid. Use --mode=update or --mode=upsert."
            }
        }
    } elseif ($Mode -eq "update") {
        # Update: requiere ID explícito
        if (-not $lid -or $lid -le 0) {
            throw "--mode=update requires --$idVar for $($comp.key)."
        }
    } else {
        # upsert: reusa existente o crea
        if (-not $lid -or $lid -le 0) {
            $existingId = & $wpCli post meta get $tid "_et_$($comp.key)_layout_id" 2>&1
            if ($LASTEXITCODE -eq 0 -and $existingId -match '^\d+$' -and $existingId -gt 0) {
                $lid = [int]$existingId
                Write-Host "  $($comp.key): reusing existing layout ID $lid" -ForegroundColor Gray
            }
        }
    }

    if ($lid -and $lid -gt 0) {
        $out = & $wpCli agentic layout_ensure $($comp.key) $schemaArg --by-id=$lid $DsArg 2>&1
        if ($LASTEXITCODE -ne 0) { throw "layout_ensure $($comp.key): $out" }
        Write-Host "  $($comp.key): ID $lid (updated)" -ForegroundColor Green
    } else {
        $out = & $wpCli agentic layout_deploy $($comp.key) $schemaArg $DsArg 2>&1
        if ($LASTEXITCODE -ne 0) { throw "layout_deploy $($comp.key): $out" }
        $lid = ($out | Select-Object -Last 1).Trim()
        Write-Host "  $($comp.key): ID $lid (created)" -ForegroundColor Green
    }
    $wireArgs += "--$($comp.key)-id=$lid"

    $enabledVar = "$($comp.key)Enabled"
    $enabled = Get-Variable -Name $enabledVar -ValueOnly
    if ($enabled -ne 1) { $wireArgs += "--$($comp.key)-enabled=$enabled" }

    $globalVar = "$($comp.key)Global"
    $global = Get-Variable -Name $globalVar -ValueOnly
    if ($global -ne 1) { $wireArgs += "--$($comp.key)-global=$global" }
}

# Preserve existing layouts not being deployed
$allKeys = @("header", "footer", "body")
foreach ($k in $allKeys) {
    $already = $wireArgs | Where-Object { $_ -like "--$k-id=*" }
    if (-not $already) {
        $existingId = & $wpCli post meta get $tid "_et_${k}_layout_id" 2>&1 | Select-Object -Last 1
        if ($LASTEXITCODE -eq 0 -and $existingId -match '^\d+$' -and $existingId -gt 0) {
            $wireArgs += "--$k-id=$existingId"
            $enabled = & $wpCli post meta get $tid "_et_${k}_enabled" 2>&1 | Select-Object -Last 1
            if ($LASTEXITCODE -eq 0 -and $enabled -eq "0") { $wireArgs += "--$k-enabled=0" }
        }
    }
}

# Step 4: Wire to template
Write-Host "[4/4] Wiring template $tid..." -ForegroundColor Yellow
& $wpCli agentic template_wire $wireArgs
if ($LASTEXITCODE -ne 0) { throw "template_wire failed" }

if (-not $SkipCache) {
    & $wpCli cache flush
    if (Test-Path $EtCache) {
        Remove-Item -Path "$EtCache\*" -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "=== Deploy complete: $Title ===" -ForegroundColor Cyan
