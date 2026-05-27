<?php
// Pull a single page from remote DB → txt backup
// Usage: php workspace/automation/pull_remote_page.php --slug=inicio

$options = getopt("", ["slug:"]);
$slug = $options['slug'] ?? '';
if (!$slug) die("Usage: --slug=PAGE_SLUG\n");

$target_dir = dirname(__DIR__) . '/content_state/remote/';
if (!is_dir($target_dir)) mkdir($target_dir, 0777, true);

$sep = "|||SEP|||";
$query = "SET NAMES utf8mb4; SELECT CONCAT(ID, '$sep', post_title, '$sep', post_name, '$sep', post_content, '$sep', post_type, '$sep', post_status, '$sep', post_modified) FROM fxr_posts WHERE post_name = '$slug' AND post_type = 'page' AND post_status = 'publish' LIMIT 1;";

$sql_file = __DIR__ . '/pull_' . $slug . '.sql';
$out_file = __DIR__ . '/pull_' . $slug . '.out';
file_put_contents($sql_file, $query);

shell_exec('.\mysql_remote.bat -N -s -r --default-character-set=utf8mb4 < ' . escapeshellarg($sql_file) . ' > ' . escapeshellarg($out_file));
$raw = file_get_contents($out_file);

if (file_exists($sql_file)) unlink($sql_file);
if (file_exists($out_file)) unlink($out_file);

if (!$raw || trim($raw) === '') {
    die("No data returned for slug: $slug\n");
}

$parts = explode($sep, trim($raw));
if (count($parts) < 6) die("Unexpected format\n");

echo "ID: {$parts[0]}\n";
echo "Title: {$parts[1]}\n";
echo "Slug: {$parts[2]}\n";
echo "Type: {$parts[4]}\n";
echo "Status: {$parts[5]}\n";
echo "Modified: {$parts[6]}\n";
echo "Content length: " . strlen($parts[3]) . " chars\n";

// Save txt backup
$txt_file = $target_dir . $slug . '.txt';
file_put_contents($txt_file, $parts[3]);
echo "Saved to: remote/$slug.txt\n";
