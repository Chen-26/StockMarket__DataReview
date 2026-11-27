#!/usr/bin/env python3
"""Fetch a small review watchlist from Yahoo Finance's chart endpoint."""
import argparse
import datetime as dt
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

WATCHLIST = [
    ("^GSPC", "����", "����ָ��"),
    ("^IXIC", "����", "����ָ��"),
    ("^DJI", "����", "����ָ��"),
    ("000001.SS", "A��", "A��ָ��"),
    ("000300.SS", "A��", "A��ָ��"),
    ("399001.SZ", "A��", "A��ָ��"),
    ("399006.SZ", "A��", "A��ָ��"),
    ("600519.SS", "A��", "A�ɸ���"),
    ("300750.SZ", "A��", "A�ɸ���"),
    ("AAPL", "����", "���ɸ���"),
    ("NVDA", "����", "���ɸ���"),
    ("TSLA", "����", "���ɸ���"),
]


def fetch(symbol):
    query = urllib.parse.urlencode({"range": "1d", "interval": "1m", "includePrePost": "false"})
    url = "https://query1.finance.yahoo.com/v8/finance/chart/{}?{}".format(
        urllib.parse.quote(symbol, safe="^."), query
    )
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; StockMarketDataReview/1.0)", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    results = payload.get("chart", {}).get("result") or []
    if not results:
        raise ValueError(payload.get("chart", {}).get("error") or "empty chart result")
    result = results[0]
    meta = result.get("meta", {})
    indicators = result.get("indicators", {}).get("quote", [{}])[0]
    closes = [v for v in indicators.get("close", []) if isinstance(v, (int, float))]
    price = meta.get("regularMarketPrice") or (closes[-1] if closes else None)
    previous = meta.get("chartPreviousClose") or meta.get("previousClose")
    if price is None:
        raise ValueError("no recent price")
    change = price - previous if previous is not None else None
    percent = change / previous * 100 if previous else None
    return {
        "symbol": symbol,
        "name": meta.get("longName") or meta.get("shortName") or symbol,
        "market": next(market for code, market, _ in WATCHLIST if code == symbol),
        "category": next(category for code, _, category in WATCHLIST if code == symbol),
        "currency": meta.get("currency"),
        "price": round(price, 6),
        "previousClose": previous,
        "change": round(change, 6) if change is not None else None,
        "changePercent": round(percent, 4) if percent is not None else None,
        "volume": (indicators.get("volume") or [None])[-1],
        "marketTime": dt.datetime.fromtimestamp(meta.get("regularMarketTime", 0), dt.timezone.utc).isoformat()
        if meta.get("regularMarketTime") else None,
        "sparkline": closes[-40:],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="public/data/quotes.json")
    args = parser.parse_args()
    quotes, errors = [], []
    for symbol, _, _ in WATCHLIST:
        try:
            quotes.append(fetch(symbol))
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, IndexError, json.JSONDecodeError) as exc:
            errors.append({"symbol": symbol, "error": str(exc)[:180]})
        time.sleep(0.35)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    output = {
        "updatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider": "Yahoo Finance chart �� 1m",
        "intervalMinutes": 5,
        "quotes": quotes,
        "errors": errors,
    }
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, separators=(",", ":"))
    print("Wrote {} quotes ({} unavailable) to {}".format(len(quotes), len(errors), args.output))


if __name__ == "__main__":
    main()

