param([switch]$ClearCache)
$ErrorActionPreference = "Stop"
$ROOT = "C:\Users\CORE I9\Local Sites\sanpablo"
$WP = "$ROOT\wp.bat"
Set-Location -LiteralPath $ROOT

Write-Host "--- Deploy Footer ---" -ForegroundColor Cyan

# Validate
if (-not (Test-Path "$ROOT/workspace/pages/footer-global.json")) { throw "footer-global.json not found" }

# Sync
Copy-Item -Path "$ROOT/workspace/pages/footer-global.json" -Destination "$ROOT/app/public/wp-content/themes/divi-agentic-core/layouts/footer.json" -Force

# Compile & update post 110489
& $WP eval @'
$engine = new \DAC\Core\Layout_Engine();
$raw = file_get_contents('C:\Users\CORE I9\Local Sites\sanpablo\workspace\pages\footer-global.json');
$blocks = $engine->compile($raw);
wp_update_post(['ID' => 110489, 'post_content' => wp_slash($blocks)]);
echo 'Footer 110489 updated. Len=' . strlen(get_post_field('post_content', 110489));
'@

# Ensure TB option points to correct ID
& $WP eval @'
$opt = get_option('et_theme_builder_layouts');
$opt['default']['footer_id'] = 110489;
update_option('et_theme_builder_layouts', $opt);
echo 'footer_id=110489';
'@

if ($ClearCache) {
    & $WP eval "et_core_clear_wp_cache();"
    Remove-Item -Path "app\public\wp-content\et-cache" -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "--- Footer done ---" -ForegroundColor Green
