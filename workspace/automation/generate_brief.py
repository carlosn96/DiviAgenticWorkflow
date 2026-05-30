#!/usr/bin/env python3
"""
================================================================================
generate_brief.py — Generador de Briefs de Diseño Inteligente y Dinámico
================================================================================
Este script traduce solicitudes en lenguaje natural a archivos de brief YAML
estructurados, compatibles con el orquestador DAW (orchestrate_page.php).

Diseñado para ser ultra robusto, económico y libre de dependencias externas.

--------------------------------------------------------------------------------
1. Características Principales:
--------------------------------------------------------------------------------
- **Estrategia de Fallback en Cadena**: Intenta consumir las API Keys configuradas
  en el .env de forma secuencial si alguna de ellas falla por red o DNS.
- **Bypass de Bloqueos Cloudflare**: Envía User-Agent de navegador para evitar
  errores 403 Forbidden (error 1010) comunes en proveedores como Groq.
- **Auto-Mapeo de Modelos Deprecados**: Traduce modelos obsoletos (como
  llama3-8b-8192 de Groq) a sus sucesores activos (como llama-3.1-8b-instant).
- **Modo Interactivo**: Si no se proporciona el argumento `--prompt`, el script
  se ejecutará en modo interactivo solicitando al usuario que escriba su prompt.
- **Limpieza de Preámbulo de IA**: Limpia el output eliminando explicaciones
  conversacionales previas y posteriores al bloque YAML.

--------------------------------------------------------------------------------
2. Variables de Entorno Soportadas (.env):
--------------------------------------------------------------------------------
El script busca automáticamente credenciales en el siguiente orden de costo:
  1. DEEPSEEK_API_KEY   -> deepseek-chat
  2. GEMINI_API_KEY     -> gemini-2.5-flash
  3. OPENAI_API_KEY     -> gpt-4o-mini
    4. NVIDIA_API_KEY     -> qwen/qwen3-coder-480b-a35b-instruct via OpenAI SDK
    5. OPENROUTER_API_KEY -> openai/gpt-4o-mini (auto-mapea prefijos)
    6. ANTHROPIC_API_KEY  -> claude-3-5-haiku (evita Opus/Sonnet para ahorrar)
    7. GROQ_API_KEY       -> llama-3.3-70b-versatile
    8. LLM_API_KEY / URL  -> Endpoint genérico compatible con OpenAI (Ollama, etc.)

--------------------------------------------------------------------------------
3. Argumentos de Línea de Comandos:
--------------------------------------------------------------------------------
    --query "texto"       Query/brief inicial que el modelo optimiza internamente antes de generar el YAML final
    --prompt "texto"      Alias compatible de --query
  --out "archivo"       Nombre del archivo de salida (slug)
  --provider "nombre"   Fuerza un proveedor específico (groq, gemini, etc.)
  --model "modelo"      Fuerza un modelo específico
  --tone "tono"         Fuerza el tono estético (modern, editorial, premium...)
  --verbose             Muestra detalles completos del payload y response HTTP

--------------------------------------------------------------------------------
4. Ejemplos de Uso:
--------------------------------------------------------------------------------
- Modo Interactivo Simple:
    python DAW_bundle/workspace/automation/generate_brief.py

- Prompt Directo con Tono y Depuración:
    python DAW_bundle/workspace/automation/generate_brief.py \\
      --prompt "hazme una pagina de servicios de tecnologia" \\
      --tone premium \\
      --verbose
================================================================================
"""
import os
import sys
import json
import urllib.request
import urllib.error
import argparse
import re
from pathlib import Path

# Setup paths
SCRIPT_DIR = Path(__file__).parent.resolve()
DAW_ROOT = SCRIPT_DIR.parent.parent
ENV_PATH = DAW_ROOT / ".env"
if not ENV_PATH.exists() and DAW_ROOT.parent.joinpath(".env").exists():
    ENV_PATH = DAW_ROOT.parent / ".env"

def get_briefs_dir():
    site_name = os.environ.get('DAW_SITE') or 'bibliotheca'
    return DAW_ROOT / "site" / site_name / "briefs"

