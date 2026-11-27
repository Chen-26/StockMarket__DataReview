const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync("index.html", "utf8");
const inlineScript = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(inlineScript, "dashboard script exists");
new vm.Script(inlineScript[1], { filename: "index.html:inline-script" });

const handlers = new Map();
const elements = new Map();
function element(id, dataset = {}) {
  if (elements.has(id)) return elements.get(id);
  const classes = new Set();
  const value = {
    id, dataset, value: "", textContent: "", innerHTML: "", style: {}, disabled: false, hidden: false, attributes: {},
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
    setAttribute(name, item) { this.attributes[name] = item; },
    addEventListener(type, callback) { handlers.set(id + ":" + type, callback); },
  };
  elements.set(id, value);
  return value;
}

const filters = [
  ["cn", "all"], ["cn", "index"], ["cn", "stock"],
  ["us", "all"], ["us", "index"], ["us", "stock"],
].map(([market, filter], i) => element("filter-" + i, { market, filter }));
const marketTabs = [
  element("tab-cn", { marketTab: "cn" }),
  element("tab-us", { marketTab: "us" }),
];
const marketPanels = [
  element("cnPanel", { marketView: "cn" }),
  element("usPanel", { marketView: "us" }),
];
const cnSubTabs = [
  element("cn-tab-market", { cnTab: "market" }),
  element("cn-tab-emotion", { cnTab: "emotion" }),
];
const cnSubViews = [
  element("cn-market-view", { cnView: "market" }),
  element("cn-emotion-view", { cnView: "emotion" }),
];
const emotionGroups = [
  element("yesterday-up", { yesterdayGroup: "up" }),
  element("yesterday-down", { yesterdayGroup: "down" }),
];
marketTabs[0].classList.add("active");
marketTabs[0].setAttribute("aria-selected", "true");
marketTabs[1].setAttribute("aria-selected", "false");
marketPanels[1].hidden = true;
const data = {
  updatedAt: "2026-11-27T14:00:00Z",
  provider: "smoke fixture",
  emotion: {
    tradeDate: "2026-11-27", yesterdayDate: "2026-11-26",
    breadth: { up: 2500, down: 1700, flat: 150, total: 4350 },
    pools: { limitUpCount: 60, limitDownCount: 8, brokenCount: 20, brokenRate: 25 },
    yesterdayLimitUp: [{ symbol: "600001", name: "Alpha", changePercent: 4.2 }],
    yesterdayLimitDown: [{ symbol: "600002", name: "Beta", changePercent: -2.1 }],
    yesterdayPerformance: { up: { avgChangePercent: 1.5, positiveCount: 1, negativeCount: 0 }, down: { avgChangePercent: -2.1, positiveCount: 0, negativeCount: 1 } },
  },
  quotes: [
    { symbol: "000001.SS", name: "上证指数", market: "A股", category: "A股指数", price: 3300, changePercent: 0.5, sparkline: [3290, 3300] },
    { symbol: "600519.SS", name: "贵州茅台", market: "A股", category: "A股个股", price: 1500, changePercent: -0.4, sparkline: [1510, 1500] },
    { symbol: "^GSPC", name: "S&P 500", market: "美股", category: "美股指数", price: 5900, changePercent: 0.2, sparkline: [5890, 5900] },
    { symbol: "NVDA", name: "NVIDIA", market: "美股", category: "美股个股", price: 140, changePercent: 1.2, sparkline: [138, 140] },
  ],
};
const historicalData = { ...data, updatedAt: "2026-11-26T14:00:00Z", emotion: { ...data.emotion, tradeDate: "2026-11-26" } };
const requestedUrls = [];
const storage = new Map();
const context = {
  document: {
    getElementById: element,
    querySelectorAll(selector) {
      if (selector === ".market-tab") return marketTabs;
      if (selector === ".market-view") return marketPanels;
      if (selector === ".cn-subtab") return cnSubTabs;
      if (selector === ".cn-subview") return cnSubViews;
      if (selector === ".emotion-group") return emotionGroups;
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
  fetch: async (url) => {
    requestedUrls.push(url);
    if (url.includes("data/history/index.json")) return { ok: true, json: async () => ({ dates: ["2026-11-26"] }) };
    if (url.includes("data/history/2026-11-26.json")) return { ok: true, json: async () => historicalData };
    if (url.includes("data/history/")) return { ok: false, json: async () => ({}) };
    return { ok: true, json: async () => data };
  },
  setInterval() { return 1; },
  setTimeout(callback) { callback(); return 1; },
  clearTimeout() {},
  confirm: () => true,
  Date, Promise, Number, String, Math, JSON, isFinite,
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
  assert.equal(element("emotionUp").textContent, "2,500", "A-share breadth renders from snapshot");
  assert.equal(element("limitUpCount").textContent, "60", "limit-up count renders from snapshot");
  assert.equal(element("brokenRate").textContent, "25.0%", "opened-limit rate renders from snapshot");
  assert.match(element("yesterdayRows").innerHTML, /600001/, "yesterday limit-up performance renders");
  assert.equal(element("tradeDate").value, "2026-11-27", "date picker defaults to snapshot trading day");
  element("tradeDate").value = "2026-11-26";
  fire("tradeDate", "change");
  await new Promise((resolve) => setImmediate(resolve));
  assert.ok(requestedUrls.some((url) => url.includes("data/history/2026-11-26.json")), "selected trading date loads archived snapshot");
  assert.equal(element("emotionDate").textContent, "2026-11-26", "historical snapshot renders its own date");
  element("tradeDate").value = "2026-11-25";
  fire("tradeDate", "change");
  assert.equal(element("tradeDate").value, "2026-11-26", "unarchived dates are rejected");
  element("tradeDate").value = "2026-11-27";
  fire("tradeDate", "change");
  await new Promise((resolve) => setImmediate(resolve));
  fire("cn-tab-emotion", "click");
  assert.equal(element("cn-market-view").hidden, true, "emotion tab hides market view");
  assert.equal(element("cn-emotion-view").hidden, false, "emotion tab shows emotion view");
  fire("yesterday-down", "click");
  assert.match(element("yesterdayRows").innerHTML, /600002/, "yesterday limit-down group switches");

  fire("tab-us", "click");
  assert.equal(element("cnPanel").hidden, true, "US tab hides A-share panel");
  assert.equal(element("usPanel").hidden, false, "US tab shows US panel");
  assert.equal(element("tab-us").attributes["aria-selected"], "true", "US tab exposes selected state");
  fire("tab-cn", "click");
  assert.equal(element("cnPanel").hidden, false, "A-share tab shows A-share panel");
  assert.equal(element("usPanel").hidden, true, "A-share tab hides US panel");

  fire("filter-1", "click");
  assert.match(element("cnRows").innerHTML, /000001\.SS/, "index filter keeps A-share index");
  assert.doesNotMatch(element("cnRows").innerHTML, /600519\.SS/, "index filter hides A-share stock");
  fire("filter-5", "click");
  assert.match(element("usRows").innerHTML, /NVDA/, "stock filter keeps US stock");
  assert.doesNotMatch(element("usRows").innerHTML, /\^GSPC/, "stock filter hides US index");

  element("search").value = "NVDA";
  fire("search", "input");
  assert.match(element("usRows").innerHTML, /NVDA/, "search finds matching symbol");
  assert.match(element("cnRows").innerHTML, /没有匹配的标的/, "search filters other market");

  element("marketNote").value = "记录市场驱动";
  fire("marketNote", "input");
  const noteKey = "market-review-" + new Date().toLocaleDateString("sv-SE");
  assert.equal(JSON.parse(storage.get(noteKey)).marketNote, "记录市场驱动", "notes autosave locally");

  fire("refresh", "click");
  await new Promise((resolve) => setImmediate(resolve));
  assert.match(element("status").innerHTML, /\u6700\u65b0\u884c\u60c5\u5feb\u7167/, "manual refresh loads quote snapshot");
  element("search").value = "";
  fire("search", "input");
  context.fetch = async () => { throw new Error("local file has no snapshot file"); };
  fire("refresh", "click");
  await new Promise((resolve) => setImmediate(resolve));
  assert.match(element("status").innerHTML, /本地预览快照/, "offline mode activates local preview");
  assert.match(element("cnRows").innerHTML, /000001\.SS/, "local preview remains usable offline");

  fire("clearNotes", "click");
  assert.equal(storage.has(noteKey), false, "clear action removes today's local note");
  console.log("Smoke passed: rendering, filters, search, notes, refresh, and offline preview.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
