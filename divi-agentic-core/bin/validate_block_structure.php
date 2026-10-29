<?php
require_once 'app/public/wp-load.php';
$post_id = isset($argv[1]) ? intval($argv[1]) : 127774;
$post = get_post($post_id);
if (! $post) { echo "NO POST $post_id\n"; exit(1); }
$blocks = parse_blocks($post->post_content);

echo "Top-level blocks: " . count($blocks) . "\n";
foreach ($blocks as $i => $block) {
    $name = $block['blockName'] ?? 'null';
    echo "  $i: $name\n";
    if (! empty($block['innerBlocks'])) {
        echo "    inner: " . count($block['innerBlocks']) . "\n";
    }
}

// Find any block with empty blockName but non-empty content
foreach ($blocks as $block) {
    if (empty($block['blockName']) && ! empty(trim($block['innerHTML']))) {
        echo "Unparsed content fragment:\n";
        echo substr($block['innerHTML'], 0, 300) . "\n";
    }
}