def get_brand_vars():
    site_name = os.environ.get('DAW_SITE') or 'bibliotheca'
    vars_path = DAW_ROOT / "site" / site_name / "brand" / "_design_vars.json"
    if vars_path.exists():
        try:
            with open(vars_path, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def load_section_schema():
    schema_path = SCRIPT_DIR.parent / "section-schema.json"
    if schema_path.exists():
        try:
            with open(schema_path, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def build_schema_prompt(schema: dict) -> str:
    lines = []
    for st, entry in schema.items():
        lines.append(f"  '{st}' ({entry['template']}):")
        section_f = entry.get('section_fields') or entry.get('slots', [])
        item_f = entry.get('item_fields') or {}
        sfields = [f for f in section_f if not any(f in v for v in item_f.values())]
        if sfields:
            lines.append(f"    fields: {', '.join(sorted(set(sfields)))}")
        for src, fields in item_f.items():
            lines.append(f"    items ({src}): each with {', '.join(fields)}")
        if entry.get('variants'):
            vnames = ', '.join(entry['variants'].keys())
            lines.append(f"    variants: {vnames}")
    return '\n'.join(lines)

def normalize_yaml_structure(raw: str) -> str:
    """Ensure the YAML follows the expected single-document sections[] format.
    Handles multi-document YAML (--- separated) by merging into sections: list."""
    lines = raw.strip().split('\n')
    
    # Phase 1: Strip markdown fences
    cleaned = []
    in_fence = False
    for line in lines:
        if line.strip().startswith('```'):
            in_fence = not in_fence
            continue
        if not in_fence:
            cleaned.append(line)
    lines = cleaned
    
    # Phase 2: Detect if already has sections: key
    has_sections = any(re.match(r'^\s*sections:', l) for l in lines)
    if has_sections:
        return '\n'.join(lines)
    
    # Phase 3: Split by --- to detect multi-document YAML
    docs = []
    current = []
    for line in lines:
        if line.strip() == '---':
            if current:
                docs.append(current)
                current = []
        else:
            current.append(line)
    if current:
        docs.append(current)
    
    if len(docs) <= 1:
        return '\n'.join(lines)
    
    # Phase 4: First doc = page metadata, rest = sections
    first = '\n'.join(docs[0])
    section_docs = ['\n'.join(d) for d in docs[1:]]
    
    # Extract page-level keys from first doc
    page_keys = []
    section_keys = []
    for line in docs[0]:
        if re.match(r'^(title|slug|description|tone|language|locale):', line):
            page_keys.append(line)
        elif re.match(r'^\s*(section_type|sections|eyebrow|text|btn_|features|items|testimonials|stats|logos|media|decorative|body):', line):
            section_keys.append(line)
    
    # Build page metadata
    result_lines = page_keys.copy()
    if not any('slug:' in l for l in result_lines):
        result_lines.insert(0, 'slug: page')
    
    # Append section docs as sections: list items
    result_lines.append('sections:')
    for sd in section_docs:
        result_lines.append('  - section_type: auto')
        for line in sd.split('\n'):
            if re.match(r'^\s*(section_type|tone|language):', line):
                continue
            result_lines.append(f'    {line.strip()}')
    
    return '\n'.join(result_lines)

def build_system_prompt(brand_vars, section_schema):
    brand_name = brand_vars.get('brand_name', 'Nueva Marca')
    brand_desc = brand_vars.get('brand_description', 'Un proyecto premium')
    schema_guide = build_schema_prompt(section_schema) if section_schema else "(no schema available)"
    return f"""You are the Lead Content Architect for '{brand_name}' ({brand_desc}).
Generate a design brief in YAML. Work in a single pass: first, internally rewrite the user query into a richer, clearer, more specific design prompt; then use that improved prompt to generate the final brief. Do not output the rewritten prompt. Return STRICTLY VALID YAML only.

SECTION TYPES — use the EXACT value after "section_type:" below. Do NOT invent other values:

section_type: "hero"     (template: hero-split, split 1_2,1_2 layout)
  fields: eyebrow, title, text, btn_primary_text, btn_primary_url
  optional: btn_secondary_text, btn_secondary_url

section_type: "hero-centered"     (template: hero-centered, centered layout)
  fields: eyebrow, title, text, btn_primary_text, btn_primary_url
  optional: btn_secondary_text, btn_secondary_url

section_type: "features"     (template: features-3col, 3-column grid)
  fields: eyebrow, title, text
  items (field: 'features'): each with title, icon, text

section_type: "content"     (template: content-split, text + media card)
  fields: eyebrow, title, text, body, btn_primary_text, btn_primary_url
  optional: media_icon, media_attribution

section_type: "content-list"     (template: content-split-icon-list, text + icon list)
  fields: eyebrow, title, text, body
  items (field: 'items'): each with title, icon

section_type: "stats"     (template: stats-4col, 4-column counter grid)
  items (field: 'stats'): each with number, label

section_type: "testimonials"     (template: testimonials-3col, 3-column grid)
  fields: eyebrow, title
  items (field: 'testimonials'): each with text, name, role
  optional per item: avatar

section_type: "logos"     (template: logos-4col, 4-column grid)
  fields: title, text
  items (field: 'logos'): each with icon, name

section_type: "cta"     (template: cta-centered, centered CTA)
  fields: eyebrow, title, text, btn_primary_text, btn_primary_url
  optional: btn_secondary_text, btn_secondary_url

VALID section_type values (use ONE of these EXACTLY): hero, hero-centered, features, content, content-list, stats, testimonials, logos, cta

OUTPUT FORMAT:
title: <Page Title>
slug: <page-slug>
tone: <editorial|modern|premium|minimal|dramatic|playful>
description: <Brief description>
sections:
  - section_type: hero      # ← use EXACT one-word value from the list above
    eyebrow: <Uppercase kicker>
    title: <Section heading>
    text: <Description paragraph>
    body: <Long-form plain text>
    btn_primary_text: <Button label>
    btn_primary_url: <Button URL>
    features:   # only for section_type: features
      - title: <Item title>
        icon: <Divi unicode>
        text: <Item description>
    # or stats:, testimonials:, logos:, items: (same list pattern, use correct per-type fields listed above)

CRITICAL RULES:
- section_type MUST be one of: hero, hero-centered, features, content, content-list, stats, testimonials, logos, cta. NEVER invent other values.
- Use EXACTLY the field names listed above. NEVER use template names as section_type.
- Use 'body:' for body text. NEVER use 'body_text:', 'description:', or 'content:'.
- Icons use Divi unicode: &#xe000;-&#xf800; (e.g. &#xe03a;, &#xe065;, &#xe0bf;).
- Every repeat item MUST include ALL required fields for its type (e.g. stats need number AND label; features need title, icon, AND text).
- Do NOT use HTML tags, markdown, or inline formatting. Plain text only.
- Each section must have exactly ONE section_type key. No duplicate keys.
- Omit optional fields entirely instead of leaving them empty.
- Output ONLY raw YAML. No markdown fences, no code blocks, no explanations.

DYNAMIC SCHEMA (reference, use field names from above):
{schema_guide}
"""

def load_env(env_path):
    file_env = {}
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('export '):
                    line = line[len('export '):].lstrip()
                if '=' not in line:
                    continue
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip()
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                elif '#' in val:
                    val = val.split('#', 1)[0].rstrip()

                def _repl(match):
                    var = match.group(1) or match.group(2)
                    return file_env.get(var) or os.environ.get(var) or ''

                val = re.sub(r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)', _repl, val)
                file_env[key] = val

    merged = file_env.copy()
    merged.update(os.environ)
    return merged

def sanitize_slug(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text

def make_request(url, headers, payload, verbose=False):
    # Copy headers and add standard browser User-Agent to bypass Cloudflare 403 blocks (error code 1010)
    req_headers = headers.copy() if headers else {}
    if "User-Agent" not in req_headers:
        req_headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=req_headers, method='POST')
    
    if verbose:
        print(f"\n[VERBOSE DEBUG] API Request details:")
        print(f"URL: {url}")
        print(f"Headers: {json.dumps(req_headers, indent=2)}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_body = response.read().decode('utf-8')
            if verbose:
                print(f"[VERBOSE DEBUG] Response Status: {response.status}")
                print(f"[VERBOSE DEBUG] Response Body: {res_body}\n")
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"API HTTP Error: {e.code} - {err_body}", file=sys.stderr)
        raise e
    except Exception as e:
        print(f"Network Connection Error: {e}", file=sys.stderr)
        raise e

def _extract_openai_message_content(completion):
    choices = getattr(completion, "choices", None) or []
    if not choices:
        return str(completion)

    message = getattr(choices[0], "message", None)
    if message is None:
        return str(choices[0])

    content = getattr(message, "content", None)
    if content:
        return content

    return str(message)

class LLMProviderStrategy:
    def __init__(self, api_key, api_url, model):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model

    def generate(self, system_prompt, user_prompt, verbose=False):
        raise NotImplementedError

class OpenAIStyleProvider(LLMProviderStrategy):
    def generate(self, system_prompt, user_prompt, verbose=False):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }
        res = make_request(self.api_url, headers, payload, verbose)
        if isinstance(res, dict) and res.get("choices"):
            choice = res["choices"][0]
            if isinstance(choice.get("message"), dict):
                return choice["message"]["content"]
            if choice.get("text"):
                return choice["text"]
        return str(res)

class OpenAISDKProvider(LLMProviderStrategy):
    def __init__(self, api_key, api_url, model, temperature=0.7, top_p=0.8, max_tokens=4096, stream=False):
        super().__init__(api_key, api_url, model)
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.stream = stream

    def generate(self, system_prompt, user_prompt, verbose=False):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("The 'openai' package is required for this provider. Install it with 'pip install openai'.") from exc

        base_url = self.api_url
        if base_url.endswith("/chat/completions"):
            base_url = base_url.rsplit("/chat/completions", 1)[0]

        client = OpenAI(base_url=base_url, api_key=self.api_key)
        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            stream=self.stream,
        )

        if verbose:
            print("\n[VERBOSE DEBUG] OpenAI SDK response received")

        return _extract_openai_message_content(completion)

