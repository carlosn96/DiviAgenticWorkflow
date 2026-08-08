# Implementation Plan: Design Quality Gate

## Overview

Cerrar el ciclo huevo-gallina: que `_design_vars.json` no pueda sincronizarse a WordPress sin pasar por un quality gate que valide contraste, escalas, pares tipográficos y coherencia cromática. Tres capas: metadatos en `Token_Registry`, validador PHP autónomo, enforcement en `wp brand sync`.

## Architecture Decisions

| Decisión | Por qué |
|----------|---------|
| Reglas de validación en `Token_Registry` | Único lugar donde se definen tokens. Si cambia un token, su validación cambia con él. |
| `Design_Validator` es PHP puro | Determínistico, sin dependencias externas, corre en cada `sync`. |
| `sync` exige `validate` pasar | El quality gate es técnico, no documental. Sin approve técnico no hay sync. |
| `--force` bypass | Para power users que saben lo que hacen. |

## Dependency Graph

```
Token_Registry (add validate metadata)
    │
    ├── Design_Validator (lee metadatos, ejecuta checks)
    │       │
    │       ├── wp brand validate (CLI)
    │       │
    │       └── Brand_Sync_Handler::run() (gate enforcement)
    │
    └── docs (wire DAW skill Fase 2 + AGENTS.md)
```

## Task List

### Phase 1: Foundation — Validation metadata en `Token_Registry`

**Task 1.1: Añadir `validate` a tokens de color**

Cada token `color_*` recibe:
- `contrast_against: string[]` — qué otros tokens debe contrastar
- `contrast_min: float` — ratio mínimo (3.0 large, 4.5 body)
- `harmony_group: string` — primary, surface, text, functional

Ejemplo:
```php
'color_accent' => [
    'type'     => 'color',
    'required' => true,
    'validate' => [
        'contrast_against' => ['color_surface_deep', 'color_surface_light', 'color_surface_white'],
        'contrast_min'     => 3.0,
        'harmony_group'    => 'primary',
    ],
    'et_divi' => [...],
],
```

**Task 1.2: Añadir `validate` a tokens de tipografía y escala**

- `font_display`, `font_body`, `font_ui`: `pairing_incompatible_with` — qué fuentes NO puede pairing
- `font_heading_size_h1..h6`, `font_body_size`: `scale_group` + `expected_ratio`
- `space_*`: `scale_group` + `expected_ratio`
- `radius_*`: `scale_group` + `expected_ratio`

**Files touched:** `inc/core/class-token-registry.php`
**Scope:** M (~4h de trabajo de datos)

---

### Phase 2: Core — `Design_Validator` class

**Task 2.1: Implementar checks de color**

- `check_contrast(string $hex1, string $hex2): float` — WCAG relative luminance
- `check_contrast_pair(string $token_key, array $vars, array $rule): array` — status + ratio + message
- Iterar todos los tokens `color_*` con `validate.contrast_against`
- Reportar: pass si ≥ min, warn si ≥ min-0.5, fail si <

**Task 2.2: Implementar checks de escala**

- `check_scale_progression(array $values, string $group, float $expected_ratio): array`
- Para heading sizes: h1→h2, h2→h3, etc. deben seguir una progresión armónica
- Para spacings: xs, sm, md, lg, xl, 2xl, 3xl deben escalar consistentemente
- Ratio default: 1.25 (Perfect Fourth) para headings, 1.5 (Perfect Fifth) para spacings

**Task 2.3: Implementar checks de font pairing**

- `check_font_pairing(string $font_a, string $font_b): array`
- Matriz de compatibilidad: sans+sans fail, serif+sans pass, display+sans warn
- Si dos fuentes son de la misma categoría (script, display, sans, serif, mono) y no son la misma familia → fail

**Task 2.4: Integrar checks en `Design_Validator::run()`**

```php
public static function run(array $vars): array {
    $results = [];

    // 1. Color contrast pairs
    $results = array_merge($results, self::check_all_contrasts($vars));

    // 2. Heading scale progression
    $results[] = self::check_heading_scale($vars);

    // 3. Spacing scale progression
    $results[] = self::check_spacing_scale($vars);

    // 4. Font pairing
    $results[] = self::check_font_pairing(
        $vars['font_display'] ?? '',
        $vars['font_body'] ?? ''
    );

    // 5. Aggregate
    $results['_summary'] = [
        'total'   => count($results),
        'pass'    => count(array_filter($results, fn($r) => $r['status'] === 'pass')),
        'warn'    => count(array_filter($results, fn($r) => $r['status'] === 'warn')),
        'fail'    => count(array_filter($results, fn($r) => $r['status'] === 'fail')),
        'gate'    => self::gate_passes($results),
    ];

    return $results;
}
```

