# DAW Bundle — Divi Agentic Workflow

Pipeline completo PHP para diseñar y desplegar páginas Divi 5 Native.

---

## Requisitos

1. **Plugin activo**: `divi-agentic-core` instalado como plugin de WordPress (junction link desde `DAW_bundle/divi-agentic-core/` → `app/public/wp-content/plugins/divi-agentic-core/`). Activar en WP Admin > Plugins.
2. **Archivo `.env`**: Copiar `DAW_bundle/.env.example` → `.env` en la raíz del proyecto y completar valores reales.
3. **Design System**: `site/bibliotheca/design-system/divitheme.json` (generado con `build_design_system.py`).

---

## ⚡ Quickstart

```powershell
# 1. Activar plugin (WP Admin > Plugins > Divi Agentic Core)

# 2. Configurar entorno
Copy-Item DAW_bundle/.env.example .env

# 3. Generar schemas de módulos (una vez)
.\php.bat DAW_bundle/divi-agentic-core/bin/generate-module-schema.php --all

# 4. Generar design system
$env:DAW_SITE="bibliotheca"
python DAW_bundle/workspace/build_design_system.py

# 5. Sincronizar colores globales
.\wp.bat agentic global_colors sync `
  --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"

# 6. Crear página en site/bibliotheca/page-defs/<slug>.json

# 7. Build + Deploy
.\php.bat DAW_bundle/divi-agentic-core/bin/build_page.php `
  --def=DAW_bundle/site/bibliotheca/page-defs/mi-pagina.json `
  --deploy
```

---

## Pipeline (1 comando)

```
page-defs/<slug>.json → build_page.php --deploy → WordPress
```

```powershell
php DAW_bundle/divi-agentic-core/bin/build_page.php ^
  --def=DAW_bundle/site/bibliotheca/page-defs/home.json ^
  --deploy
```

### Opciones de `build_page.php`

| Flag | Descripción |
|------|-------------|
| `--def=<file>` | Definición de página (en `page-defs/` o ruta completa) |
| `--out=<file>` | Escribir schema resuelto sin desplegar |
| `--deploy` | Construir + desplegar vía `wp agentic deploy_page` |
| `--front` | Establecer como portada (solo con `--deploy`) |
| `--verify` | Ejecutar verificación post-deploy (solo con `--deploy`) |
| `--url=<url>` | URL pública para verificación visual (implica `--verify`) |
| `--site-url=<url>` | URL base para `{{SITE_URL}}` (auto-detectado con `--deploy`) |
| `--no-resolve` | Schema raw sin expandir presets/tokens (debug) |
| `--help` | Ayuda |

---

## Flujo completo

```powershell
# 0. (una vez) Regenerar schemas de módulos tras actualizar Divi
php DAW_bundle/divi-agentic-core/bin/generate-module-schema.php --all

# 1. (una vez por marca) Generar design system desde datos de marca
$env:DAW_SITE="minuevamarca"
python DAW_bundle/workspace/build_design_system.py

# 2. Sincronizar colores globales en Divi 5
wp agentic global_colors sync ^
  --design-system="DAW_bundle/site/bibliotheca/design-system/divitheme.json"

# 3. Build + Deploy (un solo comando)
php DAW_bundle/divi-agentic-core/bin/build_page.php ^
  --def=DAW_bundle/site/bibliotheca/page-defs/mi-pagina.json ^
  --deploy

# 4. Solo build (sin deploy)
php DAW_bundle/divi-agentic-core/bin/build_page.php ^
  --def=DAW_bundle/site/bibliotheca/page-defs/mi-pagina.json ^
  --out=DAW_bundle/site/bibliotheca/pages/mi-pagina.json
```

---

## Estructura

```
DAW_bundle/
├── README.md                           <- Este archivo
├── AGENTS.md                           <- Documentación completa del flujo
├── .env.example                        <- Template de configuración
├── wp.bat, php.bat, mysql.bat          <- Wrappers que delegan a raíz del proyecto
├── site/                               <- ⭐ DATOS DE PROYECTO
│   ├── bibliotheca/                    <-    Marca activa (brand/, page-defs/, design-system/, briefs/, content_state/)
│   └── example/                        <-    Template para nuevas marcas
├── workspace/
│   ├── build_design_system.py          <- Generador de design system (único Python activo)
│   ├── data/modules/                   <- Schemas de módulos Divi 5 (102, generados por PHP)
│   └── automation/                     <- Scripts de automatización
├── daw-skill/                          <- Orquestación de 4 fases (SKILL.md)
├── divi-agentic-core/
│   ├── Plugin WordPress (Layout Engine + CLI + metadata)
│   └── bin/
│       ├── build_page.php              <- ⭐ Pipeline unificado PHP
│       └── generate-module-schema.php  <- Genera schemas de módulos desde metadata real Divi 5
└── ui-ux-pro-max/                      <- Skill externo de diseño UI/UX
```

---

## Reglas

1. Namespace correcto: `divi/*` — nunca `et_pb_*`.
2. Colores como `{{design:color:*}}` — nunca hex hardcodeados.
3. Definiciones de página en `site/<DAW_SITE>/page-defs/`.
4. Pipeline: `site/<DAW_SITE>/page-defs/<slug>.json` → `build_page.php --deploy` → WordPress.
5. Sin CSS inyectado en `functions.php` ni overrides en `style.css`.
6. No editar `divitheme.json` a mano — siempre regenerar con `build_design_system.py`.
7. `build_design_system.py` es el único Python activo; el resto del pipeline es PHP.
8. **site/ es la frontera**: framework DAW puro arriba, datos de proyecto en `site/<DAW_SITE>/`.

---

## Referencias

| Recurso | Path |
|---------|------|
| Documentación completa | `AGENTS.md` |
| Orquestación 4 fases | `daw-skill/SKILL.md` |
| Diccionario de bloques | `daw-skill/references/blocks-dictionary.md` |
| Lógica del diseñador | `daw-skill/references/designer.md` |
| Lógica del ingeniero | `daw-skill/references/engineer.md` |
