# Ecosistema INC v3.0: Arquitecto Institucional Autónomo

Este ecosistema unifica la inteligencia del DAW (Divi Agentic Workflow) con un motor de ejecución nativo para Divi 5.

## 🏗️ Arquitectura del Sistema

El framework está diseñado para ser autosuficiente y opera bajo una estructura de carga unificada:

- **`inc/loader.php`**: El Director. Gestiona la carga automática de todas las clases del sistema.
- **`inc/core/`**: El Músculo. Contiene los motores de Layout, Customizer, Inteligencia (Brain) y Comunicación (AI Bridge).
- **`inc/cli/`**: La Interfaz. Comandos WP-CLI para la operación diaria.
- **`inc/docs/`**: El Conocimiento. Documentación exhaustiva para agentes e ingenieros.

## 🚀 Guía de Inicio Rápido

### 1. Generación de Páginas
Para crear una página desde un prompt humano con inyección nativa:
```powershell
.\wp.bat agentic generate --prompt="Página de Bachillerato con hero y tabla de costos" --title="Bachillerato" --slug="bachillerato" --deploy
```

### 2. Aplicación de Identidad (Branding)
Para inyectar el ADN de marca desde un archivo de diseño:
```powershell
.\wp.bat agentic theme_apply ./workspace/design/identidad-corporativa.md
```

## 📚 Documentación Maestra (Sin Ambigüedades)

Para operar el sistema con éxito, consulta estos dos pilares:

1.  **[Manual Operativo DAW](../inc/docs/workflow.md)**: El proceso paso a paso desde el prompt hasta la persistencia en producción. **Lectura obligatoria para nuevos agentes.**
2.  **[Manifiesto Arquitectónico y Catálogo](../inc/docs/architectural-manifesto.md)**: El estándar de diseño, tokens disponibles y el diccionario técnico de componentes (Presets).

---
*Nota: Este sistema reemplaza y absorbe todas las capacidades del antiguo framework DAC. No se requieren dependencias externas para la construcción del sitio.*
