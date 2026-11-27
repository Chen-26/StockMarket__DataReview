#!/usr/bin/env python3
"""Small public Tonghuashun quote adapter used by the dashboard collector.

The endpoints are public web interfaces, not the authenticated iFinD API. They
may change or rate-limit automated callers; callers should surface failures.
"""

import datetime as dt
import json
import re
import urllib.parse
import urllib.request
import time
import urllib.error


HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://q.10jqka.com.cn/",
    "User-Agent": "Mozilla/5.0 (compatible; StockMarketDataReview/1.0)",
}
DATA_HEADERS = dict(HEADERS, Referer="https://data.10jqka.com.cn/")

THS_CODES = {
    "000001.SS": "1A0001",
    "399001.SZ": "399001",
    "399006.SZ": "399006",
    "000688.SS": "1B0688",
    "600519.SS": "600519",
    "300750.SZ": "300750",
}


def _fetch_text(url, headers=None):
    for attempt in range(3):
        request = urllib.request.Request(url, headers=headers or HEADERS)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
            time.sleep(0.6 * (attempt + 1))


def fetch_quote(symbol, market, category):
    """Fetch the latest daily quote/K-line row from Tonghuashun."""
    code = THS_CODES.get(symbol)
    if not code:
        raise ValueError("symbol is not mapped to a Tonghuashun code")
    endpoint = "https://d.10jqka.com.cn/v6/line/hs_{}/01/last1200.js".format(code)
    text = _fetch_text(endpoint)
    match = re.match(r"^[\w$]+\((.*)\);?\s*$", text, re.S)
    if match:
        text = match.group(1)
    payload = json.loads(text)
    raw = (payload.get("data") or "").strip()
    rows = [line.split(",") for line in raw.split(";") if line]
    rows = [row for row in rows if len(row) >= 5 and row[0].isdigit()]
    if not rows:
        raise ValueError("Tonghuashun returned no daily quote rows")
    latest = rows[-1]
    previous = rows[-2] if len(rows) > 1 else None
    price = float(latest[4])
    previous_close = float(previous[4]) if previous else None
    change = price - previous_close if previous_close else None
    trade_day = dt.datetime.strptime(latest[0], "%Y%m%d").date()
    market_time = dt.datetime.combine(
        trade_day, dt.time(15, 0), tzinfo=dt.timezone(dt.timedelta(hours=8))
    )
    name = {
        "000001.SS": "上证指数",
        "399001.SZ": "深证成指",
        "399006.SZ": "创业板指",
        "000688.SS": "科创50",
        "600519.SS": "贵州茅台",
        "300750.SZ": "宁德时代",
    }[symbol]
    return {
        "symbol": symbol,
        "name": name,
        "market": market,
        "category": category,
        "currency": "CNY",
        "price": price,
        "previousClose": previous_close,
        "change": change,
        "changePercent": (change / previous_close * 100)
        if change is not None and previous_close
        else None,
        "volume": float(latest[5]) if len(latest) > 5 and latest[5] else None,
        "marketTime": market_time.isoformat(),
        "tradeDate": trade_day.isoformat(),
        "sparkline": [float(row[4]) for row in rows[-40:]],
        "provider": "Tonghuashun",
    }


def _fetch_pool(route, day):
    query = urllib.parse.urlencode(
        {
            "page": 1,
            "limit": 1600,
            "field": "199112,10,9001,330323,330324,330325,9002,330329,133971,133970,1968584,3475914,9003,9004",
            "filter": "HS,GEM2STAR",
            "date": day,
            "order_field": "330324",
            "order_type": 0,
        }
    )
    url = "https://data.10jqka.com.cn/dataapi/limit_up/{}?{}".format(route, query)
    payload = json.loads(_fetch_text(url, DATA_HEADERS))
    if payload.get("status_code") not in (None, 0):
        raise ValueError("Tonghuashun pool error: {}".format(payload.get("status_msg")))
    data = payload.get("data") or {}
    info = data.get("info")
    if not isinstance(info, list):
        raise ValueError("Tonghuashun pool response schema changed")
    meta = data.get("page") or {}
    total = meta.get("total")
    trade_date = data.get("date") or day
    if total is not None and int(total) != len(info):
        raise ValueError("Tonghuashun pool pagination is incomplete")
    return info, str(trade_date)


def fetch_emotion_pools(day):
    """Fetch limit-up, limit-down and broken-board pools for YYYYMMDD."""
    routes = {
        "limitUp": "limit_up_pool",
        "limitDown": "lower_limit_pool",
        "broken": "open_limit_pool",
    }
    result = {}
    dates = set()
    for key, route in routes.items():
        rows, trade_date = _fetch_pool(route, day)
        dates.add(trade_date)
        result[key] = rows
    if len(dates) != 1:
        raise ValueError("Tonghuashun pool dates do not match")
    return {"tradeDate": dates.pop(), "pools": result, "provider": "Tonghuashun"}
