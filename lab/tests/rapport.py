"""Gedeelde testsuite, deel 3 (in de tools-container): voegt de Python-checks en de
Respect-runs samen tot results/<stack>.json (machineleesbaar) en results/<stack>.md.

Exitcode 1 als er een fail is die niet in `bekende_fouten` van stack.yaml staat.
"""
import argparse
import fnmatch
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kader import CATEGORIEEN, ROOT, laad_manifest, lees_ps  # noqa: E402

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def schoon(tekst, n=400):
    tekst = ANSI.sub("", tekst or "").strip()
    tekst = re.sub(r"\s+", " ", tekst)
    return tekst[:n]


def respect_checks(job):
    uitvoer = ROOT / job["uitvoer"]
    basis = {"categorie": job["categorie"], "component": job["component"]}
    if not uitvoer.exists():
        log = (ROOT / job["log"]).read_text() if (ROOT / job["log"]).exists() else "geen log"
        return [{**basis, "id": job["prefix"], "naam": job["naam"], "status": "fail",
                 "reden": "Respect gaf geen uitvoer: " + schoon(log[-600:])}]
    data = json.loads(uitvoer.read_text())
    uit = []
    for bestand in data.get("files", {}).values():
        for wf in bestand.get("executedWorkflows", []):
            wid = wf["workflowId"]
            r = {**basis, "id": f"{job['prefix']}/{wid}", "naam": f"{job['naam']}: {wid}",
                 "duur_s": round(wf.get("totalTimeMs", 0) / 1000, 2)}
            stappen = wf.get("executedSteps", [])
            if wf.get("status") in ("success", "warn"):
                r["status"] = "pass"
                waarsch = [c for s in stappen for c in s.get("checks", []) if not c.get("passed")]
                r["detail"] = f"{len(stappen)} stap(pen)" + (
                    f", {len(waarsch)} waarschuwing(en), o.a. {schoon(waarsch[0].get('message'), 160)}" if waarsch else "")
            else:
                r["status"] = "fail"
                reden = f"workflow {wf.get('status')}"
                for s in stappen:
                    fout = [c for c in s.get("checks", []) if not c.get("passed") and c.get("severity", "error") == "error"]
                    if s.get("status") == "error" or fout:
                        c = (fout or [{}])[0]
                        reden = f"stap {s.get('stepId')}: {c.get('name', '')}: {schoon(c.get('message'), 300)}"
                        break
                if wf.get("globalTimeoutError"):
                    reden = "time-out van de workflow"
                r["reden"] = reden
            uit.append(r)
    if not uit:
        uit.append({**basis, "id": job["prefix"], "naam": job["naam"], "status": "fail",
                    "reden": "Respect voerde geen workflows uit"})
    return uit


def git_commit():
    git = ROOT / ".git"
    try:
        head = (git / "HEAD").read_text().strip()
        if not head.startswith("ref:"):
            return head[:12]
        ref = head.split(" ", 1)[1]
        if (git / ref).exists():
            return (git / ref).read_text().strip()[:12]
        for regel in (git / "packed-refs").read_text().splitlines():
            if regel.endswith(ref):
                return regel.split()[0][:12]
    except OSError:
        pass
    return None


