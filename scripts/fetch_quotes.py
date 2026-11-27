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

try:
    from ths_provider import fetch_emotion_pools as fetch_ths_emotion_pools
    from ths_provider import fetch_quote as fetch_ths_quote
except ImportError:
    fetch_ths_emotion_pools = None
    fetch_ths_quote = None


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



EASTMONEY_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://quote.eastmoney.com/",
    "User-Agent": "Mozilla/5.0 (compatible; StockMarketDataReview/1.0)",
}


def fetch_json(url):
    request = urllib.request.Request(url, headers=EASTMONEY_HEADERS)
    with urllib.request.urlopen(request, timeout=18) as response:
        return json.loads(response.read().decode("utf-8"))


def eastmoney_list(endpoint, params):
    url = "https://push2ex.eastmoney.com/{}?{}".format(
        endpoint, urllib.parse.urlencode(params)
    )
    payload = fetch_json(url)
    data = payload.get("data") or {}
    pool = data.get("pool") or data.get("diff") or []
    if isinstance(pool, dict):
        pool = list(pool.values())
    return data, pool


def parse_pool_stock(item):
    """Normalize Eastmoney's current and yesterday limit-pool item."""
    code = item.get("c") or item.get("code") or item.get("f12")
    name = item.get("n") or item.get("name") or item.get("f14") or code
    change = item.get("zdp")
    if change is None:
        change = item.get("f3")
    if isinstance(change, str):
        change = change.replace("%", "").strip()
    try:
        change = float(change) if change is not None else None
    except (TypeError, ValueError):
        change = None
    return {
        "symbol": str(code or ""),
        "name": str(name or ""),
        "changePercent": change,
        "price": item.get("p") or item.get("f2"),
        "limitUpDays": item.get("lbc"),
    }


