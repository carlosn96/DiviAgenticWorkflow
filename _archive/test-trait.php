<?php
define('DIVI_AGENTIC_CORE_DIR', __DIR__ . '/..');
require DIVI_AGENTIC_CORE_DIR . '/inc/core/trait-module-metadata.php';

class TestMeta { use Module_Metadata; }

echo "module_exists slider: " . (TestMeta::module_exists('divi/slider') ? 'YES' : 'NO') . "\n";
echo "module_exists number-counter: " . (TestMeta::module_exists('number-counter') ? 'YES' : 'NO') . "\n";
echo "slide has image attr: " . (TestMeta::module_has_attribute('divi/slide', 'image') ? 'YES' : 'NO') . "\n";
echo "slide has foobar attr: " . (TestMeta::module_has_attribute('divi/slide', 'foobar') ? 'YES' : 'NO') . "\n";

echo "\nslide.image innerContent items: " . implode(', ', TestMeta::get_inner_content_items('divi/slide', 'image')) . "\n";

echo "\nblurb.title decoration groups: " . implode(', ', TestMeta::get_decoration_groups('divi/blurb', 'title')) . "\n";
echo "blurb.content decoration groups: " . implode(', ', TestMeta::get_decoration_groups('divi/blurb', 'content')) . "\n";

echo "\nAll modules: " . count(TestMeta::get_all_modules()) . "\n";

$sections = TestMeta::get_modules_by_category('section');
echo "Sections: " . implode(', ', $sections) . "\n";

$modules = TestMeta::get_modules_by_category('module');
echo "Modules: " . count($modules) . "\n";
