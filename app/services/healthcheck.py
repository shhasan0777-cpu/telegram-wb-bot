from aiohttp import web

async def health(_request):
    return web.json_response({"status": "ok"})

async def start_health_server(host: str, port: int):
    app = web.Application()
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
