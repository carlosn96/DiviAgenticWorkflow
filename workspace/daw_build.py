"""
DAW Build Orchestrator — brand + design + page → deploy

Usage:
    # First time (creates brand + design system)
    python daw_build.py --name "Aletheia" --accent "#CA8A04"

    # Every page after that (auto-detects site from .env)
    python daw_build.py --prompt "pagina de instalaciones"

    # Different site
    python daw_build.py --site otra-marca --prompt "home"
"""

import os, sys, json, subprocess, argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DAW_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, DAW_ROOT)

from daw.cfg import load_daw_site  # noqa: E402


def load_env_site():
    """Read DAW_SITE from env or .env (delegates to daw.cfg)."""
    try:
        return load_daw_site()
    except Exception:
        return os.environ.get('DAW_SITE', '')


def brand_files_exist(site_dir: str) -> bool:
    brand_dir = os.path.join(site_dir, 'brand')
    return os.path.exists(os.path.join(brand_dir, '_design_vars.json')) and \
           os.path.exists(os.path.join(brand_dir, '_design_presets.json'))


def design_system_needs_rebuild(vars_path: str, presets_path: str, ds_path: str,
                                 force: bool = False) -> bool:
    """Check if design system is stale or missing.

    Rebuild triggers:
      - divitheme.json doesn't exist
      - _design_vars.json is newer than divitheme.json
      - _design_presets.json is newer than divitheme.json
      - --force-design-system flag passed
    """
    if force:
        return True
    if not os.path.exists(ds_path):
        return True
    ds_mtime = os.path.getmtime(ds_path)
    if os.path.exists(vars_path) and os.path.getmtime(vars_path) > ds_mtime:
        return True
    if os.path.exists(presets_path) and os.path.getmtime(presets_path) > ds_mtime:
        return True
    return False


def generate_brand(site: str, name: str, accent: str, tone: str = None,
                   description: str = "", fonts: dict = None) -> bool:
    """Run brand_generator.py inline or as subprocess."""
    generator_path = os.path.join(DAW_ROOT, 'workspace', 'brand_generator.py')
    if not os.path.exists(generator_path):
        print(f"[ERROR] brand_generator.py not found at {generator_path}")
        return False

    cmd = [
        sys.executable, generator_path,
        '--site', site,
        '--name', name,
        '--accent', accent,
        '--yes'
    ]
    if tone:
        cmd.extend(['--tone', tone])
    if description:
        cmd.extend(['--description', description])
    if fonts and fonts.get('display'):
        cmd.extend(['--font-display', fonts['display']])
    if fonts and fonts.get('body'):
        cmd.extend(['--font-body', fonts['body']])

    env = os.environ.copy()
    env['DAW_SITE'] = site

    result = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8")
    if result.returncode != 0:
        print(f"[ERROR] Brand generation failed:\n{result.stderr}")
        return False
    print(result.stdout)
    return True


def build_design_system(site: str, vars_path: str, presets_path: str,
                        out_path: str = None) -> bool:
    """Run build_design_system.py with explicit paths."""
    builder_path = os.path.join(DAW_ROOT, 'workspace', 'build_design_system.py')
    if not os.path.exists(builder_path):
        print(f"[ERROR] build_design_system.py not found at {builder_path}")
        return False

    cmd = [
        sys.executable, builder_path,
        '--vars', vars_path,
        '--presets', presets_path,
        '--quiet'
    ]
    if out_path:
        cmd.extend(['--out', out_path])

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"[ERROR] Design system build failed:\n{result.stderr}")
        return False
    # Print only key lines
    for line in result.stdout.split('\n'):
        if any(k in line for k in ('OK', 'STRATEGY', 'PALETTE', 'PRESETS', 'VALIDATE')):
            print(line)
    return True


def generate_brief(site: str, prompt: str) -> str:
    """Generate brief.json via UX-Pro deterministic engine (incl. design_direction)."""
    site_dir = os.path.join(DAW_ROOT, 'site', site)
    briefs_dir = os.path.join(site_dir, 'briefs')
    os.makedirs(briefs_dir, exist_ok=True)

    slug = prompt.lower().replace(' ', '-').replace('á', 'a').replace('é', 'e')[:30]
    brief_path = os.path.join(briefs_dir, f"{slug}.json")

    brief_script = os.path.join(DAW_ROOT, 'workspace', 'automation', 'ux_pro_brief_generator.py')
    if not os.path.exists(brief_script):
        print(f"[WARN] ux_pro_brief_generator.py not found")
        return ""

    env = os.environ.copy()
    env['DAW_SITE'] = site

    cmd = [sys.executable, brief_script, '--query', prompt, '--out', brief_path]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8")
    if result.returncode != 0:
        print(f"[WARN] Brief generation failed:\n{result.stderr}")
        return ""

    print(f"Brief: {brief_path}")
    return brief_path


