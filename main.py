#!/usr/bin/env python3
import asyncio
import signal
import sys
import logging
from bot.core import Codex2050Bot
from rpc.server import RPCServer
from utils.logger import setup_logging
from config import Config

logger = setup_logging()

class Application:
    def __init__(self):
        self.config = Config()
        self.bot = None
        self.rpc_server = None
        
    async def startup(self):
        logger.info("🚀 Starting Codex2050 Application...")
        if not self.config.TELEGRAM_TOKEN:
            logger.error("❌ TELEGRAM_TOKEN not configured!")
            sys.exit(1)
        
        self.bot = Codex2050Bot(self.config)
        if self.config.ENABLE_RPC:
            self.rpc_server = RPCServer(host=self.config.RPC_HOST, port=self.config.RPC_PORT)
        logger.info("✅ Services initialized")
        
    async def shutdown(self):
        logger.info("🛑 Shutting down services...")
        if self.bot: await self.bot.shutdown()
        if self.rpc_server: await self.rpc_server.shutdown()
        
    async def run(self):
        await self.startup()
        tasks = []
        if self.bot: tasks.append(asyncio.create_task(self.bot.run()))
        if self.rpc_server: tasks.append(asyncio.create_task(self.rpc_server.run()))
        if self.config.ENABLE_WEB:
            from web.dashboard import start_web_server
            tasks.append(asyncio.create_task(start_web_server()))
            
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            await self.shutdown()

def signal_handler(signum, frame):
    sys.exit(0)

async def main():
    app = Application()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())
