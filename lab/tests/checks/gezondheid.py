"""Categorie 1, gezondheid: draaien de containers van elk component, en antwoordt het?"""
import requests

from kader import Context, eis

CAT = "gezondheid"


def _component(ctx: Context, comp: dict):
    delen = []
    for svc in comp.get("services", []):
        rij = ctx.ps.get(svc)
        eis(rij is not None, f"service {svc} bestaat niet in deze stack (geen container)")
        state, health = rij.get("State"), rij.get("Health") or ""
        eis(state == "running", f"service {svc} is {state} ({rij.get('Status', '')})")
        eis(health in ("", "healthy"), f"service {svc} is {health}")
        delen.append(f"{svc} {health or state}")
    h = comp.get("health")
    if h:
        r = requests.get(h["url"], timeout=15, allow_redirects=False)
        eis(r.status_code in h.get("status", [200]), f"{h['url']} gaf {r.status_code}, verwacht {h.get('status', [200])}")
        delen.append(f"HTTP {r.status_code}")
    images = sorted({ctx.ps[s].get("Image", "?") for s in comp.get("services", []) if s in ctx.ps})
    return "; ".join(delen) + (f" [{', '.join(images)}]" if images else "")


def uitvoeren(ctx: Context):
    for comp in ctx.manifest["componenten"]:
        cid = f"{CAT}/{comp['id']}"
        if not comp.get("services") and not comp.get("health"):
            ctx.overslaan(cid, CAT, comp["id"], comp["naam"], "geen services of health-URL in het manifest")
            continue
        ctx.voer_uit(cid, CAT, comp["id"], f"{comp['naam']} draait en antwoordt", _component, ctx, comp)
    for comp in ctx.manifest.get("gepland", []):
        ctx.overslaan(f"{CAT}/{comp['id']}", CAT, comp["id"], comp.get("naam", comp["id"]),
                      "gepland, nog niet in de stack" + (f": {comp['opmerking']}" if comp.get("opmerking") else ""))
