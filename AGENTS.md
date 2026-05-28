# DAW — Divi Agentic Workflow

Este documento es la fuente de verdad para todo el flujo de diseño y despliegue de páginas Divi 5. Es autocontenido: un agente que solo vea esta carpeta puede operar sin depender de la raíz del proyecto.

Todos los paths son relativos a `DAW_bundle/` a menos que se indique lo contrario. Los comandos se ejecutan desde la raíz del proyecto (`divitheme/`).

---

## 1. Mapa del DAW

```
DAW_bundle/
├── AGENTS.md                      <- Este archivo (punto de entrada al DAW)
├── README.md                      <- Documentación rápida
├── .env.example                   <- Template de configuración
├── .gitignore                     <- Reglas git del framework
├── wp.bat, php.bat, mysql.bat     <- Wrappers genéricos (delegan a raíz del proyecto)
├── site/                          <- ⭐ DATOS DE PROYECTO (separados del framework)
│   ├── bibliotheca/               <-    Marca activa: San Pablo MX / Bibliotheca
│   │   ├── brand/                 <-       _design_vars.json + _design_presets.json
│   │   ├── page-defs/             <-       ⭐ ENTRADA: JSON semántico del diseñador (tokens {{design:*}}, presets)
│   │   ├── pages/                 <-       SALIDA OPCIONAL: schema resuelto por build_page.php (--out, solo debug)
│   │   ├── design-system/         <-       divitheme.json generado (gitignored)
│   │   ├── briefs/                <-       Briefs de diseño
│   │   └── content_state/         <-       Estado entre fases (local/ + remote/)
│   └── example/                   <-    Template para nuevas marcas (brand/, page-defs/, etc.)
├── ui-ux-pro-max/                 <- Skill de diseño UI/UX (opcional)
├── daw-skill/SKILL.md             <- FLUJO PRINCIPAL: orquestación de 4 fases
├── workspace/                     <- Código fuente del framework
│   ├── build_design_system.py     <- GENERADOR del design system (site/*/brand/ → divitheme.json)
│   ├── data/modules/              <- Schemas de módulos generados por PHP (102 módulos)
│   └── automation/                <- Scripts de automatización
└── divi-agentic-core/
    ├── Plugin WordPress (Layout Engine, CLI, metadata)
    └── bin/
        └── build_page.php         <- ⭐ PUNTO ÚNICO DE ENTRADA ($DAW_SITE via env)
```

---

## ⚡ Primeros Pasos (Quickstart)

```powershell
# 1. Activar el plugin
#    Ir a WP Admin > Plugins > "Divi Agentic Core" > Activar
#    (junction link desde DAW_bundle/divi-agentic-core/ → app/public/wp-content/plugins/)

# 2. Configurar entorno
Copy-Item DAW_bundle/.env.example .env        # editar con credenciales reales

# 3. (una vez) Generar schemas de módulos Divi 5
.\php.bat DAW_bundle/divi-agentic-core/bin/generate-module-schema.php --all

# 4. (una vez por marca) Generar design system
#    Variables en: site/<DAW_SITE>/brand/_design_vars.json
#    Presets en:   site/<DAW_SITE>/brand/_design_presets.json
$env:DAW_SITE="bibliotheca"
python DAW_bundle/workspace/build_design_system.py

# 5. Sincronizar colores globales en Divi 5
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"

# 6. Crear definición de página en site/bibliotheca/page-defs/<slug>.json
#    (ver site/bibliotheca/page-defs/home.json como plantilla)

# 7. Build + Deploy (un solo comando)
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=DAW_bundle/site/bibliotheca/page-defs/mi-pagina.json `
  --deploy
```

---

## 2. Pipeline: diseño → deploy (PHP unificado)

```
Capa 0 — Module Schemas (PHP, fuente única de estructura)
  php divi-agentic-core/bin/generate-module-schema.php --all
  → Lee _all_modules_metadata.php (metadata real de Divi 5)
  → workspace/data/modules/<slug>.json (102 módulos, estructura autoritativa)
  ⚠️ build_page.php NO define atributos de módulo — los carga de estos JSONs.

Capa 1 — Design System (build_design_system.py)
  site/bibliotheca/brand/_design_vars.json + site/bibliotheca/brand/_design_presets.json
  → build_design_system.py
  → site/bibliotheca/design-system/divitheme.json
    (57 presets con referencias {{design:type:name}} + tokens)

