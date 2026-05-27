# Manual Operativo DAW: Ecosistema INC v3.0

Este documento define el flujo de trabajo de alta fidelidad para el **Diseñador automático Divi5**. Cada página debe seguir este proceso de 4 fases para garantizar autoridad, diseño premium y editabilidad total.

## Fase 0: El Briefing (Estrategia de Diseño)
*Inspirado en la inteligencia UI/UX Pro Max.*

Antes de generar cualquier bloque, el agente debe orquestar un **Briefing Estratégico** siguiendo estos pasos tácticos:

1.  **Extracción de Contexto**: El agente debe leer el mapa del sitio (`brief-mapa.md` o archivos en `content_state/local/`) para entender cómo encaja la nueva página en el ecosistema.
2.  **Investigación Técnica (NATIVA: `UX_Engine`)**: El agente consulta internamente el motor de inteligencia absorbido:
    *   **Acción**: El agente invoca el `UX_Engine` para obtener patrones de *Storytelling*, *Pricing* y *UX Guidelines* específicos del sector educativo directamente desde la base de datos integrada en `inc/core/intelligence/db/`.
    *   **Extracción**: Se extraen obligatoriamente los patrones de conversión y anti-patrones institucionales.
3.  **Definición del ADN Visual**: Consultar el `architectural-manifesto.md` para seleccionar los tokens y presets que aplicarán (ej. Presets `hero` y `card` para la oferta).
4.  **Generación del Brief**: Crear un artefacto en `workspace/briefs/<slug>.md` con:
    - **Objetivo Estratégico**: (Ej. Convertir prospectos en citas informativas).
    - **Mapa de Componentes**: Lista secuencial de lo que se construirá.
    - **Copia Maestra (Copywriting)**: Títulos y textos clave con tono institucional.

## Fase 1: La Arquitectura (El Arquitecto)
*Responsable: `Page_Brain.php`*

1.  **Traducción de Brief**: El Cerebro toma el `brief.md` y selecciona el blueprint adecuado (Landing, Service, History).
2.  **Composición Semántica**: Define el orden de las secciones y el contenido textual basado en la jerarquía institucional.
3.  **Salida**: Un esquema JSON estructurado con tipos de módulos nativos de Divi 5.

## Fase 2: El Diseño (El Diseñador)
*Responsable: `AI_Bridge.php` + `Layout_Engine.php`*

1.  **Resolución de Estilo**: El `AI_Bridge` traduce la intención del brief en **Tokens de Diseño** específicos.
2.  **Inyección de Presets**: El `Layout_Engine` aplica los presets institucionales (`hero`, `card`, `glass`) inyectando valores reales (padding, hex, border-radius) en los atributos de decoración.
3.  **Inyección Nativa**: Se asegura de que cada valor sea visible y editable en el Visual Builder de Divi.

## Fase 3: Ejecución e Ingeniería (El Ingeniero)
*Responsable: CLI + `manage_content.php`*

1.  **Despliegue Local**: Ejecutar el comando de generación, **pasando el brief** para que el cerebro lo use como contexto:
    ```powershell
    .\wp.bat agentic generate --prompt="Admisiones 2026 con hero, proceso, costos y FAQ" --title="Admisiones" --slug="admisiones" --brief="workspace/briefs/admisiones.md" --deploy
    ```
2.  **Snapshot de Estado**: Registrar el cambio en el ecosistema local para permitir futuras ediciones o despliegues remotos:
    ```powershell
    .\php.bat workspace\automation\manage_content.php --mode=local
    ```
3.  **Despliegue a Producción (Opcional)**: Usar el protocolo Hex-Safe detallado en `AGENTS.md` para inyectar el contenido en SiteGround.

---

## Reglas Críticas para la Excelencia
- **Brief Primero**: Nunca generar una página sin haber analizado el Brief previo.
- **Zero Emojis**: Usar siempre iconos de Tabler/SVG.
- **Editabilidad Total**: Si el diseñador gráfico no puede editar un margen desde el panel de Divi, el agente ha fallado.
- **Consistencia de Tokens**: Siempre usar `{{token:name}}` para permitir cambios globales.
