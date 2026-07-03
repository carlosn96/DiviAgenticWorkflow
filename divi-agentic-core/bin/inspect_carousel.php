<?php
$path = $argv[1] ?? 'php://stdin';
$s = json_decode(file_get_contents($path), true);
foreach ($s['sections'] as $sec) {
    foreach ($sec['rows'] as $row) {
        foreach ($row['columns'] as $col) {
            foreach ($col['modules'] as $mod) {
                $type = $mod['_type'] ?? $mod['type'] ?? '';
                if ($type === 'dgpc/product-carousel') {
                    echo json_encode($mod, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
                    exit(0);
                }
            }
        }
    }
}
echo "not found";