Capa 2 — Page Schema + Deploy (build_page.php — UN SOLO COMANDO)
  php divi-agentic-core/bin/build_page.php --def=page-defs/mipagina.json --deploy

  build_page.php hace TODO:
    • Lee page-defs/<slug>.json desde site/<DAW_SITE>/page-defs/ (ver §3)
    • Carga estructura de módulo desde schema PHP (workspace/data/modules/)
    • Carga design system desde site/<DAW_SITE>/design-system/divitheme.json
    • Resuelve {{design:color:name}} → var(--gcid-*)
    • Resuelve {{design:font|radius|space:name}} → literales
    • Expande presets inline via deep_merge()
    • Normaliza gradient stops
    • Valida estructura (sections → rows → columns → modules)
    • Escribe site/<DAW_SITE>/pages/<slug>.json (schema completo)
    • [--deploy] Ejecuta wp agentic deploy_page
      → Layout Engine convierte var(--gcid-*) → $variable() en post_content
      → Visual Builder reconoce colores globales

  ⚠️ Sin Python en el pipeline de página. Sin archivos intermedios.
     Un solo lenguaje (PHP), un solo comando.

### page-defs/ vs pages/ (duda frecuente)

| Carpeta | Rol | Quién escribe | Git |
|---------|-----|---------------|-----|
| `page-defs/` | **Entrada** — JSON semántico del diseñador con `{{design:*}}` tokens y presets por nombre. El pipeline lee de aquí. | El diseñador (Fase 3) | Trackeado |
| `pages/` | **Salida opcional** — Schema completo con tokens resueltos, presets expandidos inline. `build_page.php` genera esto solo si se pasa `--out`. NO es necesario para el deploy (`--deploy` trabaja en memoria). | `build_page.php` | Ignorado |

> El flujo normal es `page-defs/<slug>.json → build_page.php --deploy`. `pages/` existe únicamente para debug: inspeccionar el schema resuelto antes de enviarlo a WordPress.
```

---

## 3. Crear una página nueva (PHP-only)

0. (Una vez por proyecto o tras actualizar Divi) Regenerar schemas de módulos:
   ```
   .\php.bat DAW_bundle/divi-agentic-core/bin/generate-module-schema.php --all
   ```

1. Crear definición de página en `site/<DAW_SITE>/page-defs/<slug>.json`:

   > `DAW_SITE` defaults to `bibliotheca`. Para usar otra marca: `$env:DAW_SITE="minuevamarca"`

```json
{
  "title": "Título de la Página",
  "slug": "mi-pagina",
  "description": "Opcional",
  "sections": [
    {
      "presets": ["section:hero-dark"],
      "parallax": "on",
      "bg_gradient": {
        "type": "linear", "direction": "135deg",
        "overlaysImage": "on",
        "stops": [
          {"color": "rgba(15,23,42,0.92)", "position": "0"},
          {"color": "rgba(15,23,42,0.35)", "position": "100"}
        ]
      },
      "rows": [
        {
          "column_structure": "4_4",
          "modules": [
            {"type": "divi/text", "presets": ["text:eyebrow"],
             "content": "<p>Subt&iacute;tulo</p>"},
            {"type": "divi/text", "presets": ["text:display-xl"],
             "content": "<h1>T&iacute;tulo Principal</h1>"}
          ]
        },
        {
          "column_structure": "1_2,1_2",
          "columns": [
            {"type": "1_2", "modules": [
              {"type": "divi/button", "presets": ["module:btn-primary"],
               "button_text": "Acci&oacute;n", "button_url": "/ruta"}
            ]},
            {"type": "1_2", "modules": [
              {"type": "divi/blurb", "presets": ["module:feature-card"],
               "title": "Feature", "icon": "&#xe03a;"}
            ]}
          ]
        }
      ]
    }
  ]
}
```

**Formato de definición:**
- `sections[]` — arreglo de secciones
  - `presets[]` — refs a presets del design system (`section:*`, `text:*`, `module:*`)
  - `rows[]` — arreglo de filas
    - `column_structure` — string como `"4_4"`, `"1_2,1_2"`, `"1_3,1_3,1_3"`
    - `modules[]` — (modo simple) módulos en columna única (4_4 implícito)
    - `columns[]` — (modo explícito) arreglo de columnas, cada una con `type` y `modules[]`
    - `module.type` — nombre del módulo Divi 5: `divi/text`, `divi/blurb`, etc.
    - `module.presets[]` — presets a aplicar (se expanden inline)
    - `module.decoration` — decoration object (spacing, border, boxShadow, animation, etc.)
    - `animation`, `scroll`, `transform` — motion presets como string (ej: `"fade-in"`)

2. Build + Deploy (un solo paso):
   ```
   .\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php --def=site/bibliotheca/page-defs/mi-pagina.json --deploy
   ```

   Opciones adicionales:
   - `--out=path.json` — escribir schema sin desplegar
   - `--no-resolve` — schema raw sin expandir presets/tokens (debug)
   - `--deploy --front` — desplegar y establecer como portada
   - `--deploy --verify` — ejecutar verificación post-deploy (comprueba gcids, bloques, estructura)
   - `--deploy --verify --url="https://..."` — verificación + acceso HTTP público
   - `DAW_SITE` env var — cambiar proyecto activo (`$env:DAW_SITE="otromarca"`)

   La verificación post-deploy ejecuta `verify_page.php` que comprueba:
   - La página existe en WordPress
   - El contenido contiene bloques Divi 5
   - Las variables `var(--gcid-*)` están presentes
   - No quedan tokens `{{design:*}}` sin resolver
   - Coincidencia estructural vs schema (opcional con `--schema`)
   - Accesibilidad HTTP pública (opcional con `--url`)

   > Para verificación visual (screenshot), integrar con Playwright:
   > `npx playwright wk http://localhost/mi-pagina --screenshot`

