# DAW Knowledge & Standards — Agnostic Core

Este archivo es la **Verdad Absoluta (Ground Truth)** del proyecto. Todo agente debe seguir estas directrices para asegurar la integridad de la arquitectura.

---

## 1. Arquitectura de Orquestación (DAW v4.0)

Para la creación de cualquier página o componente, se DEBE seguir el flujo **Divi Agentic Workflow (DAW)** de cuatro fases:

| Fase | Rol | Responsabilidad | Entregable |
| :--- | :--- | :--- | :--- |
| **1. Análisis** | Arquitecto | Define la estructura semántica y objetivos de negocio | Plan Semántico (JSON) |
| **2. Dirección** | Design Lead | Investiga dirección visual, valida UX, documenta decisiones | Documento de dirección visual |
| **3. Mapeo** | Diseñador | Traduce el plan + dirección a bloques `divi/*` nativos y tokens `{{design:*}}` | JSON Schema listo para el Layout_Engine |
| **4. Ejecución** | Ingeniero | Ejecuta el comando WP-CLI y verifica la persistencia | WP Post ID confirmado |

**Prohibición:** No se permite la creación manual de contenido HTML/CSS ad-hoc que ignore el sistema nativo de WordPress.

---

## 2. Dependencia del Sistema de Diseño (Obligatorio)

Todo proyecto DAW depende **estrictamente** de un archivo de sistema de diseño precargado en la ruta `workspace/design-system/<proyecto>.json` (ej. `san-pablo-mx.json`).

**Prohibición Absoluta:** Ningún agente (ni el Design Lead ni el Designer) puede inventar, asumir o hardcodear colores, fuentes, radios o tokens que no estén explícitamente declarados en el archivo del proyecto actual.

- **Tokens Semánticos `{{design:*}}`**: El archivo JSON define los tokens exactos disponibles bajo los nodos `color`, `font`, `radius`, `space`. Por ejemplo, si el JSON expone `{{design:color:ink}}` o `{{design:color:primary}}`, solo esos pueden usarse. No se permite inventar `{{design:color:magenta}}` si no existe.
- **Presets de Diseño (`presets`)**: El archivo JSON incluye configuraciones pre-fabricadas (ej. `section.hero-dark`, `module.card`). 
- **Estándar de Calidad Ultra-Premium Universal**: Independientemente de los colores de la marca, los componentes deben mantener un estándar premium. Esto significa usar los valores de `radius` más grandes, sombras difusas (alta difusión, baja opacidad) para el `boxShadow`, y tokens de espaciado masivos (`space.xl`, `space.3xl`) para asegurar que el diseño respire (whitespace abundante).

> [!IMPORTANT]
> El Layout_Engine reemplaza los tokens `{{design:*}}` en el JSON generado por el Designer *antes* de compilar a bloques Divi. Para variables de entorno, también soporta `{{SITE_URL}}` y `{{SITE_NAME}}`.

---

## 3. Estándares Técnicos

- **Motor:** Divi 5.5.0 Native (bloques Gutenberg `<!-- wp:divi/... -->`).
- **CLI:** Uso mandatorio de `./wp.bat agentic deploy_page` (wrapper local de WP-CLI).
- **Namespace bloques:** SIEMPRE usar `divi/section`, `divi/row`, `divi/column`, `divi/text`, `divi/code`, `divi/image`, `divi/button`, `divi/menu`. **NUNCA** usar `et_pb_*`.
- **Estilos:** Usar configuraciones nativas de WordPress, `theme.json`, patrones, estilos de bloque y atributos permitidos por el bloque.
- **Híbrido:** El código debe ser 100% editable en el Visual Builder. Evitar `!important` globales.
- **CSS Prohibido:** No añadir CSS a `style.css` del child theme. Todo CSS debe resolverse de forma nativa en WordPress.
- **Versión de meta:** El motor fija automáticamente `_et_pb_built_with_d5 = 1` y `_et_builder_version = 5.5.0`.

---

## 4. Directorios Clave del Proyecto

| Directorio / Archivo | Propósito |
| :--- | :--- |
| `workspace/pages/*.json` | **Fuente de schemas JSON** de páginas. Aquí se guardan todos los esquemas. |
| `workspace/docs/DEPLOYMENT-GUIDE.md` | Guía de despliegue detallada con referencia de bloques y estilos nativos |
| `workspace/automation/` | Scripts PHP/PS para sincronización y despliegue a producción |
| `workspace/content_state/local/` | Volcados de DB local en `.txt` (fuente de verdad de contenido existente) |
| `app/public/wp-content/themes/divi-agentic-core/inc/core/class-layout-engine.php` | Motor compilador JSON → bloques Divi 5 |
| `app/public/wp-content/themes/divi-agentic-core/inc/cli/class-agentic-command.php` | Registro de comandos `wp agentic` y validador de esquemas nativos |
| `.agents/skills/daw-skill/` | Este skill (fuente de verdad del flujo DAW) |

---

*Última actualización: 2026-05-20 — DAW-Skill Local v2.1*
