import logging

from aiohttp import web

logger = logging.getLogger("RPC")

MAX_BODY_BYTES = 64 * 1024


class RPCServer:
    """Minimaler JSON-RPC-Mock (ohne Authentifizierung). Nur lokal betreiben."""

    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port
        self.app = web.Application(client_max_size=MAX_BODY_BYTES)
        self.app.router.add_post("/", self.handle_rpc)

    @staticmethod
    def _fehler(code, nachricht, id_=None, status=400):
        return web.json_response(
            {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": nachricht}}, status=status
        )

    async def handle_rpc(self, request):
        try:
            data = await request.json()
        except ValueError:
            return self._fehler(-32700, "Parse error")
        if not isinstance(data, dict) or not isinstance(data.get("method"), str):
            return self._fehler(-32600, "Invalid Request", data.get("id") if isinstance(data, dict) else None)
        method = data["method"]
        result = "0x1"  # Mock result
        if method == "eth_chainId":
            result = "0x21A8"
        return web.json_response({"jsonrpc": "2.0", "id": data.get("id"), "result": result})

    async def run(self):
        logger.info("RPC Server running on %s:%s", self.host, self.port)
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

    async def shutdown(self):
        pass
