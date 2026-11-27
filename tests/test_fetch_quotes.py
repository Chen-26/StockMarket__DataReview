import unittest

from scripts.fetch_quotes import parse_quote_result


class ParseQuoteResultTests(unittest.TestCase):
    def setUp(self):
        self.result = {
            "meta": {
                "longName": "Test Security",
                "regularMarketPrice": 101.0,
                "chartPreviousClose": 100.0,
                "currency": "USD",
                "regularMarketTime": 1795791600,
            },
            "indicators": {
                "quote": [{"close": [99.0, 100.0, 101.0], "volume": [10, None, 30]}]
            },
        }

    def test_normalizes_quote_and_change(self):
        quote = parse_quote_result(self.result, "TEST", "美股", "美股个股")
        self.assertEqual(quote["symbol"], "TEST")
        self.assertEqual(quote["name"], "Test Security")
        self.assertEqual(quote["price"], 101.0)
        self.assertEqual(quote["change"], 1.0)
        self.assertEqual(quote["changePercent"], 1.0)
        self.assertEqual(quote["volume"], 30)
        self.assertEqual(quote["sparkline"], [99.0, 100.0, 101.0])

    def test_uses_last_close_when_market_price_is_missing(self):
        self.result["meta"].pop("regularMarketPrice")
        quote = parse_quote_result(self.result, "TEST", "美股", "美股个股")
        self.assertEqual(quote["price"], 101.0)

    def test_rejects_response_without_price(self):
        self.result["meta"].pop("regularMarketPrice")
        self.result["indicators"]["quote"][0]["close"] = []
        with self.assertRaisesRegex(ValueError, "no recent price"):
            parse_quote_result(self.result, "TEST", "美股", "美股个股")


if __name__ == "__main__":
    unittest.main()
