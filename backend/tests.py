from unittest.mock import Mock, patch

import requests
from django.test import Client, TestCase


class SearchApiTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _mock_response(self, payload: dict, status_code: int = 200):
        response = Mock()
        response.status_code = status_code
        response.raise_for_status.return_value = None
        response.json.return_value = payload
        return response

    def test_keyword_is_required(self):
        response = self.client.get("/api/search/")

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertIn("error", body)
        self.assertTrue(body["error"])

    @patch("backend.views.requests.get")
    def test_returns_normalized_and_sorted_results(self, mock_get):
        payload = {
            "prods": [
                {
                    "Id": "A1",
                    "name": "Product One",
                    "price": 1990,
                    "originPrice": 2590,
                    "picB": "/items/a1.jpg",
                },
                {
                    "Id": "A2",
                    "name": "Product Two",
                    "price": 990,
                    "originPrice": 1290,
                    "picB": "https://img.example.com/a2.jpg",
                },
            ]
        }
        mock_get.return_value = self._mock_response(payload)

        response = self.client.get(
            "/api/search/",
            {
                "keyword": "keyboard",
                "providers": "pchome",
                "sort": "price_asc",
                "limit": "2",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["keyword"], "keyboard")
        self.assertEqual(body["count"], 2)
        self.assertEqual(body["providers"], ["pchome"])
        self.assertEqual(body["provider_counts"]["pchome"], 2)
        self.assertEqual(body["sort"], "price_asc")
        self.assertEqual(body["warnings"], [])
        self.assertEqual(body["results"][0]["id"], "A2")
        self.assertEqual(body["results"][0]["price"], 990)
        self.assertEqual(body["results"][1]["id"], "A1")
        self.assertEqual(body["results"][1]["discount_amount"], 600)
        self.assertEqual(body["results"][1]["image_url"], "https://cs-a.ecimg.tw/items/a1.jpg")

    @patch("backend.views.requests.get")
    def test_provider_failure_returns_warning(self, mock_get):
        mock_get.side_effect = requests.RequestException("timeout")

        response = self.client.get("/api/search/", {"keyword": "monitor", "providers": "pchome"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 0)
        self.assertEqual(body["results"], [])
        self.assertTrue(body["warnings"])
        self.assertIn("PChome", body["warnings"][0])

    @patch("backend.views.requests.get")
    def test_ruten_provider_returns_products(self, mock_get):
        search_payload = {"Rows": [{"Id": "R100"}]}
        detail_payload = [
            {
                "ProdId": "R100",
                "ProdName": "Ruten Product",
                "PriceRange": [300, 600],
                "Image": "/g1/sample.jpg",
            }
        ]

        mock_get.side_effect = [
            self._mock_response(search_payload),
            self._mock_response(detail_payload),
        ]

        response = self.client.get(
            "/api/search/",
            {
                "keyword": "iphone",
                "providers": "ruten",
                "limit": "5",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["providers"], ["ruten"])
        self.assertEqual(body["provider_counts"]["ruten"], 1)
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["price"], 300)
        self.assertEqual(body["results"][0]["original_price"], 600)
        self.assertEqual(body["results"][0]["image_url"], "https://gcs.rimg.com.tw/g1/sample.jpg")

    @patch("backend.views.requests.get")
    def test_shopee_blocked_returns_warning_code(self, mock_get):
        mock_get.return_value = self._mock_response(
            {
                "error": 90309999,
                "is_login": False,
            },
            status_code=403,
        )

        response = self.client.get(
            "/api/search/",
            {
                "keyword": "iphone",
                "providers": "shopee",
                "limit": "5",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["providers"], ["shopee"])
        self.assertEqual(body["provider_counts"]["shopee"], 0)
        self.assertEqual(body["count"], 0)
        self.assertTrue(body["warnings"])
        self.assertIn("90309999", body["warnings"][0])

    @patch("backend.views.requests.get")
    def test_pchome_out_of_stock_includes_off_shelf_signals(self, mock_get):
        payload = {
            "prods": [
                {
                    "Id": "A-OUT",
                    "name": "Out Product",
                    "price": 2190,
                    "originPrice": 2690,
                    "picB": "/items/out.jpg",
                    "qty": 0,
                    "status": "off",
                }
            ]
        }
        mock_get.return_value = self._mock_response(payload)

        response = self.client.get(
            "/api/search/",
            {
                "keyword": "monitor",
                "providers": "pchome",
                "limit": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        item = body["results"][0]

        self.assertEqual(item["availability"], "out_of_stock")
        self.assertEqual(item["is_available"], False)
        self.assertEqual(item["is_off_shelf"], True)
        self.assertEqual(item["availability_confidence"], "high")
        self.assertIn("stock_qty<=0", item["availability_signals"])
        self.assertEqual(body["availability_summary"]["out_of_stock"], 1)