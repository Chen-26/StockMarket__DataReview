# 市场复盘看板

深色响应式 A 股 / 美股复盘网页。可直接打开 `index.html` 体验布局和交互；本地文件模式显示内置预览数据。部署到 Cloudflare Pages 后，页面会通过同域 Pages Function 获取行情。

## 页面内容

- A 股、美股分栏展示主要指数和代表标的。
- 名称/代码搜索；每个板块可筛选全部、指数或个股。
- 每日市场判断、交易复盘和下一步计划自动保存在当前浏览器。
- 网页每分钟检查行情；Function 使用边缘缓存，减少重复请求。

## Cloudflare Pages 免费部署

1. 在 Cloudflare 控制台进入 **Workers & Pages → Create application → Pages → Connect to Git**。
2. 授权 GitHub，选择私有仓库 `Chen-26/StockMarket__DataReview` 和生产分支 `main`。
3. Framework preset 选 **None**；Build command 填 `mkdir -p public && cp index.html public/index.html`；Build output directory 填 `public`。
4. 保存并部署。以后 push 到 `main` 会自动发布。

`functions/api/quotes.js` 是 Pages Function，无需 API key 或运行时环境变量。Cloudflare Pages Functions 请求会占用 Workers Free 的日请求额度；静态资源请求免费。Git 集成免费方案每月最多 500 次构建。具体额度以 Cloudflare 当前套餐说明为准。

> 注意：Cloudflare Pages 地址默认可公开访问，私有 GitHub 仓库不会自动让网页也变成私有。复盘笔记只存当前浏览器，不会上传；若需要网页访问控制，可再为站点配置 Cloudflare Access。

## 调整关注列表

在 `functions/api/quotes.js` 的 `WATCHLIST` 修改代码；若新增标的，再在 `index.html` 补充展示名称和分类。

## 核心交互冒烟测试

需要 Node.js 20 或更新版本。在项目目录执行 `node tests/smoke.cjs`，验证页面脚本、A 股/美股数据渲染、板块筛选、搜索、笔记自动保存/清空、手动刷新、本地预览回退和行情 Function 响应。

## 行情说明

行情来自 Yahoo Finance 图表接口。该接口不是有实时 SLA 的公开行情 API，可能延迟、限流或暂时不可用；页面仅供复盘参考，不构成投资建议。
