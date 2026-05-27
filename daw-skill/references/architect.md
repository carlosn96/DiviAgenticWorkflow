# DAW Module: Phase 1 — Semantic Analysis (The Architect)

## Objective
Understand the business requirement and output a structured list of semantic components without technical implementation details.

## Instructions
1.  **Contextualize**: Identify the site identity (Institutional/Premium).
2.  **Deconstruct**: Break the user request into logical sections.
3.  **Semantic Plan**: Create a JSON structure following this example:
    ```json
    {
      "page_goal": "Lead generation for admissions",
      "sections": [
        {
          "name": "Hero",
          "intent": "Visual impact and primary CTA",
          "elements": ["Background Image", "Main Headline", "Lead Text", "Primary Button"]
        },
        {
          "name": "Stats",
          "intent": "Build trust through data",
          "elements": ["Grid of 4 statistics", "Trust badges"]
        }
      ]
    }
    ```
4.  **Handoff**: Pass this JSON to the **Design Lead** (Phase 2) para investigación y validación de diseño, quien luego lo pasará al Diseñador (Phase 3).

## Pro-Tips
- Don't think about Divi modules yet.
- Focus on the "Why" and the "What".
- Ensure the tone matches the project's brand guidelines.