class AnthropicProvider(LLMProviderStrategy):
    def generate(self, system_prompt, user_prompt, verbose=False):
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        payload = {
            "model": self.model,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 4000,
            "temperature": 0.2
        }
        res = make_request(self.api_url, headers, payload, verbose)
        return res["content"][0]["text"]

class GeminiProvider(LLMProviderStrategy):
    def generate(self, system_prompt, user_prompt, verbose=False):
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"System Instructions:\n{system_prompt}\n\nUser Request: {user_prompt}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2
            }
        }
        url = self.api_url.format(model=self.model, key=self.api_key) if "{model}" in self.api_url else self.api_url
        res = make_request(url, headers, payload, verbose)
        return res["candidates"][0]["content"]["parts"][0]["text"]

PROVIDER_REGISTRY = [
    {
        "name": "deepseek",
        "prefix": "DEEPSEEK",
        "model": "deepseek-chat",
        "url": "https://api.deepseek.com/chat/completions",
        "cls": OpenAIStyleProvider
    },
    {
        "name": "gemini",
        "prefix": "GEMINI",
        "model": "gemini-2.5-flash",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        "cls": GeminiProvider
    },
    {
        "name": "openai",
        "prefix": "OPENAI",
        "model": "gpt-4o-mini",
        "url": "https://api.openai.com/v1/chat/completions",
        "cls": OpenAIStyleProvider
    },
    {
        "name": "nvidia",
        "prefix": "NVIDIA",
        "model": "qwen/qwen3-coder-480b-a35b-instruct",
        "url": "https://integrate.api.nvidia.com/v1",
        "cls": OpenAISDKProvider
    },
    {
        "name": "openrouter",
        "prefix": "OPENROUTER",
        "model": "gpt-4o-mini",
        "url": "https://api.openrouter.ai/v1/chat/completions",
        "cls": OpenAIStyleProvider
    },
    {
        "name": "anthropic",
        "prefix": "ANTHROPIC",
        "model": "claude-3-5-haiku",
        "url": "https://api.anthropic.com/v1/messages",
        "cls": AnthropicProvider
    },
    {
        "name": "groq",
        "prefix": "GROQ",
        "model": "llama-3.3-70b-versatile",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "cls": OpenAIStyleProvider
    }
]

