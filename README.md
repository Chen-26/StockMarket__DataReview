# 市场复盘看板

深色响应式 A 股 / 美股复盘网页。可直接打开 `index.html` 预览布局和交互；本地文件模式显示内置预览行情。GitHub Pages 部署后，网页读取 Actions 生成的行情快照。

## 页面内容

- A 股、美股通过顶部按钮单独切换，分别展示主要指数和代表标的。
- 名称/代码搜索；每个板块可筛选全部、指数或个股。
- 每日市场判断、交易复盘和下一步计划自动保存在当前浏览器。
- 工作日由 GitHub Actions 每 5 分钟抓取一次快照；网页每分钟检查一次。GitHub 可能延迟定时任务，行情源也可能延迟或不可用。

## GitHub Pages 发布

仓库需保持公开（GitHub Free 的 Pages 条件）。进入仓库 **Settings → Pages**，将 **Build and deployment → Source** 设为 **GitHub Actions**。保存后到 **Actions → Publish market review → Run workflow** 触发首次发布。之后代码 push 会自动发布；工作日定时任务也会刷新行情并部署新快照。

预期地址：<https://chen-26.github.io/StockMarket__DataReview/>。网页公开访问，仓库本身也公开；笔记只保存在当前浏览器，不会上传。

## 调整关注列表

在 `scripts/fetch_quotes.py` 的 `WATCHLIST` 修改标的代码。Yahoo Finance 代码常见格式：沪市 `.SS`、深市 `.SZ`。若添加新标的，再到 `index.html` 补充展示名称。

## 数据说明

行情通过 Yahoo Finance 图表接口获取。该接口不是有实时 SLA 的公开行情 API，可能延迟、限流或不可用；看板仅用于复盘参考，不构成投资建议。

## 验证

需要 Node.js 20+ 和 Python 3。在项目目录运行 `node tests/smoke.cjs` 与 `python -m unittest discover -s tests -p "test_*.py"`。