---

## 4. Sistema de Diseño

No editar `divitheme.json` a mano. Usar `build_design_system.py` (v2.0, data-driven):

```
python DAW_bundle/workspace/build_design_system.py ^
  --vars DAW_bundle/site/bibliotheca/brand/_design_vars.json ^
  --presets DAW_bundle/site/bibliotheca/brand/_design_presets.json ^
  --out DAW_bundle/site/bibliotheca/design-system/divitheme.json
```

Para otra marca: `$env:DAW_SITE="otramarca"` antes de ejecutar, o pasar rutas explicitas con `--vars`/`--presets`/`--out`.

Sincronizar colores globales en Divi 5:
```
.\wp.bat agentic global_colors sync ^
  --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"
```

El generador auto-descubre tokens por prefijo (`color_`, `font_`, `radius_`, `space_`) de cualquier archivo de variables. No hay nombres hardcodeados en Python — funciona con cualquier marca.

**Colores**: se referencian como `{{design:color:name}}` y el resolver los convierte a `var(--gcid-name)` (dinámico). Los tokens en `divitheme.json` mantienen valores hex para el sync de gcids.

**Fonts, radii, spacing**: se referencian como `{{design:font:name}}`, `{{design:radius:name}}`, `{{space_name}}` y se resuelven a literales (horneados en build).

---

## 5. Prerrequisito: Global Colors (gcid)

Antes del primer deploy, sincronizar colores. El verificador de hash está en `_dac_gcid_hash`:

| Acción | Comando |
|--------|---------|
| Sincronizar | `wp agentic global_colors sync --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"` |
| Verificar estado | `wp agentic global_colors status --design-system="..."` |
| Listar activos | `wp agentic global_colors list` |

Si no hay gcids sincronizados, `deploy_page` emite warning y resuelve a hex.

---

## 6. Referencias

| Recurso | Path (desde DAW_bundle/) | Propósito |
|---------|--------------------------|-----------|
| SKILL.md (4 fases) | `daw-skill/SKILL.md` | Orquestación completa análisis → diseño → mapeo → CLI |
| Diccionario de bloques | `daw-skill/references/blocks-dictionary.md` | Guía de 94+ bloques Divi 5 |
| Lógica del Diseñador | `daw-skill/references/designer.md` | Mapeo semántico → bloques, tokens, decoration |
| Lógica del Ingeniero | `daw-skill/references/engineer.md` | Comandos CLI, deploy, verificación |
| Build page (PHP) | `divi-agentic-core/bin/build_page.php` | Pipeline unificado PHP (usa `DAW_SITE` env) |
| Design system (generado) | `site/<DAW_SITE>/design-system/divitheme.json` | 57 presets, fuente de verdad de tokens |
| Variables de entrada | `site/<DAW_SITE>/brand/_design_vars.json` | Colores, fonts, radios, espacio |
| Presets de diseño | `site/<DAW_SITE>/brand/_design_presets.json` | 57 presets (section/text/module/animation/scroll/hover) |
| Definiciones de página | `site/<DAW_SITE>/page-defs/` | JSON de entrada (home.json, about.json...) |
| Schemas de páginas | `site/<DAW_SITE>/pages/` | JSON generados (output de build_page.php) |
| Plugin WordPress | `divi-agentic-core/` | Layout Engine, CLI, metadata |