class ProviderFactory:
    @staticmethod
    def resolve_all(env, force_provider=None, force_model=None):
        global_key = env.get("LLM_API_KEY")
        global_url = env.get("LLM_API_URL")
        global_model = env.get("LLM_MODEL")

        resolved = []
        for cfg in PROVIDER_REGISTRY:
            name = cfg["name"]
            if force_provider and force_provider.lower() != name:
                continue

            prefix = cfg["prefix"]
            key = global_key or env.get(f"{prefix}_API_KEY")
            if not key:
                continue

            url = global_url or env.get(f"{prefix}_API_URL") or cfg["url"]
            model = force_model or global_model or env.get(f"{prefix}_MODEL") or cfg["model"]

            # Groq decommissioned models mapping
            if name == "groq":
                if model == "llama3-8b-8192":
                    model = "llama-3.1-8b-instant"
                elif model == "llama3-70b-8192":
                    model = "llama-3.3-70b-versatile"

            # OpenRouter model mapping to ensure standard models are correctly prefixed
            if name == "openrouter" and "/" not in model:
                if model.startswith("gpt-"):
                    model = f"openai/{model}"
                elif model.startswith("claude-"):
                    model = f"anthropic/{model}"
                elif model.startswith("gemini-"):
                    model = f"google/{model}"
                elif model.startswith("llama"):
                    model = f"meta-llama/{model}"
                elif model.startswith("deepseek-"):
                    model = f"deepseek/{model}"

            resolved.append((name, cfg["cls"](key, url, model)))

        if not resolved and global_key and global_url and (global_model or force_model):
            model = force_model or global_model
            resolved.append(("generic", OpenAIStyleProvider(global_key, global_url, model)))

        return resolved

