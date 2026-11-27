# 市场复盘看板

深色响应式 A 股 / 美股复盘网页。可直接打开 `index.html` 预览布局和交互；本地文件模式显示内置预览行情。GitHub Pages 部署后，网页读取 Actions 生成的行情快照。

## 页面内容

- A 股、美股通过顶部按钮单独切换，分别展示主要指数和代表标的。
- A 股“大盘”展示上证指数、深证成指、创业板指、科创50。
- 名称/代码搜索；每个板块可筛选全部、指数或个股。
- 每日市场判断、交易复盘和下一步计划自动保存在当前浏览器。
- 工作日由 GitHub Actions 每 5 分钟抓取一次快照；网页每分钟检查一次。GitHub 可能延迟定时任务，行情源也可能延迟或不可用。

## GitHub Pages 发布

仓库需保持公开（GitHub Free 的 Pages 条件）。进入仓库 **Settings → Pages**，将 **Build and deployment → Source** 设为 **GitHub Actions**。保存后到 **Actions → Publish market review → Run workflow** 触发首次发布。之后代码 push 会自动发布；工作日定时任务也会刷新行情并部署新快照。

预期地址：<https://chen-26.github.io/StockMarket__DataReview/>。网页公开访问，仓库本身也公开；笔记只保存在当前浏览器，不会上传。

## 调整关注列表

在 `scripts/fetch_quotes.py` 的 `WATCHLIST` 修改标的代码。Yahoo Finance 代码常见格式：沪市 `.SS`、深市 `.SZ`。若添加新标的，再到 `index.html` 补充展示名称。

## 数据说明

行情源按市场和指标区分：A 股指数/关注标的日 K 与涨跌停、跌停、炸板股池使用同花顺公开网页接口；涨跌家数和昨日涨跌停股表现仍使用东方财富公开接口；美股使用 Yahoo Finance 图表接口。当前接入的同花顺地址是网页数据接口，不是 iFinD 正式 API；接口可能变化、延迟或触发访问限制。看板会显示最近可用交易日，接口失效时会记录错误，不应将旧快照当成实时行情；数据仅用于复盘参考，不构成投资建议。

## 验证

需要 Node.js 20+ 和 Python 3。在项目目录运行 `node tests/smoke.cjs` 与 `python -m unittest discover -s tests -p "test_*.py"`。


## 历史交易日

- 页面顶部可按日期查看当日行情和情绪快照。
- GitHub Actions 在交易日 15:05 之后保存每日快照，目前最多保留 756 个交易日。
- 这次功能上线后才开始累积存档；选择尚无存档的日期会提示没有数据。
