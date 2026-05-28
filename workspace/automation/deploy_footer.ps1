param([switch]$ClearCache)
$ErrorActionPreference = "Stop"
$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$SITE = if ($env:DAW_SITE) { $env:DAW_SITE } else { "bibliotheca" }
$WP = Join-Path $ROOT "DAW_bundle\wp.bat"
$EnvFile = Join-Path $ROOT ".env"
$FooterId = $null
Set-Location -LiteralPath $ROOT

if (Test-Path $EnvFile) {
    Get-Content $EnvFile | Where-Object { $_ -match '^\s*([^#]+?)\s*=\s*(.*)$' } | ForEach-Object {
        $varName = $Matches[1].Trim()
        $varValue = ($Matches[2].Trim() -replace '^"|"$', '') -replace "^'|'$", ""
        if ($varName -eq "DAW_FOOTER_ID" -and $varValue) {
            $FooterId = [int]$varValue
        }
    }
}

Write-Host "--- Deploy Footer ---" -ForegroundColor Cyan

if (-not (Test-Path (Join-Path $ROOT "DAW_bundle/site/$SITE/pages/footer-global.json"))) { throw "footer-global.json not found in site/$SITE/pages/" }
if (-not $FooterId) { throw "DAW_FOOTER_ID not set in .env" }

$schemaFile = Join-Path $ROOT "DAW_bundle/site/$SITE/pages/footer-global.json"
$phpEval = @'
$engine = new \DAC\Core\Layout_Engine();
$raw = file_get_contents('__SCHEMA__');
$blocks = $engine->compile($raw);
wp_update_post(['ID' => __FOOTER_ID__, 'post_content' => wp_slash($blocks)]);
echo 'Footer __FOOTER_ID__ updated. Len=' . strlen(get_post_field('post_content', __FOOTER_ID__));
'@
$phpEval = $phpEval.Replace('__SCHEMA__', $schemaFile).Replace('__FOOTER_ID__', $FooterId)
& $WP eval $phpEval

& $WP eval "`$opt = get_option('et_theme_builder_layouts');`$opt['default']['footer_id'] = $FooterId; update_option('et_theme_builder_layouts', `$opt); echo 'footer_id=$FooterId';"

if ($ClearCache) {
    & $WP eval "et_core_clear_wp_cache();"
    Remove-Item -Path (Join-Path $ROOT 'app/public/wp-content/et-cache') -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "--- Footer done ---" -ForegroundColor Green
