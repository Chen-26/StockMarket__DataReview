const WATCHLIST = [
  ["^GSPC", "����", "����ָ��"],
  ["^IXIC", "����", "����ָ��"],
  ["^DJI", "����", "����ָ��"],
  ["000001.SS", "A��", "A��ָ��"],
  ["000300.SS", "A��", "A��ָ��"],
  ["399001.SZ", "A��", "A��ָ��"],
  ["399006.SZ", "A��", "A��ָ��"],
  ["600519.SS", "A��", "A�ɸ���"],
  ["300750.SZ", "A��", "A�ɸ���"],
  ["AAPL", "����", "���ɸ���"],
  ["NVDA", "����", "���ɸ���"],
  ["TSLA", "����", "���ɸ���"],
];

async function fetchQuote([symbol, market, category]) {
  const endpoint = "https://query1.finance.yahoo.com/v8/finance/chart/" +
    encodeURIComponent(symbol) + "?range=1d&interval=1m&includePrePost=false";
  const response = await fetch(endpoint, {
    headers: {
      "Accept": "application/json",
      "User-Agent": "Mozilla/5.0 (compatible; MarketReview/1.0)",
    },
  });
  if (!response.ok) throw new Error("upstream returned " + response.status);

  const payload = await response.json();
  const result = payload.chart && payload.chart.result && payload.chart.result[0];
  if (!result) throw new Error("empty chart response");

  const meta = result.meta || {};
  const quote = (result.indicators && result.indicators.quote && result.indicators.quote[0]) || {};
  const closes = (quote.close || []).filter((value) => typeof value === "number");
  const price = meta.regularMarketPrice ?? closes[closes.length - 1] ?? null;
  const previous = meta.chartPreviousClose ?? meta.previousClose ?? null;
  if (price === null) throw new Error("no recent price");

  const change = previous === null ? null : price - previous;
  const volumeValues = quote.volume || [];
  let volume = null;
  for (let i = volumeValues.length - 1; i >= 0; i -= 1) {
    if (typeof volumeValues[i] === "number") {
      volume = volumeValues[i];
      break;
    }
  }

  return {
    symbol,
    name: meta.longName || meta.shortName || symbol,
    market,
    category,
    currency: meta.currency || null,
    price,
    previousClose: previous,
    change,
    changePercent: previous ? (change / previous) * 100 : null,
    volume,
    marketTime: meta.regularMarketTime
      ? new Date(meta.regularMarketTime * 1000).toISOString()
      : null,
    sparkline: closes.slice(-40),
  };
}

export async function onRequest(context) {
  const cache = caches.default;
  const cacheKey = new Request(new URL("/api/quotes", context.request.url).toString());
  const cached = await cache.match(cacheKey);
  if (cached) return cached;

  const results = await Promise.allSettled(WATCHLIST.map(fetchQuote));
  const quotes = results.filter((result) => result.status === "fulfilled").map((result) => result.value);
  const errors = results.filter((result) => result.status === "rejected").length;
  if (!quotes.length) {
    return Response.json({ error: "����Դ��ʱ������", quotes: [] }, { status: 502 });
  }

  const response = Response.json({
    updatedAt: new Date().toISOString(),
    provider: "Yahoo Finance chart �� 1m",
    quotes,
    unavailable: errors,
  }, {
    headers: { "Cache-Control": "public, max-age=30, s-maxage=90" },
  });
  context.waitUntil(cache.put(cacheKey, response.clone()));
  return response;
}