def fetch_emotion(trade_date=None):
    """Fetch breadth and prior cohorts, with THS as the limit-pool source."""
    now_cn = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    day = trade_date or now_cn.strftime("%Y%m%d")
    if trade_date is None and now_cn.weekday() >= 5:
        for offset in range(1, 11):
            candidate = (now_cn - dt.timedelta(days=offset)).strftime("%Y%m%d")
            try:
                prior, pool = eastmoney_list("getTopicZTPool", {
                    "ut": "7eea3edcaed734bea9cbfc24409ed989", "dpt": "wz.ztzt",
                    "Pageindex": 0, "pagesize": 1000, "sort": "fbt:asc", "date": candidate,
                })
                if int(prior.get("tc", len(pool)) or 0) > 0:
                    day = candidate
                    break
            except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
                continue
    display_day = "{}-{}-{}".format(day[:4], day[4:6], day[6:8])
    current_changes = {}
    result = {
        "tradeDate": display_day,
        "breadth": {"up": None, "down": None, "flat": None, "total": None},
        "pools": {"limitUpCount": None, "limitDownCount": None, "brokenCount": None, "brokenRate": None},
        "yesterdayLimitUp": [],
        "yesterdayLimitDown": [],
        "yesterdayPerformance": {},
        "errors": [],
    }
    try:
        query = urllib.parse.urlencode({
            "pn": 1, "pz": 6000, "po": 1, "np": 1, "fltt": 2,
            "invt": 2, "fid": "f3",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f12,f14,f3",
        })
        payload = fetch_json("https://push2.eastmoney.com/api/qt/clist/get?{}".format(query))
        data = payload.get("data") or {}
        items = data.get("diff") or []
        if isinstance(items, dict):
            items = list(items.values())
        changes = []
        for item in items:
            try:
                value = float(item.get("f3"))
            except (TypeError, ValueError):
                continue
            changes.append(value)
            code = item.get("f12")
            if code:
                current_changes[str(code)] = value
        result["breadth"] = {
            "up": sum(1 for value in changes if value > 0),
            "down": sum(1 for value in changes if value < 0),
            "flat": sum(1 for value in changes if value == 0),
            "total": data.get("total", len(changes)),
        }
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
        result["errors"].append({"source": "breadth", "error": str(exc)[:160]})

    pools = [
        ("limitUpCount", "getTopicZTPool"),
        ("limitDownCount", "getTopicDTPool"),
        ("brokenCount", "getTopicZBPool"),
    ]
    for key, endpoint in pools:
        try:
            data, pool = eastmoney_list(endpoint, {
                "ut": "7eea3edcaed734bea9cbfc24409ed989",
                "dpt": "wz.ztzt", "Pageindex": 0, "pagesize": 1000,
                "sort": "fbt:asc", "date": day,
            })
            result["pools"][key] = data.get("tc", len(pool))
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
            result["errors"].append({"source": key, "error": str(exc)[:160]})
    limit_up = result["pools"]["limitUpCount"]
    broken = result["pools"]["brokenCount"]
    if limit_up is not None and broken is not None and int(limit_up) + int(broken):
        result["pools"]["brokenRate"] = round(int(broken) / (int(limit_up) + int(broken)) * 100, 2)

    yesterday_specs = [
        ("yesterdayLimitUp", "getYesterdayZTPool", "up"),
    ]
    for key, endpoint, group in yesterday_specs:
        try:
            data, pool = eastmoney_list(endpoint, {
                "ut": "7eea3edcaed734bea9cbfc24409ed989",
                "dpt": "wz.ztzt", "Pageindex": 0, "pagesize": 1000,
                "sort": "zdp:desc", "date": day,
            })
            stocks = [parse_pool_stock(item) for item in pool]
            result[key] = stocks
            valid = [item["changePercent"] for item in stocks if item["changePercent"] is not None]
            result["yesterdayPerformance"][group] = {
                "count": data.get("tc", len(stocks)),
                "avgChangePercent": round(sum(valid) / len(valid), 2) if valid else None,
                "positiveCount": sum(1 for value in valid if value > 0),
                "negativeCount": sum(1 for value in valid if value < 0),
            }
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
            result["errors"].append({"source": key, "error": str(exc)[:160]})

    # Yesterday's limit-down cohort has no dedicated Eastmoney performance pool.
    # Find the most recent prior session, then apply today's all-stock quote changes.
    try:
        prior_pool = []
        prior_date = None
        for offset in range(1, 11):
            candidate = (dt.datetime.strptime(day, "%Y%m%d") - dt.timedelta(days=offset)).strftime("%Y%m%d")
            prior_data, prior_up_pool = eastmoney_list("getTopicZTPool", {
                "ut": "7eea3edcaed734bea9cbfc24409ed989", "dpt": "wz.ztzt",
                "Pageindex": 0, "pagesize": 1000, "sort": "fbt:asc", "date": candidate,
            })
            if int(prior_data.get("tc", len(prior_up_pool)) or 0) > 0:
                prior_date = candidate
                _, prior_pool = eastmoney_list("getTopicDTPool", {
                    "ut": "7eea3edcaed734bea9cbfc24409ed989", "dpt": "wz.ztzt",
                    "Pageindex": 0, "pagesize": 1000, "sort": "fbt:asc", "date": candidate,
                })
                break
        stocks = [parse_pool_stock(item) for item in prior_pool]
        for stock in stocks:
            stock["changePercent"] = current_changes.get(stock["symbol"])
        result["yesterdayLimitDown"] = stocks
        valid = [stock["changePercent"] for stock in stocks if stock["changePercent"] is not None]
        result["yesterdayPerformance"]["down"] = {
            "count": len(stocks),
            "avgChangePercent": round(sum(valid) / len(valid), 2) if valid else None,
            "positiveCount": sum(1 for value in valid if value > 0),
            "negativeCount": sum(1 for value in valid if value < 0),
        }
        if prior_date:
            result["yesterdayDate"] = "{}-{}-{}".format(prior_date[:4], prior_date[4:6], prior_date[6:8])
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
        result["errors"].append({"source": "yesterdayLimitDown", "error": str(exc)[:160]})
    try:
        if fetch_ths_emotion_pools:
            ths = fetch_ths_emotion_pools(day)
            up = ths["pools"]["limitUp"]
            down = ths["pools"]["limitDown"]
            broken = ths["pools"]["broken"]
            result["pools"].update({
                "limitUpCount": len(up),
                "limitDownCount": len(down),
                "brokenCount": len(broken),
            })
            if len(up) + len(broken):
                result["pools"]["brokenRate"] = round(len(broken) / (len(up) + len(broken)) * 100, 2)
            result["poolProvider"] = "Tonghuashun public data endpoint"
            result["tradeDate"] = "{}-{}-{}".format(
                ths["tradeDate"][:4], ths["tradeDate"][4:6], ths["tradeDate"][6:8]
            ) if len(ths["tradeDate"]) == 8 else ths["tradeDate"]
        else:
            result["poolProvider"] = "Eastmoney public endpoints (THS unavailable)"
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
        result["errors"].append({"source": "tonghuashun_pools", "error": str(exc)[:160]})
        result["poolProvider"] = "Eastmoney public endpoints (THS unavailable)"
    result["breadthProvider"] = "Eastmoney public quote endpoint"
    result["yesterdayPerformanceProvider"] = "Eastmoney public quote endpoint"
    return result

def build_snapshot(watchlist=WATCHLIST, fetcher=fetch_quote, pause=0.35):
    quotes, errors = [], []
    for symbol, market, category in watchlist:
        try:
            if market == "A股" and fetcher is fetch_quote and fetch_ths_quote:
                quotes.append(fetch_ths_quote(symbol, market, category))
            else:
                quotes.append(fetcher(symbol, market, category))
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, IndexError, json.JSONDecodeError) as exc:
            errors.append({"symbol": symbol, "error": str(exc)[:180]})
        if pause:
            time.sleep(pause)
    try:
        emotion = fetch_emotion()
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
        emotion = {"errors": [{"source": "emotion", "error": str(exc)[:160]}]}
    return {
        "updatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider": "A股行情/涨跌停：同花顺；涨跌家数/昨日表现：东方财富；美股：Yahoo Finance",
        "providers": {
            "A股行情": "Tonghuashun public K-line endpoint",
            "A股涨跌停/炸板": "Tonghuashun public data endpoint",
            "A股涨跌家数及昨日表现": "Eastmoney public quote endpoints",
            "美股行情": "Yahoo Finance",
        },
        "intervalMinutes": 5,
        "quotes": quotes,
        "emotion": emotion,
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
