from aiohttp import web
import logging
logger = logging.getLogger("RPC")

class RPCServer:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.app.router.add_post("/", self.handle_rpc)
        
    async def handle_rpc(self, request):
        data = await request.json()
        method = data.get("method")
        result = "0x1" # Mock result
        if method == "eth_chainId": result = "0x21A8"
        return web.json_response({"jsonrpc": "2.0", "id": data.get("id"), "result": result})
        
    async def run(self):
        logger.info(f"🔗 RPC Server running on {self.port}")
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
    async def shutdown(self):
        pass