**Files touched:**
- `inc/core/class-design-validator.php` (nuevo)
**Scope:** M (~5h)

---

### Phase 3: CLI — `wp brand validate`

**Task 3.1: Añadir subcomando `validate` a `Brand_Command`**

```powershell
wp brand validate <slug>
```

- Lee `_design_vars.json`
- Corre `Design_Validator::run($vars)`
- Muestra reporte estructurado: cada check con status + valor actual + esperado + mensaje
- Exit code: 0 = all pass, 1 = some fail

**Task 3.2: Añadir flag `--json` para output machine-readable**

- `wp brand validate <slug> --json` → stdout JSON procesable por skills

**Files touched:**
- `inc/cli/class-brand-command.php`
**Scope:** S (~2h)

---

### Phase 4: Gate — Integrar en `Brand_Sync_Handler`

**Task 4.1: Llamar `Design_Validator::run()` antes de sync**

```php
public static function run(?string $site = null, bool $force = false): void {
    // ... load vars ...

    if (!$force) {
        $validation = Design_Validator::run($vars);
        if (!$validation['_summary']['gate']) {
            WP_CLI::error('Design validation failed. Run wp brand validate for details.');
            WP_CLI::log('Use --force to sync anyway.');
        }
    }

    // ... proceed to sync ...
}
```

**Task 4.2: Añadir `--force` flag a `wp brand sync`**

```powershell
wp brand sync <slug> --force
```

**Files touched:**
- `inc/core/class-brand-sync-handler.php`
- `inc/cli/class-brand-command.php`
**Scope:** S (~1h)

---

### Phase 5: Docs — Workflow integration

**Task 5.1: Actualizar AGENTS.md**

- Documentar el flujo: init → cargar skill → editar vars → `validate` → `sync`
- El quality gate ahora es técnico, no documental

**Task 5.2: Actualizar daw-skill/references/design-lead.md**

- Conectar la Fase 2 (6 Leyes, Design Brief) con el nuevo `wp brand validate`
- El Design Brief sigue siendo el gate de **página**; `validate` es el gate de **brand vars**

**Task 5.3: Actualizar RUNBOOK.md**

- Añadir sección de validación de diseño

**Files touched:**
- `AGENTS.md`
- `daw-skill/references/design-lead.md`
- `RUNBOOK.md`
**Scope:** S (~1h)

---

## Checkpoints

### Checkpoint 1 (after Phase 1)
- [ ] `Token_Registry` exports tokens con metadatos de validación
- [ ] Confirmar que `wp brand status` y `wp brand init` siguen funcionando

### Checkpoint 2 (after Phase 2)
- [ ] `Design_Validator::run()` produce reporte con checks de contraste, escala y pairing
- [ ] Verificar con valores conocidos: `#DC2626` sobre `#ffffff` = 3.9:1 (warn), etc.
- [ ] Review con humano antes de pasar a Phase 3

### Checkpoint 3 (after Phase 3+4)
- [ ] `wp brand validate` corre y muestra reporte
- [ ] `wp brand sync` falla si validate no pasa
- [ ] `wp brand sync --force` bypassa
- [ ] End-to-end: init → edit → validate → sync → reset

### Checkpoint 4 (after Phase 5)
- [ ] AGENTS.md refleja el flujo completo
- [ ] RUNBOOK.md actualizado

## Verification commands

```powershell
# Unit-style checks (manual)
wp brand validate netflix
wp brand validate netflix --json

# Gate enforcement
wp brand sync netflix                    # debe fallar si validate no pasa
wp brand sync netflix --force            # debe pasar

# Full pipeline
wp brand init testsite
# editar _design_vars.json con valores malos
wp brand validate testsite               # fails
# editar con valores buenos
wp brand validate testsite               # passes
wp brand sync testsite                   # syncs
wp brand reset testsite
Remove-Item -Recurse site/testsite
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Falsos positivos (rechazar diseño válido) | Medium | Umbrales WCAG estándar, no inventados. `--force` como escape. |
| Token_Registry se vuelve enorme con metadatos | Low | Los metadatos de validación son un campo más por token, no duplican estructura. |
| El DAW skill queda obsoleto | Low | No — la Fase 2 sigue validando página; esto valida brand vars. Son complementarios. |

## Decisions

| Pregunta | Decisión |
|----------|----------|
| Umbrales WCAG | **AAA**: 7:1 body text, 4.5:1 large text (>18px). Warn si ≥ AA (4.5:1 / 3:1). Fail si < AA. |
| Font pairing matrix | **Hardcodeada** en PHP por categorías: sans, serif, display, script, mono. Dos de la misma categoría = fail. |
| `--force` | **Visible**: loggear advertencia clara en output de sync. "⚠️ Bypass de validación de diseño — usar solo si sabes lo que haces." |
