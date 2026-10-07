"""Tests für den JSON-RPC-Mock (rpc.server): robuste Fehlerbehandlung, kein 500 bei Müll."""

import asyncio
import importlib.util
import unittest

HAT_AIOHTTP = importlib.util.find_spec("aiohttp") is not None


@unittest.skipUnless(HAT_AIOHTTP, "aiohttp nicht installiert")
class TestRPC(unittest.TestCase):
    def _anfrage(self, **kwargs):
        from aiohttp.test_utils import TestClient, TestServer
        from rpc.server import RPCServer

        async def lauf():
            async with TestClient(TestServer(RPCServer().app)) as c:
                r = await c.post("/", **kwargs)
                return r.status, await r.json()
        return asyncio.run(lauf())

    def test_standard_bindung_nur_lokal(self):
        from rpc.server import RPCServer
        self.assertEqual(RPCServer().host, "127.0.0.1")

    def test_chain_id(self):
        status, body = self._anfrage(json={"jsonrpc": "2.0", "id": 1, "method": "eth_chainId"})
        self.assertEqual((status, body["result"], body["id"]), (200, "0x21A8", 1))

    def test_kaputtes_json_gibt_parse_error_statt_500(self):
        status, body = self._anfrage(data=b"{nope", headers={"Content-Type": "application/json"})
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], -32700)

    def test_ungueltige_anfrage(self):
        for payload in ([1, 2], {"id": 1}, {"method": 5}):
            status, body = self._anfrage(json=payload)
            self.assertEqual((status, body["error"]["code"]), (400, -32600), payload)


if __name__ == "__main__":
    unittest.main()
