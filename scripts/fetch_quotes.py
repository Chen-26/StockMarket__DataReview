#!/usr/bin/env python3
"""Fetch a small A-share and US-market quote snapshot for GitHub Pages."""

import argparse
import datetime as dt
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


WATCHLIST = [
    ("^GSPC", "美股", "美股指数"),
    ("^IXIC", "美股", "美股指数"),
    ("^DJI", "美股", "美股指数"),
    ("000001.SS", "A股", "A股指数"),
    ("399001.SZ", "A股", "A股指数"),
    ("399006.SZ", "A股", "A股指数"),
    ("000688.SS", "A股", "A股指数"),
    ("600519.SS", "A股", "A股个股"),
    ("300750.SZ", "A股", "A股个股"),
    ("AAPL", "美股", "美股个股"),
    ("NVDA", "美股", "美股个股"),
    ("TSLA", "美股", "美股个股"),
]


def parse_quote_result(result, symbol, market, category):
    """Normalize one Yahoo Finance chart result into the dashboard format."""
    meta = result.get("meta", {})
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    closes = [value for value in quote.get("close", []) if isinstance(value, (int, float))]
    price = meta.get("regularMarketPrice")
    if price is None and closes:
        price = closes[-1]
    previous = meta.get("chartPreviousClose")
    if previous is None:
        previous = meta.get("previousClose")
    if price is None:
        raise ValueError("no recent price")

    change = price - previous if previous is not None else None
    volume = next(
        (value for value in reversed(quote.get("volume", [])) if isinstance(value, (int, float))),
        None,
    )
    market_time = meta.get("regularMarketTime")
    return {
        "symbol": symbol,
        "name": meta.get("longName") or meta.get("shortName") or symbol,
        "market": market,
        "category": category,
        "currency": meta.get("currency"),
        "price": price,
        "previousClose": previous,
        "change": change,
        "changePercent": (change / previous * 100) if change is not None and previous else None,
        "volume": volume,
        "marketTime": dt.datetime.fromtimestamp(market_time, dt.timezone.utc).isoformat()
        if market_time
        else None,
        "sparkline": closes[-40:],
    }


def fetch_quote(symbol, market, category):
    query = urllib.parse.urlencode(
        {"range": "1d", "interval": "1m", "includePrePost": "false"}
    )
    endpoint = "https://query1.finance.yahoo.com/v8/finance/chart/{}?{}".format(
        urllib.parse.quote(symbol, safe="^."), query
    )
    request = urllib.request.Request(
        endpoint,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; StockMarketDataReview/1.0)",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    results = payload.get("chart", {}).get("result") or []
    if not results:
        raise ValueError(payload.get("chart", {}).get("error") or "empty chart result")
    return parse_quote_result(results[0], symbol, market, category)


def build_snapshot(watchlist=WATCHLIST, fetcher=fetch_quote, pause=0.35):
    quotes, errors = [], []
    for symbol, market, category in watchlist:
        try:
            quotes.append(fetcher(symbol, market, category))
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, IndexError, json.JSONDecodeError) as exc:
            errors.append({"symbol": symbol, "error": str(exc)[:180]})
        if pause:
            time.sleep(pause)
    return {
        "updatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider": "Yahoo Finance chart · 1m",
        "intervalMinutes": 5,
        "quotes": quotes,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="public/data/quotes.json")
    args = parser.parse_args()
    snapshot = build_snapshot()
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, ensure_ascii=False, separators=(",", ":"))
    print(
        "Wrote {} quotes ({} unavailable) to {}".format(
            len(snapshot["quotes"]), len(snapshot["errors"]), args.output
        )
    )


if __name__ == "__main__":
    main()