def markdown(rapport):
    s = rapport["samenvatting"]
    r = [f"# Testresultaten stack {rapport['stack']}", "",
         f"{rapport['titel']}. Gedraaid op {rapport['gestart']}, commit `{rapport.get('commit') or '?'}`.", "",
         *([("Plug-ins: " + ", ".join(f"{p.get('titel') or p['naam']} ({p.get('leverancier') or 'onbekende leverancier'}"
                                       + (f", {p['versie']}" if p.get("versie") else "") + ")"
                                       for p in rapport["plugins"]) + "."), ""] if rapport.get("plugins") else
           ["Zonder plug-ins.", ""]),
         f"**{s['pass']} geslaagd, {s['fail']} gefaald ({s['fail_bekend']} bekend, {s['fail_onverwacht']} onverwacht), "
         f"{s['skip']} overgeslagen.**", "",
         "| Categorie | Geslaagd | Gefaald | Waarvan bekend | Overgeslagen |", "|---|---|---|---|---|"]
    for cat, c in rapport["per_categorie"].items():
        r.append(f"| {cat} | {c['pass']} | {c['fail']} | {c['fail_bekend']} | {c['skip']} |")
    for cat in CATEGORIEEN:
        checks = [c for c in rapport["checks"] if c["categorie"] == cat]
        if not checks:
            continue
        r += ["", f"## {cat}", "", "| Status | Check | Toelichting |", "|---|---|---|"]
        for c in checks:
            status = {"pass": "geslaagd", "fail": "GEFAALD", "skip": "overgeslagen"}[c["status"]]
            if c.get("bekend"):
                status = "gefaald (bekend)"
            tekst = c.get("detail") or c.get("reden") or ""
            if c.get("bekend"):
                tekst = f"{tekst} Bekend: {c['bekend']}"
            tekst = tekst.replace("|", "\\|")
            r.append(f"| {status} | `{c['id']}` | {tekst} |")
    r += ["", "## Images", "", "| Service | Image | Status |", "|---|---|---|"]
    for svc, info in sorted(rapport["omgeving"]["services"].items()):
        r.append(f"| {svc} | `{info['image']}` | {info['status']} |")
    return "\n".join(r) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stack", required=True)
    ap.add_argument("--rapport", help="naam van het rapport (standaard de stack)")
    args = ap.parse_args()
    naam = args.rapport or args.stack
    raw = ROOT / "results" / "raw" / naam
    manifest = laad_manifest(args.stack)
    python = json.loads((raw / "python.json").read_text())
    checks = list(python["checks"])
    jobs_pad = raw / "respect-jobs.json"
    for job in json.loads(jobs_pad.read_text()) if jobs_pad.exists() else []:
        checks += respect_checks(job)
    checks.sort(key=lambda c: CATEGORIEEN.index(c["categorie"]))

    bekend = manifest.get("bekende_fouten") or {}
    for c in checks:
        c.pop("traceback", None)
        if c["status"] == "fail":
            for patroon, uitleg in bekend.items():
                if fnmatch.fnmatchcase(c["id"], patroon):
                    c["bekend"] = " ".join(str(uitleg).split())
                    break

    def tel(lijst):
        t = Counter(c["status"] for c in lijst)
        fb = sum(1 for c in lijst if c["status"] == "fail" and c.get("bekend"))
        return {"pass": t["pass"], "fail": t["fail"], "skip": t["skip"], "fail_bekend": fb,
                "fail_onverwacht": t["fail"] - fb, "totaal": len(lijst)}

    ps = lees_ps(raw / "ps.json")
    rapport = {
        "stack": args.stack,
        "titel": manifest.get("titel", args.stack),
        "plugins": [{k: v for k, v in p.items() if k != "map" and v} for p in manifest.get("plugins", [])],
        "gestart": python.get("gestart"),
        "gegenereerd": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "commit": git_commit(),
        "alleen": python.get("alleen"),
        "samenvatting": tel(checks),
        "per_categorie": {cat: tel([c for c in checks if c["categorie"] == cat])
                          for cat in CATEGORIEEN if any(c["categorie"] == cat for c in checks)},
        "omgeving": {"services": {s: {"image": r.get("Image"), "status": r.get("Status")} for s, r in ps.items()}},
        "checks": checks,
    }
    uit = ROOT / "results"
    (uit / f"{naam}.json").write_text(json.dumps(rapport, indent=2, ensure_ascii=False) + "\n")
    (uit / f"{naam}.md").write_text(markdown(rapport))

    s = rapport["samenvatting"]
    print()
    for cat, c in rapport["per_categorie"].items():
        print(f"  {cat:<16} {c['pass']:>3} geslaagd  {c['fail']:>3} gefaald ({c['fail_bekend']} bekend)  {c['skip']:>3} overgeslagen")
    print(f"\nStack {args.stack}: {s['pass']} geslaagd, {s['fail']} gefaald ({s['fail_bekend']} bekend), "
          f"{s['skip']} overgeslagen. Rapport: results/{naam}.json en results/{naam}.md")
    for c in checks:
        if c["status"] == "fail" and not c.get("bekend"):
            print(f"  ONVERWACHT GEFAALD {c['id']}: {c.get('reden', '')[:300]}")
    sys.exit(1 if s["fail_onverwacht"] else 0)


if __name__ == "__main__":
    main()
