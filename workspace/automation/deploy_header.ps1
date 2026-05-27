param([switch]$ClearCache)
$WP = ".\wp.bat"
$ErrorActionPreference = "Stop"

Write-Host "--- Deploy Header ---" -ForegroundColor Cyan

# Validate
if (-not (Test-Path "workspace/pages/navbar-global.json")) { throw "navbar-global.json not found" }

# Compile & update post 121485
& $WP eval @'
$engine = new \DAC\Core\Layout_Engine();
$raw = file_get_contents('C:\Users\CORE I9\Local Sites\sanpablo\workspace\pages\navbar-global.json');
$blocks = $engine->compile($raw);
wp_update_post(['ID' => 121485, 'post_content' => wp_slash($blocks)]);
echo 'Header 121485 updated. Len=' . strlen(get_post_field('post_content', 121485));
'@

# Ensure TB option points to correct ID
& $WP eval @'
$opt = get_option('et_theme_builder_layouts');
$opt['default']['header_id'] = 121485;
update_option('et_theme_builder_layouts', $opt);
echo 'header_id=121485';
'@

if ($ClearCache) {
    & $WP eval "et_core_clear_wp_cache();"
    Remove-Item -Path "app\public\wp-content\et-cache" -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "--- Header done ---" -ForegroundColor Green
