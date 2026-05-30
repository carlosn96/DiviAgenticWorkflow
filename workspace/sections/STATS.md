# Stats Section — number-counter Pitfall

`divi/number-counter` in the Layout Engine compile path (line ~415) reads `$data['title']` for
`$attrs['title']['innerContent']`. If the incoming title is an object (decoration metadata only,
no text content), the subsequent `strpos($number_val, '%')` on `number` crashes because the
title object pollutes the attrs path.

## Fix applied (class-layout-engine.php:415)

```php
// Before (crash):
$attrs['title']['innerContent'] = [ 'desktop' => ['value' => $data['title'] ?? ''] ];

// After (fallback to label):
$title_text = $data['title'] ?? $data['label'] ?? '';
if (is_array($title_text)) {
    $title_text = $title_text['innerContent']['desktop']['value'] ?? $data['label'] ?? '';
}
$attrs['title']['innerContent'] = [ 'desktop' => ['value' => $title_text ] ];
```

## Why compose_page.php templates must include `label`

The `number-counter` module's `title` in Divi 5 is a decoration-only attribute (font, color).
The actual text content comes from `label`. Templates must set both:
```json
{
  "type": "divi/number-counter",
  "number": "{{slot:number}}",
  "label": "{{slot:label}}"
}
```
