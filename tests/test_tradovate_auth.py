import unittest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.tradovate_client import TradovateClient
from bot.config import config

class TestTradovateClient(unittest.TestCase):
    def setUp(self):
        self.client = TradovateClient()

    @patch("requests.post")
    def test_authentication_flow(self, mock_post):
        # Simular resposta positiva de /auth/accesstokenrequest
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "accessToken": "mock_jwt_token_12345",
            "userId": 999,
            "expirationTime": "2026-09-17T12:00:00Z"
        }
        mock_post.return_value = mock_resp

        # Forçar credencials temporals per al test
        with patch.object(config, "user", "test_user"), patch.object(config, "password", "test_pass"):
            success = self.client.authenticate()
            self.assertTrue(success)
            self.assertEqual(self.client.access_token, "mock_jwt_token_12345")
            self.assertEqual(self.client.user_id, 999)

    @patch("requests.post")
    def test_place_bracket_order_payload(self, mock_post):
        self.client.access_token = "valid_token"
        self.client.account_id = 12345
        self.client.account_spec = "DEMO12345"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"orderId": 8888, "status": "Working"}
        mock_post.return_value = mock_resp

        # Test Sell Limit OSO (London High)
        res = self.client.place_bracket_order(
            symbol="MNQZ6",
            action="Sell",
            qty=1,
            entry_price=29400.00,
            tp_price=29390.00,
            sl_price=29460.00
        )

        self.assertIsNotNone(res)
        self.assertEqual(res.get("orderId"), 8888)

        # Validar payload enviat
        args, kwargs = mock_post.call_args
        payload = kwargs.get("json")
        self.assertEqual(payload["action"], "Sell")
        self.assertEqual(payload["symbol"], "MNQZ6")
        self.assertEqual(payload["orderType"], "Limit")
        self.assertEqual(payload["price"], 29400.00)
        
        # Brackets
        self.assertEqual(payload["bracket1"]["action"], "Buy")
        self.assertEqual(payload["bracket1"]["orderType"], "Stop")
        self.assertEqual(payload["bracket1"]["stopPrice"], 29460.00)
        
        self.assertEqual(payload["bracket2"]["action"], "Buy")
        self.assertEqual(payload["bracket2"]["orderType"], "Limit")
        self.assertEqual(payload["bracket2"]["price"], 29390.00)

if __name__ == "__main__":
    unittest.main()
