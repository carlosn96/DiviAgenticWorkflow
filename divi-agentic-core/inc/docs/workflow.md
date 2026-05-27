# Manual Operativo DAW: Ecosistema INC v3.0

Este documento define el flujo de trabajo de alta fidelidad para el **DiseÃ±ador automÃ¡tico Divi5**. Cada pÃ¡gina debe seguir este proceso de 4 fases para garantizar autoridad, diseÃ±o premium y editabilidad total.

## Fase 0: El Briefing (Estrategia de DiseÃ±o)
*Inspirado en la inteligencia UI/UX Pro Max.*

Antes de generar cualquier bloque, el agente debe orquestar un **Briefing EstratÃ©gico** siguiendo estos pasos tÃ¡cticos:

1.  **ExtracciÃ³n de Contexto**: El agente debe leer el mapa del sitio (`brief-mapa.md` o archivos en `content_state/local/`) para entender cÃ³mo encaja la nueva pÃ¡gina en el ecosistema.
2.  **InvestigaciÃ³n TÃ©cnica (NATIVA: `UX_Engine`)**: El agente consulta internamente el motor de inteligencia absorbido:
    *   **AcciÃ³n**: El agente invoca el `UX_Engine` para obtener patrones de *Storytelling*, *Pricing* y *UX Guidelines* especÃ­ficos del sector educativo directamente desde la base de datos integrada en `inc/core/intelligence/db/`.
    *   **ExtracciÃ³n**: Se extraen obligatoriamente los patrones de conversiÃ³n y anti-patrones institucionales.
3.  **DefiniciÃ³n del ADN Visual**: Consultar el `architectural-manifesto.md` para seleccionar los tokens y presets que aplicarÃ¡n (ej. Presets `hero` y `card` para la oferta).
4.  **GeneraciÃ³n del Brief**: Crear un artefacto en `workspace/briefs/<slug>.md` con:
    - **Objetivo EstratÃ©gico**: (Ej. Convertir prospectos en citas informativas).
    - **Mapa de Componentes**: Lista secuencial de lo que se construirÃ¡.
    - **Copia Maestra (Copywriting)**: TÃ­tulos y textos clave con tono institucional.

## Fase 1: La Arquitectura (El Arquitecto)
*Responsable: `Page_Brain.php`*

1.  **TraducciÃ³n de Brief**: El Cerebro toma el `brief.md` y selecciona el blueprint adecuado (Landing, Service, History).
2.  **ComposiciÃ³n SemÃ¡ntica**: Define el orden de las secciones y el contenido textual basado en la jerarquÃ­a institucional.
3.  **Salida**: Un esquema JSON estructurado con tipos de mÃ³dulos nativos de Divi 5.

## Fase 2: El DiseÃ±o (El DiseÃ±ador)
*Responsable: `AI_Bridge.php` + `Layout_Engine.php`*

1.  **ResoluciÃ³n de Estilo**: El `AI_Bridge` traduce la intenciÃ³n del brief en **Tokens de DiseÃ±o** especÃ­ficos.
2.  **InyecciÃ³n de Presets**: El `Layout_Engine` aplica los presets institucionales (`hero`, `card`, `glass`) inyectando valores reales (padding, hex, border-radius) en los atributos de decoraciÃ³n.
3.  **InyecciÃ³n Nativa**: Se asegura de que cada valor sea visible y editable en el Visual Builder de Divi.

## Fase 3: EjecuciÃ³n e IngenierÃ­a (El Ingeniero)
*Responsable: CLI + `manage_content.php`*

1.  **Despliegue Local**: Ejecutar el comando de generaciÃ³n, **pasando el brief** para que el cerebro lo use como contexto:
    ```powershell
    .\wp.bat agentic generate --prompt="Admisiones 2026 con hero, proceso, costos y FAQ" --title="Admisiones" --slug="admisiones" --brief="workspace/briefs/admisiones.md" --deploy
    ```
2.  **Snapshot de Estado**: Registrar el cambio en el ecosistema local para permitir futuras ediciones o despliegues remotos:
    ```powershell
    .\php.bat workspace\automation\manage_content.php --mode=local
    ```
3.  **Despliegue a ProducciÃ³n (Opcional)**: Usar el protocolo Hex-Safe detallado en `AGENTS.md` para inyectar el contenido en SiteGround.

---

## Reglas CrÃ­ticas para la Excelencia
- **Brief Primero**: Nunca generar una pÃ¡gina sin haber analizado el Brief previo.
- **Zero Emojis**: Usar siempre iconos de Tabler/SVG.
- **Editabilidad Total**: Si el diseÃ±ador grÃ¡fico no puede editar un margen desde el panel de Divi, el agente ha fallado.
- **Consistencia de Tokens**: Siempre usar `{{token:name}}` para permitir cambios globales.