def run_vie(brief_path: str, site: str) -> str:
    """Run Visual Impact Engine (v3.0 — vie/ package) to produce rich page-def.

    Replaces the legacy subprocess call to ml-dataset/artifacts/visual_impact_engine.py
    with a direct Python function call to vie.factory.create_vie(). This uses the new
    architecture (vie/ package) instead of the monolith shim.
    """
    plans_dir = os.path.join(DAW_ROOT, 'site', site, 'plans')
    os.makedirs(plans_dir, exist_ok=True)
    slug = os.path.splitext(os.path.basename(brief_path))[0]
    plan_path = os.path.join(plans_dir, f"{slug}.json")

    # Resolve design-system path
    design_system_path = os.path.join(DAW_ROOT, 'site', site, 'design-system', 'divitheme.json')
    if not os.path.exists(design_system_path):
        print(f"[WARN] Design system not found: {design_system_path}")
        return run_die(brief_path, site)

    try:
        # Bootstrap sys.path so vie/ is importable from daw_build.py
        if DAW_ROOT not in sys.path:
            sys.path.insert(0, DAW_ROOT)
        if os.path.join(DAW_ROOT, 'workspace') not in sys.path:
            sys.path.insert(0, os.path.join(DAW_ROOT, 'workspace'))

        import json
        from vie.factory import create_vie

        with open(brief_path, 'r', encoding='utf-8') as f:
            brief = json.load(f)
        with open(design_system_path, 'r', encoding='utf-8') as f:
            design_system = json.load(f)

        engine = create_vie(design_system)
        page_def = engine.translate_brief(brief)

        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(page_def, f, indent=2, ensure_ascii=False)

        print(f"[OK] Rich plan generated (vie/): {plan_path}")
        return plan_path
    except Exception as e:
        print(f"[WARN] VIE failed: {e}")
        return ""


def deploy_page(plan_path: str, site: str) -> bool:
    """Deploy via build_page.php."""
    php_bat = os.path.join(DAW_ROOT, 'php.bat')
    build_script = os.path.join(DAW_ROOT, 'divi-agentic-core', 'bin', 'build_page.php')

    if not os.path.exists(build_script):
        print(f"[WARN] build_page.php not found — skipping deploy")
        return False

    # Pass DAW_SITE so build_page.php knows the correct site
    env = os.environ.copy()
    env['DAW_SITE'] = site
    cmd = f'"{php_bat}" "{build_script}" --def="{plan_path}" --deploy'
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, env=env, encoding="utf-8")
    if result.returncode != 0:
        print(f"[WARN] Deploy failed:\n{result.stderr}")
        return False

    print(f"[OK] Page deployed successfully")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='DAW Build Orchestrator — brand + design + page → deploy',
    )
    parser.add_argument('--site', '-s', type=str, default=None,
                        help='Site name (defaults to DAW_SITE from .env)')
    parser.add_argument('--name', '-n', type=str,
                        help='Brand name (only needed first time)')
    parser.add_argument('--accent', '-a', type=str,
                        help='Accent color hex (only needed first time)')
    parser.add_argument('--tone', '-t', type=str, choices=['luxury', 'tech', 'organic', 'minimal'],
                        default='luxury', help='Brand tone (default: luxury)')
    parser.add_argument('--prompt', '-p', type=str,
                        help='Page prompt. If given, runs full pipeline: brief → VIE → deploy')
    args = parser.parse_args()

    site = args.site or load_env_site()
    if not site:
        print("[ERROR] DAW_SITE not defined. Set in .env or pass --site")
        sys.exit(1)

    site_dir = os.path.join(DAW_ROOT, 'site', site)
    brand_dir = os.path.join(site_dir, 'brand')
    ds_dir = os.path.join(site_dir, 'design-system')
    vars_path = os.path.join(brand_dir, '_design_vars.json')
    presets_path = os.path.join(brand_dir, '_design_presets.json')
    ds_path = os.path.join(ds_dir, 'divitheme.json')

    os.makedirs(brand_dir, exist_ok=True)
    os.makedirs(ds_dir, exist_ok=True)

    print(f"Site: {site}")

    # ── Brand files (one-shot, only if missing) ─────────────────────────
    if not brand_files_exist(site_dir):
        if not args.name or not args.accent:
            print("[ERROR] Brand files missing. Provide --name and --accent to generate")
            sys.exit(1)
        print(f"Generating brand files...")
        ok = generate_brand(site=site, name=args.name, accent=args.accent, tone=args.tone)
        if not ok:
            sys.exit(1)

    # ── Design system (auto-build if stale) ─────────────────────────────
    if design_system_needs_rebuild(vars_path, presets_path, ds_path):
        print(f"Building design system...")
        ok = build_design_system(site, vars_path, presets_path, ds_path)
        if not ok:
            sys.exit(1)
        print(f"Design system ready: {ds_path}")

    # ── Page pipeline (only if --prompt given) ──────────────────────────
    if not args.prompt:
        print("Done. Pass --prompt to generate a page.")
        return

    print(f"Full pipeline: brief → VIE → deploy")
    brief_path = generate_brief(site, args.prompt)
    if not brief_path:
        sys.exit(1)

    plan_path = run_vie(brief_path, site)
    if not plan_path:
        sys.exit(1)

    deploy_page(plan_path, site)
    print("Done.")


if __name__ == '__main__':
    main()