---

## 7. Estructura de Carpetas

Cada tipo de archivo tiene su carpeta asignada. No crear archivos fuera de su ubicación:

| Carpeta | Contenido |
|---------|-----------|
| `site/<DAW_SITE>/brand/` | ⭐ Datos de marca: `_design_vars.json` + `_design_presets.json` |
| `site/<DAW_SITE>/page-defs/` | ⭐ Definiciones de página en JSON (entrada al pipeline, lo que escribe el diseñador) |
| `site/<DAW_SITE>/pages/` | Schemas resueltos (output opcional de `build_page.php --out`, solo para debug/inspección) |
| `site/<DAW_SITE>/design-system/` | `divitheme.json` generado (output, gitignored) |
| `site/<DAW_SITE>/briefs/` | Briefs de diseño por página |
| `site/<DAW_SITE>/content_state/` | Estado de contenido entre fases (local/ + remote/) |
| `site/example/` | Template de estructura para nuevas marcas |
| `workspace/data/modules/` | Schemas de módulos Divi 5 (102, generados por PHP) |
| `workspace/automation/` | Scripts de automatización |
| `workspace/build_design_system.py` | Generador de design system (único Python activo) |
| `divi-agentic-core/bin/` | ⭐ build_page.php + generate-module-schema.php |
| `daw-skill/` | Skill de orquestación y sus referencias |
| `divi-agentic-core/` | Plugin WordPress |
| `ui-ux-pro-max/` | Skill auxiliar de diseño UI/UX (opcional) |

### Cómo crear una nueva marca

```powershell
# 1. Copiar template de ejemplo
Copy-Item -Recurse DAW_bundle/site/example DAW_bundle/site/minuevamarca

# 2. Crear archivo de variables (solo las que cambian respecto a defaults ultra-pro)
#    build_design_system.py auto-descubre tokens por prefijo:
#    color_ → color, font_ → font, radius_ → radius, space_ → spacing
#    Ver site/example/brand/_design_vars.json como referencia
cat > DAW_bundle/site/minuevamarca/brand/_design_vars.json @'
{
  "brand_name": "Mi Marca",
  "brand_description": "Descripción del proyecto",
  "color_accent": "#8B6F47",
  "color_ink": "#1C1A17",
  "font_display": "Playfair Display",
  "radius_sm": "4px"
}
'@

# 3. Crear archivo de presets (opcional: si no existe, se usan 57 defaults ultra-pro)
#    Categorías: section, text, module, animation, scroll, transform
#    Usar {{design:color:name}}, {{design:font:name}}, {{design:radius:name}}, {{space_name}}
#    Ver site/example/brand/_design_presets.json como referencia

# 4. Generar design system (apuntando a la nueva marca)
$env:DAW_SITE="minuevamarca"
python DAW_bundle/workspace/build_design_system.py

# 5. Sincronizar colores en Divi 5
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/minuevamarca/design-system/divitheme.json"
```

**Regla**: todo dato de marca va en `site/<DAW_SITE>/brand/`. Definiciones de página en `site/<DAW_SITE>/page-defs/`. Código PHP de build en `divi-agentic-core/bin/`. 
**Framework**: no mezclar datos de proyecto con el código del DAW. `site/` es la frontera.

---

## 8. Reglas DAW

1. No editar `divitheme.json` a mano — siempre regenerar con `build_design_system.py`.
2. No usar `divi/code` como comodín — consultar `blocks-dictionary.md` primero.
3. No usar `et_pb_*` (shortcodes Divi 4) — solo namespace `divi/*`.
4. Colores siempre como `{{design:color:*}}`, nunca hex hardcodeados en schemas.
5. `build_page.php` con resolved=true (default) expande presets inline y resuelve tokens.
6. Sin CSS inyectado en `functions.php` ni overrides en `style.css`.
7. Posiciones de gradient sin `%` (el Layout Engine normaliza).
8. **Frontera site/**: todo dato de proyecto va en `site/<DAW_SITE>/`. El framework DAW (skills, plugin, build scripts) no contiene datos de proyecto.
9. **Pipeline de página**: `site/<DAW_SITE>/page-defs/<slug>.json` → `build_page.php --deploy` → página en WP. Un solo comando PHP, sin Python, sin archivos intermedios.
10. El pipeline de página es 100% PHP. No usar Python para construir páginas.
11. **Multi-marca**: cambiar `$env:DAW_SITE` para alternar entre proyectos en `site/`.
