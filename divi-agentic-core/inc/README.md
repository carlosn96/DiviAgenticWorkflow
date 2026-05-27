# Ecosistema INC v3.0: Arquitecto Institucional AutÃ³nomo

Bienvenido al nÃºcleo de automatizaciÃ³n de alta fidelidad para el **Instituto RamÃ³n LÃ³pez Velarde**. Este ecosistema unifica la inteligencia del DAW (Divi Agentic Workflow) con un motor de ejecuciÃ³n nativo para Divi 5.

## ðï¸ Arquitectura del Sistema

El framework estÃ¡ diseÃ±ado para ser autosuficiente y opera bajo una estructura de carga unificada:

- **`inc/loader.php`**: El Director. Gestiona la carga automÃ¡tica de todas las clases del sistema.
- **`inc/core/`**: El MÃºsculo. Contiene los motores de Layout, Customizer, Inteligencia (Brain) y ComunicaciÃ³n (AI Bridge).
- **`inc/cli/`**: La Interfaz. Comandos WP-CLI para la operaciÃ³n diaria.
- **`inc/docs/`**: El Conocimiento. DocumentaciÃ³n exhaustiva para agentes e ingenieros.

## ð GuÃ­a de Inicio RÃ¡pido

### 1. GeneraciÃ³n de PÃ¡ginas
Para crear una pÃ¡gina desde un prompt humano con inyecciÃ³n nativa:
```powershell
.\wp.bat agentic generate --prompt="PÃ¡gina de Bachillerato con hero y tabla de costos" --title="Bachillerato" --slug="bachillerato" --deploy
```

### 2. AplicaciÃ³n de Identidad (Branding)
Para inyectar el ADN de marca desde un archivo de diseÃ±o:
```powershell
.\wp.bat agentic theme_apply ./workspace/design/identidad-corporativa.md
```

## ð DocumentaciÃ³n Maestra (Sin AmbigÃ¼edades)

Para operar el sistema con Ã©xito, consulta estos dos pilares:

1.  **[Manual Operativo DAW](inc/docs/workflow.md)**: El proceso paso a paso desde el prompt hasta la persistencia en producciÃ³n. **Lectura obligatoria para nuevos agentes.**
2.  **[Manifiesto ArquitectÃ³nico y CatÃ¡logo](inc/docs/architectural-manifesto.md)**: El estÃ¡ndar de diseÃ±o, tokens disponibles y el diccionario tÃ©cnico de componentes (Presets).

---
*Nota: Este sistema reemplaza y absorbe todas las capacidades del antiguo framework DAC. No se requieren dependencias externas para la construcciÃ³n del sitio.*
