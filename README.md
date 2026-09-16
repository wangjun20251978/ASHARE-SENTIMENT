# A股每日复盘产品矩阵 · 自动更新

单文件 HTML · 白底黑字红涨（涨=红 / 跌=灰，不使用绿色）· 工作日 16:30 自动更新

**总览导航（默认首页）：** https://wangjun20251978.github.io/ASHARE-SENTIMENT/
**情绪复盘页：** https://wangjun20251978.github.io/ASHARE-SENTIMENT/sentiment.html
**产品手册（5 部分）：** 见仓库 `docs/` 目录（01-总览与导航 / 02-情绪与主线复盘 / 03-资金面 / 04-资产估值转债 / 05-标的研究打新运维）

---

## 这套矩阵是什么

同一套「数据驱动 + 单页 HTML + 自动日更」打法，覆盖 A 股复盘的不同切面。每个报告独立成页，统一皮肤，
工作日 16:30（北京时间）由 GitHub Actions 统一抓取、渲染、部署。

> 注：原计划含「ETF 每日轮动信号」，因你已有 ETF-DASHBOARD2006 三因子看板（同类重复），已砍掉。
> 现共 8 个报告（含原情绪页）。

| # | 报告 | 页面 | 数据源 | 看点 |
|---|---|---|---|---|
| 0 | A股主线与情绪复盘 | sentiment.html | 东财行情 | 板块强弱 / 涨停梯队 / 情绪温度 / 主线识别 |
| 2 | 主力资金净流入榜 | fundflow.html | 东财板块+个股资金流 | 行业 / 概念 / 个股 主力净流入与净流出 |
| 3 | 龙虎榜席位动向 | lhb.html | 东财数据中心 | 机构 / 游资 主动买卖方向 |
| 4 | 大类资产夜盘温度计 | global.html | 东财外盘 | 美股 / 港股 / 日经 / 商品 / 外汇 / 债券 |
| 5 | 指数估值分位看板 | valuation.html | 东财指数行情 | 主要宽基 点位 / 强弱 / 定性估值带 |
| 6 | 新股 / 次新复盘 | ipo.html | 东财概念板 | 近端次新强度（情绪先锋） |
| 7 | 转债市场温度计 | bond.html | 东财可转债 | 等权估值 / 双低池 / 涨幅榜 |
| 8 | 基金净值 / 重仓追踪 | fund.html | 东财 ETF行情 + 基金净值 | 持有 + 关注基金 净值 / 涨跌 |

## 两个数据源说明（重要）

- **龙虎榜（#3）**：依赖东方财富**数据中心**接口，本沙箱环境出口被拦截，抓取失败时页面显示「数据暂缺」，
  **日更任务运行于海外服务器时通常可正常获取**（次日 16:30 自动补齐）。
- **指数估值分位（#5）**：实时 PE/PB 历史分位接口在本环境不稳，故以「近期 PE 参考区间 + 定性结论」呈现，
  涨跌幅为每日真实更新；估值带为定性参考，非精确历史分位。

## 自动更新

`.github/workflows/daily.yml` 每个交易日（周一至周五）北京时间 **16:30** 自动运行：

```
抓取 8 份数据 → 生成 8 个页面 → 校验产出 → 提交 → GitHub Pages 自动部署
```

也可在 Actions 页面手动触发（`workflow_dispatch`），支持指定日期回补。

## 本地使用

```bash
python scripts/fetch_data.py      # 情绪页数据 → data.json
python scripts/flow_fetch.py      # 资金榜数据 → data_flow.json
python scripts/lhb_fetch.py       # 龙虎榜数据 → data_lhb.json（可能空）
python scripts/global_fetch.py    # 大类资产 → data_global.json
python scripts/val_fetch.py       # 估值 → data_val.json
python scripts/ipo_fetch.py       # 次新 → data_ipo.json
python scripts/bond_fetch.py      # 转债 → data_bond.json
python scripts/fund_fetch.py      # 基金 → data_fund.json

python scripts/render_report.py   # → index.html
python scripts/flow_render.py     # → fundflow.html
python scripts/lhb_render.py      # → lhb.html
python scripts/global_render.py   # → global.html
python scripts/val_render.py      # → valuation.html
python scripts/ipo_render.py      # → ipo.html
python scripts/bond_render.py     # → bond.html
python scripts/fund_render.py     # → fund.html
```

所有脚本纯 Python 标准库实现，**无需安装任何第三方依赖**。

---

**免责声明**：本项目为公开市场数据的客观整理与结构化呈现，所有判定均为框架化推演，不构成任何证券投资咨询或投资建议。投资有风险，决策须谨慎。