def generate_brief_yaml(prompt, provider, system_prompt, tone=None, verbose=False):
    tone_instruction = f"\nFuerza a que el campo `tone` en el archivo YAML sea exactamente: {tone}." if tone else ""
    user_prompt = (
        "Toma este query inicial y conviértelo mentalmente en un prompt de alto nivel más claro, completo y útil para diseño. "
        "Después genera directamente el brief YAML final usando ese prompt mejorado. No muestres el prompt intermedio ni expliques tu proceso. "
        "Construye una estructura coherente y estrictamente válida, con una sola clave `section_type` por sección y sin duplicar campos. "
        "Usa únicamente los nombres de campo exactos indicados en el prompt de sistema. Para párrafos largos usa `body`, nunca inventes campos nuevos.\n\n"
        f"Query inicial: {prompt}\n"
        f"{tone_instruction}\n"
        "Recuerda devolver únicamente el archivo YAML limpio, respetando el esquema e indicaciones del prompt de sistema. "
        "Si una idea puede expresarse con menos claves, prioriza la validez del YAML y la claridad del brief."
    )
    return provider.generate(system_prompt, user_prompt, verbose=verbose)

def clean_yaml_output(yaml_content):
    # Try to extract content between code blocks
    if "```yaml" in yaml_content:
        yaml_content = yaml_content.split("```yaml", 1)[1]
        if "```" in yaml_content:
            yaml_content = yaml_content.split("```", 1)[0]
    elif "```" in yaml_content:
        yaml_content = yaml_content.split("```", 1)[1]
        if "```" in yaml_content:
            yaml_content = yaml_content.split("```", 1)[0]
            
    lines = yaml_content.strip().split('\n')
    cleaned_lines = []
    started = False
    
    # Common YAML keys for our schema to detect start of YAML
    start_keys = ["title:", "slug:", "tone:", "description:", "sections:"]
    
    for line in lines:
        stripped = line.strip()
        # Detect the first key of the YAML document to drop conversational preambles
        if not started:
            if any(stripped.startswith(k) for k in start_keys):
                started = True
        
        if started:
            # Drop markdown closing code blocks if any got missed
            if stripped.startswith("```"):
                break
            cleaned_lines.append(line)
            
    if not cleaned_lines:
        # Fallback to stripped content if start keys detection failed
        return yaml_content.strip()
        
    return "\n".join(cleaned_lines).strip()

def strip_html_from_yaml(yaml_content):
    """Remove obvious HTML tags from YAML scalar lines while keeping indentation."""
    cleaned_lines = []
    for line in yaml_content.splitlines():
        if not line.strip():
            cleaned_lines.append(line)
            continue

        if line.lstrip().startswith("#"):
            cleaned_lines.append(line)
            continue

        prefix_match = re.match(r'^(\s*[^:]+:\s*)(.*)$', line)
        if prefix_match:
            prefix, value = prefix_match.groups()
            value = re.sub(r'<\/?(?:[A-Za-z][A-Za-z0-9:-]*)(?:\s+[^<>]*)?>', '', value)
            value = re.sub(r'\s+', ' ', value).strip()
            cleaned_lines.append(f"{prefix}{value}" if value else prefix.rstrip())
            continue

        cleaned_lines.append(re.sub(r'<\/?(?:[A-Za-z][A-Za-z0-9:-]*)(?:\s+[^<>]*)?>', '', line))

    return "\n".join(cleaned_lines).strip()

