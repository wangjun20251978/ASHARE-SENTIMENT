# -*- coding: utf-8 -*-
"""ETF 每日轮动信号渲染器 — 读 data_etf.json 写 etf.html（白底黑字红涨）。"""
import json, os, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DP = os.path.abspath(os.path.join(HERE, "..", "data_etf.json"))
OP = os.path.abspath(os.path.join(HERE, "..", "etf.html"))


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def pct(v):
    return "%.2f%%" % v


def yi(v):
    if abs(v) >= 1e8:
        return "%.2f亿" % (v / 1e8)
    return "%.0f万" % (v / 1e4)


def cls(v):
    return "c-up" if v > 0 else ("c-dn" if v < 0 else "")


def load_css():
    p = os.path.join(HERE, "style.css")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read()
    return ""


def date_cn(d):
    if len(d) == 8:
        return "%s年%s月%s日" % (d[:4], d[4:6], d[6:8])
    return d


def render(d):
    rows = d["rows"]
    # 分类概览
    cata_order = ["宽基", "行业", "海外", "商品", "债券"]
    cata_html = "".join(
        '<div class="mbox"><div class="mv %s">%s</div><div class="ml">%s<br>（%d只）</div></div>'
        % (cls(d["cata"][c]["avg"]), pct(d["cata"][c]["avg"]), c, d["cata"][c]["n"])
        for c in cata_order if c in d["cata"])

    # Top 信号表
    def signal_row(r):
        tag = "bg-up" if r["score"] >= 60 else ("bg-ac" if r["score"] >= 45 else "bg-gy")
        label = "强关注" if r["score"] >= 60 else ("关注" if r["score"] >= 45 else "中性")
        return ('<tr><td class="nm">%s <span class="badge bg-gy">%s</span></td>'
                '<td class="num mono %s">%s</td>'
                '<td class="num mono %s">%s</td>'
                '<td class="num mono %s">%s</td>'
                '<td class="num mono">%.1f</td>'
                '<td><span class="badge %s">%s</span></td></tr>'
                % (esc(r["name"]), esc(r["cata"]),
                   cls(r["pct"]), pct(r["pct"]),
                   cls(r["mainflow"]), yi(r["mainflow"]),
                   cls(r["mainflow_pct"]), pct(r["mainflow_pct"]),
                   r["score"], tag, label))
    top_html = "".join(signal_row(r) for r in d["top"])
    bot_html = "".join(
        '<tr><td class="nm">%s <span class="badge bg-gy">%s</span></td>'
        '<td class="num mono %s">%s</td><td class="num mono %s">%s</td>'
        '<td class="num mono">%.1f</td></tr>'
        % (esc(r["name"]), esc(r["cata"]), cls(r["pct"]), pct(r["pct"]),
           cls(r["mainflow"]), yi(r["mainflow"]), r["score"])
        for r in d["bot"])

    # 最强/最弱
    strongest = max(rows, key=lambda x: x["score"]) if rows else {}
    weakest = min(rows, key=lambda x: x["score"]) if rows else {}

    verdict = ("今日 ETF 池 %d 只中 <b>%d 涨 / %d 跌</b>，整体主力净流入 <b>%s</b>。"
               "综合动能最强为 <b class='c-up'>%s</b>（%.1f分），最弱为 <b>%s</b>（%.1f分）——"
               "分数越高，代表「当日涨幅 + 主力净流入 + 主力占比」三维合力越强。"
               % (d["count"], d["up"], d["dn"], yi(d["total_flow"]),
                  esc(strongest.get("name", "")), strongest.get("score", 0),
                  esc(weakest.get("name", "")), weakest.get("score", 0)))

    tmpl = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ETF 每日轮动信号 · @@DATE_CN@@</title>
<style>@@CSS@@</style>
</head>
<body>
<header>
  <div class="wrap">
    <span class="tag">ETF · 三因子日更</span>
    <h1>ETF 每日轮动信号 <span class="em">· 动能 + 资金</span></h1>
    <div class="sub">当日动能 / 主力净流入 / 主力净流入占比 —— 三维合力打分排序 ｜ <b>@@DATE_CN@@</b></div>
  </div>
</header>
<div class="wrap">

  <div class="verdict">
    <div class="t">今日总览</div>
    <p>@@VERDICT@@</p>
  </div>

  <section>
    <h2><span class="n">1</span>分类表现：哪类资产在动</h2>
    <div class="h2sub">宽基 / 行业 / 海外 / 商品 / 债券 平均涨跌对照</div>
    <div class="mgrid">@@CATA@@</div>
  </section>

  <section>
    <h2><span class="n">2</span>信号榜：综合得分 Top 12</h2>
    <div class="h2sub">得分 = 40%动能(当日%) + 30%主力净流入 + 30%主力净流入占比（组内归一化）</div>
    <div class="card">
      <table>
        <thead><tr><th>ETF</th><th class="num">当日</th><th class="num">主力净流入</th>
        <th class="num">主力占比</th><th class="num">综合分</th><th>信号</th></tr></thead>
        <tbody>@@TOP@@</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="n">3</span>风险榜：合力最弱</h2>
    <div class="h2sub">三维得分最低的方向，暂不宜追</div>
    <div class="card">
      <table>
        <thead><tr><th>ETF</th><th class="num">当日</th><th class="num">主力净流入</th><th class="num">综合分</th></tr></thead>
        <tbody>@@BOT@@</tbody>
      </table>
    </div>
  </section>

  <footer>
    <b>数据来源：</b>东方财富公开行情接口（ETF 批量行情：当日涨跌 / 主力净流入 / 主力净流入占比）｜数据截至 <b>@@DATE_CN@@ 收盘</b>｜报告生成 @@GEN@@
    <div class="disc">
      <b>免责声明：</b>本页为公开市场数据的客观整理与结构化呈现，所有「综合得分」「信号」均为基于历史数据的<b>框架化推演</b>，
      不构成任何证券投资咨询或投资建议。ETF 有净值波动与跟踪误差风险，决策须谨慎。
    </div>
  </footer>

</div>
</body>
</html>"""

    return (tmpl
            .replace("@@CSS@@", load_css())
            .replace("@@DATE_CN@@", date_cn(d.get("date", "")))
            .replace("@@VERDICT@@", verdict)
            .replace("@@CATA@@", cata_html)
            .replace("@@TOP@@", top_html)
            .replace("@@BOT@@", bot_html)
            .replace("@@GEN@@", d.get("generated", "")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DP)
    ap.add_argument("--out", default=OP)
    a = ap.parse_args()
    d = json.load(open(a.data, encoding="utf-8"))
    html = render(d)
    open(a.out, "w", encoding="utf-8").write(html)
    print("已生成: %s (%d bytes)" % (a.out, len(html.encode("utf-8"))))


if __name__ == "__main__":
    main()
