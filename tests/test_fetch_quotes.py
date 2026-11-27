import unittest

from unittest.mock import patch

from scripts.fetch_quotes import WATCHLIST, fetch_emotion, parse_pool_stock, parse_quote_result


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

    def test_a_share_market_watchlist_has_the_four_requested_indexes(self):
        indexes = [symbol for symbol, market, category in WATCHLIST if market == "A股" and category == "A股指数"]
        self.assertEqual(indexes, ["000001.SS", "399001.SZ", "399006.SZ", "000688.SS"])


class EmotionDataTests(unittest.TestCase):
    def test_parses_eastmoney_pool_item(self):
        item = parse_pool_stock({"c": "600000", "n": "Example", "zdp": "2.35", "p": 12345, "lbc": 2})
        self.assertEqual(item["symbol"], "600000")
        self.assertEqual(item["changePercent"], 2.35)
        self.assertEqual(item["limitUpDays"], 2)

    @patch("scripts.fetch_quotes.fetch_json")
    def test_fetches_breadth_limit_pools_and_yesterday_performance(self, fetch_json):
        def response(url):
            if "clist/get" in url:
                return {"data": {"total": 4, "diff": [
                    {"f12": "600000", "f3": 1.2}, {"f12": "000002", "f3": -2.5},
                    {"f12": "000003", "f3": 0}, {"f12": "000004", "f3": 3.1},
                ]}}
            if "getYesterdayZTPool" in url:
                return {"data": {"tc": 2, "pool": [
                    {"c": "600000", "n": "Alpha", "zdp": 3.0},
                    {"c": "000001", "n": "Beta", "zdp": -1.0},
                ]}}
            if "getTopicZTPool" in url and "date=20261126" in url:
                return {"data": {"tc": 2, "pool": [{"c": "600000"}]}}
            if "getTopicDTPool" in url and "date=20261126" in url:
                return {"data": {"tc": 1, "pool": [
                    {"c": "000002", "n": "Gamma", "zdp": -10.0},
                ]}}
            return {"data": {"tc": 1, "pool": []}}

        fetch_json.side_effect = response
        result = fetch_emotion("20261127")
        self.assertEqual(result["breadth"], {"up": 2, "down": 1, "flat": 1, "total": 4})
        self.assertEqual(result["pools"]["limitUpCount"], 1)
        self.assertEqual(result["pools"]["limitDownCount"], 1)
        self.assertEqual(result["pools"]["brokenRate"], 50.0)
        self.assertEqual(result["yesterdayPerformance"]["up"]["avgChangePercent"], 1.0)
        self.assertEqual(result["yesterdayLimitDown"][0]["changePercent"], -2.5)


if __name__ == "__main__":
    unittest.main()