def validate_yaml_output(yaml_content):
    """Apply lightweight guardrails to keep the brief structurally clean."""
    yaml_content = re.sub(r'```(?:yaml)?', '', yaml_content)
    yaml_content = strip_html_from_yaml(yaml_content)
    yaml_content = re.sub(r'\n{3,}', '\n\n', yaml_content).strip()
    return yaml_content

def main():
    parser = argparse.ArgumentParser(description="Generate a brief YAML using a dynamic and cheap LLM.")
    parser.add_argument("--query", help="Initial query to refine internally before generating the brief (e.g. 'página de contacto')")
    parser.add_argument("--prompt", help="Alias compatible de --query")
    parser.add_argument("--out", help="Output filename (optional, e.g. 'contacto')")
    parser.add_argument("--provider", help="Force a specific provider (e.g. 'groq', 'openai', 'nvidia', 'gemini')")
    parser.add_argument("--model", help="Force a specific model name")
    parser.add_argument("--tone", help="Force a specific layout design tone (modern, editorial, premium, etc.)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose API request/response logs")
    
    args = parser.parse_args()
    
    prompt = args.query or args.prompt
    if not prompt:
        try:
            print("No se proporcionó --query/--prompt. Iniciando modo interactivo...")
            prompt = input("Ingresa el query inicial que deseas mejorar: ").strip()
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario.")
            return 1
            
    if not prompt:
        print("Error: El prompt no puede estar vacío.", file=sys.stderr)
        return 1
        
    # Load .env
    env = load_env(ENV_PATH)
    os.environ.update(env)
    
    # Resolve providers
    providers = ProviderFactory.resolve_all(env, force_provider=args.provider, force_model=args.model)
    if not providers:
        print("Error: No API keys found in .env or environment.", file=sys.stderr)
        print("Configure LLM_API_KEY or any provider-specific API key (e.g. GROQ_API_KEY, GEMINI_API_KEY, NVIDIA_API_KEY, etc.)", file=sys.stderr)
        return 1

    # Load brand identity and section schema
    brand_vars = get_brand_vars()
    section_schema = load_section_schema()
    system_prompt = build_system_prompt(brand_vars, section_schema)
    if 'brand_name' in brand_vars:
        print(f"[GENERATE] Brand: {brand_vars['brand_name']}")
    else:
        print("[GENERATE] No brand vars found — using generic system prompt")

    yaml_content = None
    last_error = None
    chosen_provider_name = None
    chosen_model = None
    
    # Iterate through all available providers until one works
    for name, provider in providers:
        try:
            print(f"[GENERATE] Attempting to call LLM via provider '{name}' using model '{provider.model}'...")
            yaml_content = generate_brief_yaml(prompt, provider, system_prompt, tone=args.tone, verbose=args.verbose)
            chosen_provider_name = name
            chosen_model = provider.model
            break  # Success!
        except Exception as e:
            print(f"Warning: Provider '{name}' failed: {e}", file=sys.stderr)
            last_error = e

    if not yaml_content:
        print(f"Error: All configured providers failed. Last error: {last_error}", file=sys.stderr)
        return 1
        
    # Clean the YAML content using robust cleanup rules
    yaml_content = clean_yaml_output(yaml_content)
    
    # Normalize multi-document YAML to single-document sections[] format
    yaml_content = normalize_yaml_structure(yaml_content)

    # Strip leftover HTML and normalize scalar text
    yaml_content = validate_yaml_output(yaml_content)
    
    # Override slug if --out was provided
    if args.out:
        forced_slug = sanitize_slug(args.out)
        yaml_content = re.sub(r'^slug:.*', f'slug: {forced_slug}', yaml_content, flags=re.MULTILINE)
    
    # Try to parse the slug from the YAML content
    slug = None
    slug_match = re.search(r'^slug:\s*(.*)', yaml_content, re.MULTILINE)
    if slug_match:
        slug = sanitize_slug(slug_match.group(1))
        
    if not slug:
        slug = "dynamic-brief"
    
    # Use dynamic brand-aware output directory
    briefs_dir = get_briefs_dir()
    out_path = briefs_dir / f"{slug}.yml"
    briefs_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
        
    print(f"[GENERATE] Success! Brief YAML generated and written to: {out_path}")
    print(f"[GENERATE] Provider: {chosen_provider_name} | Model: {chosen_model}")
    print(f"[GENERATE] Slug: {slug}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
