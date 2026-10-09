"""TCP-doorsturing voor host-tools: luistert op 127.0.0.1:<lport>, stuurt door naar 127.0.0.1:<rport>.

Gebruik: python3 tools/poort_doorsturen.py 8000 8001  (met "127.0.0.1 openzaak.local" in /etc/hosts
is Open Zaak dan op de host bereikbaar onder zijn canonieke URL http://openzaak.local:8000).
"""
import asyncio, sys
L, R = int(sys.argv[1]), int(sys.argv[2])
async def pipe(r, w):
    try:
        while (d := await r.read(65536)):
            w.write(d); await w.drain()
    except Exception: pass
    finally:
        try: w.close()
        except Exception: pass
async def handle(cr, cw):
    try: ur, uw = await asyncio.open_connection('127.0.0.1', R)
    except Exception: cw.close(); return
    await asyncio.gather(pipe(cr, uw), pipe(ur, cw))
async def main():
    s = await asyncio.start_server(handle, '127.0.0.1', L)
    async with s: await s.serve_forever()
asyncio.run(main())
