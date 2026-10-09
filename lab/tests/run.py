"""Gedeelde testsuite, deel 1 (in de tools-container): Python-checks en het plan voor de
aansluitprofielen. Aangeroepen door `scripts/stack.sh test <naam>`.

Schrijft results/raw/<stack>/python.json en results/raw/<stack>/respect-jobs.json.
"""
import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from checks import gezondheid, isolatie, mijn_apis, rook, zgw  # noqa: E402
from kader import CATEGORIEEN, ROOT, Context, laad_manifest, lees_ps, plugin_mappen  # noqa: E402

MODULES = {"gezondheid": gezondheid, "rook": rook, "zgw": zgw, "burger-isolatie": isolatie, "mijn-apis": mijn_apis}


def laad_tests(pad: Path, modulenaam: str):
    if pad.exists():
        spec = importlib.util.spec_from_file_location(modulenaam, pad)
        spec.loader.exec_module(importlib.util.module_from_spec(spec))
        print(f"extra tests geladen: {pad}")


def laad_stack_tests(stack):
    """stacks/<naam>/tests.py en <plug-in>/tests.py mogen rooktests en isolatietypes registreren."""
    laad_tests(ROOT / "stacks" / stack / "tests.py", f"stack_tests_{stack}")
    for map_ in plugin_mappen():
        laad_tests(map_ / "tests.py", f"plugin_tests_{map_.name.replace('-', '_')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stack", required=True)
    ap.add_argument("--alleen", help="komma-gescheiden categorieen")
    ap.add_argument("--rapport", help="naam van het rapport (standaard de stack; met plug-ins <stack>+<plug-in>)")
    args = ap.parse_args()
    alleen = set(args.alleen.split(",")) if args.alleen else None
    if alleen and alleen - set(CATEGORIEEN):
        sys.exit(f"onbekende categorie(en): {alleen - set(CATEGORIEEN)}; kies uit {CATEGORIEEN}")
    rapport = args.rapport or args.stack
    raw = ROOT / "results" / "raw" / rapport
    raw.mkdir(parents=True, exist_ok=True)
    ctx = Context(args.stack, laad_manifest(args.stack), lees_ps(raw / "ps.json"), raw, alleen)
    laad_stack_tests(args.stack)
    start = time.time()
    gestart = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    for cat in CATEGORIEEN:
        if not ctx.wil(cat):
            continue
        print(f"\n== {cat}", flush=True)
        MODULES[cat].uitvoeren(ctx)
    for job in ctx.respect_jobs:
        job["uitvoer"] = f"results/raw/{rapport}/respect-{job['id']}.json"
        job["log"] = f"results/raw/{rapport}/respect-{job['id']}.log"
    (raw / "python.json").write_text(json.dumps({
        "stack": args.stack, "alleen": sorted(alleen) if alleen else None, "gestart": gestart,
        "duur_s": round(time.time() - start, 1), "checks": ctx.resultaten,
    }, indent=2, ensure_ascii=False))
    # bevat tokens: alleen in results/raw (staat in .gitignore)
    (raw / "respect-jobs.json").write_text(json.dumps(ctx.respect_jobs, indent=2))
    print(f"\n{len(ctx.resultaten)} Python-checks, {len(ctx.respect_jobs)} Respect-runs gepland")


if __name__ == "__main__":
    main()
