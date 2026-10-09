"""Maakt Keycloak bereikbaar op http://localhost:8080 binnen een andere container.

Keycloak zet als issuer in elk token http://localhost:8080/realms/<realm>, het adres dat
de browser gebruikt (KC_HOSTNAME). Spring Boot-toepassingen (NL Portal, GZAC, IKO) halen
de OIDC-configuratie op via die issuer en controleren hem. Binnen hun container wijst
localhost naar de container zelf. Deze sidecar deelt de netwerk-namespace van de
toepassing (network_mode: service:<naam>) en stuurt 127.0.0.1:8080 door naar
keycloak.local:8080. De toepassing zelf luistert daarom op een andere poort.

Gebruik: python keycloak_doorgifte.py [luisterpoort] [doelhost] [doelpoort]
"""
import asyncio
import sys

LPORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
DOEL = sys.argv[2] if len(sys.argv) > 2 else "keycloak.local"
DPORT = int(sys.argv[3]) if len(sys.argv) > 3 else 8080


async def pijp(r, w):
    try:
        while (d := await r.read(65536)):
            w.write(d)
            await w.drain()
    except Exception:
        pass
    finally:
        try:
            w.close()
        except Exception:
            pass


async def verbinding(cr, cw):
    try:
        ur, uw = await asyncio.open_connection(DOEL, DPORT)
    except Exception:
        cw.close()
        return
    await asyncio.gather(pijp(cr, uw), pijp(ur, cw))


async def main():
    s = await asyncio.start_server(verbinding, "127.0.0.1", LPORT)
    print(f"doorgifte 127.0.0.1:{LPORT} -> {DOEL}:{DPORT}", flush=True)
    async with s:
        await s.serve_forever()


asyncio.run(main())
