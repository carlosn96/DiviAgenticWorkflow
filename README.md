# DAW Bundle (Divi Agentic Workflow)

Este bundle agrupa el ecosistema completo para generar, diseñar y desplegar páginas en WordPress de forma agéntica, asegurando **100% de compatibilidad con Divi 5 Native**.

## Arquitectura de 4 Fases

El framework divide el esfuerzo en 4 especialidades para maximizar el razonamiento del LLM:
1. **Análisis (Arquitecto)**: Define semántica y elección de bloques Divi.
2. **Dirección (Design Lead)**: Define patrones UI/UX usando el subsistema `ui-ux-pro-max`.
3. **Mapeo (Diseñador)**: Traduce requerimientos a estructuras JSON mediante `workspace/daw_builder.py`.
4. **Ejecución (Ingeniero)**: Inyecta el contenido en WordPress vía WP-CLI.

## Dependencia Obligatoria: El Sistema de Diseño

Para que los esquemas JSON de la Fase 3 sean válidos y el motor de la Fase 4 los pueda renderizar, el proyecto destino **DEBE contar con un Sistema de Diseño JSON** (por ejemplo: `workspace/design-system/proyecto.json`).

**Regla de Oro:** Ningún esquema (generado por `daw_builder.py`) debe contener colores hexadecimales o píxeles hardcodeados. En su lugar, el Diseñador usa **tokens**.
Ejemplos:
- Color: `{{design:color:primary}}` o `{{design:color:ink}}`
- Tipografía: `{{design:font:heading}}`
- Espaciado: `{{design:space:xl}}`

El `Layout_Engine` (incluido en `divi-agentic-core`) es el responsable de interceptar el esquema durante el despliegue, leer el sistema de diseño local, y compilar los tokens a atributos reales en la base de datos de WordPress.

## Instrucciones de Uso

1. **Configuración CLI (`.env`)**  
   Copia el archivo `.env.example` como `.env` en la raíz de tu proyecto e indica si usarás binarios globales (`wp`) o wrappers (`.\wp.bat`).

2. **Núcleo PHP (Wordpress)**  
   Mueve e importa el código de la carpeta `divi-agentic-core` a tu instalación de WordPress (en el theme o como MU plugin). Este otorga al CLI el comando crítico `wp agentic deploy_page`.

3. **Orquestación**  
   Dirige a tu agente hacia la ruta `daw-skill/SKILL.md` para iniciar cualquier tarea de construcción de páginas.