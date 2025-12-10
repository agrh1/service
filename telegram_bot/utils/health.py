from aiohttp import web
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest

BOT_UP = Gauge("telegram_bot_up", "Telegram bot process state")


def _create_app():
    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_get("/metrics", metrics)
    return app


async def health(_request):
    return web.json_response({"status": "ok", "service": "telegram_bot"})


async def metrics(_request):
    return web.Response(body=generate_latest(), content_type=CONTENT_TYPE_LATEST)


async def start_health_server(port: int) -> web.AppRunner:
    app = _create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    BOT_UP.set(1)
    return runner


def stop_bot_metric():
    BOT_UP.set(0)
