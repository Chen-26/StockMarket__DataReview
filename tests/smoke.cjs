const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync("index.html", "utf8");
const inlineScript = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(inlineScript, "dashboard script exists");
new vm.Script(inlineScript[1], { filename: "index.html:inline-script" });
const quoteFunctionSource = fs.readFileSync("functions/api/quotes.js", "utf8");

const handlers = new Map();
const elements = new Map();
function element(id, dataset = {}) {
  if (elements.has(id)) return elements.get(id);
  const classes = new Set();
  const value = {
    id,
    dataset,
    value: "",
    textContent: "",
    innerHTML: "",
    style: {},
    disabled: false,
    classList: {
      add(name) { classes.add(name); },
      remove(name) { classes.delete(name); },
      contains(name) { return classes.has(name); },
      toggle(name, force) {
        const add = force === undefined ? !classes.has(name) : Boolean(force);
        if (add) classes.add(name);
        else classes.delete(name);
        return add;
      },
    },
    addEventListener(type, callback) {
      handlers.set(id + ":" + type, callback);
    },
  };
  elements.set(id, value);
  return value;
}

const filters = [
  ["cn", "all"], ["cn", "index"], ["cn", "stock"],
  ["us", "all"], ["us", "index"], ["us", "stock"],
].map(([market, filter], i) => element("filter-" + i, { market, filter }));
const data = {
  updatedAt: "2026-11-27T14:00:00Z",
  provider: "smoke fixture",
  quotes: [
    { symbol: "000001.SS", name: "��ָ֤��", market: "A��", category: "A��ָ��", price: 3300, changePercent: 0.5, sparkline: [3290, 3300] },
    { symbol: "600519.SS", name: "����ę́", market: "A��", category: "A�ɸ���", price: 1500, changePercent: -0.4, sparkline: [1510, 1500] },
    { symbol: "^GSPC", name: "S&P 500", market: "����", category: "����ָ��", price: 5900, changePercent: 0.2, sparkline: [5890, 5900] },
    { symbol: "NVDA", name: "NVIDIA", market: "����", category: "���ɸ���", price: 140, changePercent: 1.2, sparkline: [138, 140] },
  ],
};
const storage = new Map();
const context = {
  document: {
    getElementById: element,
    querySelectorAll(selector) {
      if (selector === ".filter") return filters;
      const match = selector.match(/\.filter\[data-market="(cn|us)"\]/);
      return match ? filters.filter((item) => item.dataset.market === match[1]) : [];
    },
  },
  localStorage: {
    getItem(key) { return storage.get(key) || null; },
    setItem(key, value) { storage.set(key, value); },
    removeItem(key) { storage.delete(key); },
  },
  fetch: async () => ({ ok: true, json: async () => data }),
  setInterval() { return 1; },
  setTimeout(callback) { callback(); return 1; },
  clearTimeout() {},
  confirm: () => true,
  Date,
  Promise,
  Number,
  String,
  Math,
  JSON,
  isFinite,
};
vm.runInNewContext(inlineScript[1], context, { filename: "dashboard-smoke" });

function fire(id, type) {
  const callback = handlers.get(id + ":" + type);
  assert.ok(callback, "handler registered for " + id + ":" + type);
  callback.call(element(id));
}

async function main() {
  await new Promise((resolve) => setImmediate(resolve));
  assert.match(element("cnRows").innerHTML, /600519\.SS/, "A-share table renders");
  assert.match(element("usRows").innerHTML, /NVDA/, "US table renders");

  fire("filter-1", "click");
  assert.match(element("cnRows").innerHTML, /000001\.SS/, "index filter keeps A-share index");
  assert.doesNotMatch(element("cnRows").innerHTML, /600519\.SS/, "index filter hides A-share stock");

  fire("filter-5", "click");
  assert.match(element("usRows").innerHTML, /NVDA/, "stock filter keeps US stock");
  assert.doesNotMatch(element("usRows").innerHTML, /\^GSPC/, "stock filter hides US index");

  element("search").value = "NVDA";
  fire("search", "input");
  assert.match(element("usRows").innerHTML, /NVDA/, "search finds matching symbol");
  assert.match(element("cnRows").innerHTML, /û��ƥ��ı��/, "search filters other market");

  element("marketNote").value = "��¼�г�����";
  fire("marketNote", "input");
  const noteKey = "market-review-" + new Date().toLocaleDateString("sv-SE");
  assert.equal(JSON.parse(storage.get(noteKey)).marketNote, "��¼�г�����", "notes autosave locally");

  fire("refresh", "click");
  await new Promise((resolve) => setImmediate(resolve));
  assert.match(element("status").innerHTML, /����ӿ�������/, "manual refresh keeps quote connection");

  element("search").value = "";
  fire("search", "input");
  context.fetch = async () => { throw new Error("local file has no API route"); };
  fire("refresh", "click");
  await new Promise((resolve) => setImmediate(resolve));
  assert.match(element("status").innerHTML, /����Ԥ������/, "offline mode activates local preview data");
  assert.match(element("cnRows").innerHTML, /000001\.SS/, "local preview remains usable without API");

  fire("clearNotes", "click");
  assert.equal(storage.has(noteKey), false, "clear action removes today's local note");

  const originalFetch = global.fetch;
  const originalCaches = global.caches;
  const cachedWrites = [];
  global.fetch = async () => new Response(JSON.stringify({ chart: { result: [{
    meta: { symbol: "MOCK", longName: "Mock Security", regularMarketPrice: 101, chartPreviousClose: 100, currency: "USD", regularMarketTime: 1795791600 },
    indicators: { quote: [{ close: [99, 100, 101], volume: [10, 20, 30] }] },
  }] } }), { status: 200, headers: { "Content-Type": "application/json" } });
  global.caches = { default: {
    match: async () => undefined,
    put: async (_key, response) => cachedWrites.push(await response.json()),
  } };
  try {
    const moduleUrl = "data:text/javascript;base64," + Buffer.from(quoteFunctionSource).toString("base64");
    const quoteModule = await import(moduleUrl);
    const pending = [];
    const response = await quoteModule.onRequest({
      request: new Request("https://review.pages.dev/api/quotes"),
      waitUntil: (promise) => pending.push(promise),
    });
    const body = await response.json();
    assert.equal(response.status, 200, "quote function returns success with upstream data");
    assert.equal(body.quotes.length, 12, "quote function returns configured symbols");
    assert.equal(body.quotes[0].price, 101, "quote function parses latest price");
    assert.equal(body.quotes[0].changePercent, 1, "quote function calculates change percent");
    await Promise.all(pending);
    assert.equal(cachedWrites.length, 1, "quote function writes edge cache");
  } finally {
    global.fetch = originalFetch;
    if (originalCaches === undefined) delete global.caches;
    else global.caches = originalCaches;
  }
  console.log("Smoke passed: market rendering, filters, search, local notes, refresh, clear, and quote API.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

