"""
DAW Build Orchestrator — Unified Brand + Design System Generator
=================================================================
Single command that:
  1. Generates brand files (_design_vars.json + _design_presets.json) if missing
  2. Builds enriched design system (divitheme.json) — ONE-SHOT, only rebuilds if stale
  3. Optionally continues to brief → DIE → deploy

Usage:
    # First time: create brand + design system (one-shot)
    python daw_build.py --site aletheia --name "Aletheia" --accent "#CA8A04"

    # After brand exists: just build a page
    python daw_build.py --site aletheia --full --prompt "home page"

    # Force rebuild design system (after editing brand files)
    python daw_build.py --site aletheia --force-design-system

    # Full pipeline from scratch
    python daw_build.py --site aletheia --name "Aletheia" --accent "#CA8A04" --full --prompt "home page"

Dependencies:
    pip install colour-science

One-shot artefacts:
    - _design_vars.json: brand variables (manual edits persist)
    - _design_presets.json: base presets (manual edits persist)
    - divitheme.json: compiled design system (auto-generated from above, do NOT edit)
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


def load_env_site():
    """Read DAW_SITE from .env in project root."""
    env_path = os.path.join(os.path.dirname(DAW_ROOT), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DAW_SITE='):
                    val = line[9:].strip().strip('"').strip("'")
                    if val:
                        return val
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


def generate_brief(site: str, prompt: str, tone: str = "editorial") -> str:
    """Generate brief.json. Returns path to brief file."""
    brief_script = os.path.join(DAW_ROOT, 'workspace', 'automation', 'generate_brief.py')
    if not os.path.exists(brief_script):
        print(f"[WARN] generate_brief.py not found — skipping brief generation")
        return ""

    site_dir = os.path.join(DAW_ROOT, 'site', site)
    briefs_dir = os.path.join(site_dir, 'briefs')
    os.makedirs(briefs_dir, exist_ok=True)

    # Generate slug from prompt
    slug = prompt.lower().replace(' ', '-').replace('á', 'a').replace('é', 'e')[:30]

    # Pass DAW_SITE to subprocess so generate_brief.py knows the correct site
    env = os.environ.copy()
    env['DAW_SITE'] = site

    cmd = [
        sys.executable, brief_script,
        '--prompt', prompt,
        '--tone', tone,
        '--out', slug,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8")
    if result.returncode != 0:
        print(f"[WARN] Brief generation failed:\n{result.stderr}")
        return ""

    brief_path = os.path.join(briefs_dir, f"{slug}.json")
    print(f"[OK] Brief generated: {brief_path}")
    return brief_path


def run_vie(brief_path: str, site: str) -> str:
    """Run Visual Impact Engine to produce rich page-def. Returns plan path."""
    vie_script = os.path.join(DAW_ROOT, 'ml-dataset', 'artifacts', 'visual_impact_engine.py')
    if not os.path.exists(vie_script):
        print(f"[WARN] visual_impact_engine.py not found — falling back to DIE")
        return run_die(brief_path, site)

    plans_dir = os.path.join(DAW_ROOT, 'site', site, 'plans')
    os.makedirs(plans_dir, exist_ok=True)
    slug = os.path.splitext(os.path.basename(brief_path))[0]
    plan_path = os.path.join(plans_dir, f"{slug}.json")

    cmd = [
        sys.executable, vie_script,
        '--brief-file', brief_path,
        '--site', site,
        '--output', plan_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"[WARN] VIE failed:\n{result.stderr}")
        return ""

    print(f"[OK] Rich plan generated (VIE): {plan_path}")
    return plan_path


def run_die(brief_path: str, site: str) -> str:
    """Run DIE to produce plan.json. Returns plan path."""
    die_script = os.path.join(DAW_ROOT, 'ml-dataset', 'artifacts', 'design_intelligence.py')
    if not os.path.exists(die_script):
        print(f"[WARN] design_intelligence.py not found — skipping DIE")
        return ""

    plans_dir = os.path.join(DAW_ROOT, 'site', site, 'plans')
    os.makedirs(plans_dir, exist_ok=True)
    slug = os.path.splitext(os.path.basename(brief_path))[0]
    plan_path = os.path.join(plans_dir, f"{slug}.json")

    cmd = [
        sys.executable, die_script,
        '--brief-file', brief_path,
        '--output', plan_path,
        '--skip-quality-gate'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"[WARN] DIE failed:\n{result.stderr}")
        return ""

    print(f"[OK] Plan generated: {plan_path}")
    return plan_path


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
        description='DAW Build Orchestrator — Unified brand + design system pipeline',
        epilog='''One-shot artefacts (do not regenerate unless changed):
  - divitheme.json: compiled design system (skip with --no-design-system)
  - _design_vars.json: brand variables (only regenerate with --regenerate)
  - _design_presets.json: base presets (only regenerate with --regenerate)
'''
    )
    parser.add_argument('--site', '-s', type=str, default=None,
                        help='Site name (defaults to DAW_SITE from .env)')
    parser.add_argument('--regenerate', '-r', action='store_true',
                        help='Force regeneration of brand files')
    parser.add_argument('--force-design-system', action='store_true',
                        help='Force rebuild of divitheme.json even if not stale')
    parser.add_argument('--no-design-system', action='store_true',
                        help='Skip design system build (assume up-to-date)')
    parser.add_argument('--name', '-n', type=str, help='Brand name (for regeneration)')
    parser.add_argument('--accent', '-a', type=str, help='Accent color (for regeneration)')
    parser.add_argument('--tone', '-t', type=str, choices=['luxury', 'tech', 'organic', 'minimal'],
                        help='Brand tone (for regeneration)')
    parser.add_argument('--full', '-f', action='store_true',
                        help='Full pipeline: brand → design → brief → deploy')
    parser.add_argument('--vie', action='store_true',
                        help='Use Visual Impact Engine (deterministic rich presets) instead of ML DIE')
    parser.add_argument('--prompt', '-p', type=str,
                        help='Page prompt (for --full mode)')
    parser.add_argument('--brief-only', action='store_true',
                        help='Stop after brief generation')
    parser.add_argument('--plan-only', action='store_true',
                        help='Stop after DIE plan generation')
    args = parser.parse_args()

    # Determine site
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

    print(f"[ORCHESTRATOR] Site: {site}")
    print(f"[ORCHESTRATOR] Brand dir: {brand_dir}")

    # ── Phase 1: Brand Files (one-shot, only if missing or --regenerate) ─
    if args.regenerate or not brand_files_exist(site_dir):
        if not args.regenerate and brand_files_exist(site_dir):
            print("[OK] Brand files exist — skipping generation")
        else:
            if not args.name or not args.accent:
                print("[ERROR] Brand files missing. Provide --name and --accent to generate")
                sys.exit(1)

            print(f"[PHASE 1] Generating brand files...")
            ok = generate_brand(
                site=site,
                name=args.name,
                accent=args.accent,
                tone=args.tone,
                fonts={'display': args.name, 'body': args.name}  # simplified
            )
            if not ok:
                sys.exit(1)
    else:
        print("[OK] Brand files already exist (one-shot)")

    # ── Phase 2: Design System (one-shot, only if stale or forced) ──
    if args.no_design_system:
        print("[SKIP] Design system build (--no-design-system)")
    elif design_system_needs_rebuild(vars_path, presets_path, ds_path,
                                     force=args.force_design_system):
        print(f"[PHASE 2] Building design system (one-shot)...")
        ok = build_design_system(site, vars_path, presets_path, ds_path)
        if not ok:
            sys.exit(1)
        print(f"[OK] Design system ready: {ds_path}")
    else:
        print(f"[SKIP] Design system up-to-date: {ds_path}")
        print("        (Use --force-design-system to rebuild, or --no-design-system to skip)")

    # ── Phase 3+: Full Pipeline (page generation) ──────────────────────
    if not args.full:
        print("\n[DONE] Brand + Design System verified")
        if not brand_files_exist(site_dir):
            print(f"    To generate a page next time:")
            print(f"      python daw_build.py --site {site} --full --prompt \"...\"")
        return

    if not args.prompt:
        print("[ERROR] --full requires --prompt")
        sys.exit(1)

    # Brief
    print(f"[PHASE 3] Generating brief...")
    brief_path = generate_brief(site, args.prompt)
    if not brief_path:
        sys.exit(1)
    if args.brief_only:
        return

    # Page generation: VIE (deterministic) or DIE (ML)
    if args.vie:
        print(f"[PHASE 4] Running Visual Impact Engine (deterministic)...")
        plan_path = run_vie(brief_path, site)
    else:
        print(f"[PHASE 4] Running DIE (ML pipeline)...")
        plan_path = run_die(brief_path, site)
    if not plan_path:
        sys.exit(1)
    if args.plan_only:
        return

    # Deploy
    print(f"[PHASE 5] Deploying...")
    deploy_page(plan_path, site)

    print("\n[DONE] Full pipeline completed successfully")


if __name__ == '__main__':
    main()
