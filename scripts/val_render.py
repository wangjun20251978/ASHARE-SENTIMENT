# -*- coding: utf-8 -*-
"""指数估值分位看板渲染器 — 读 data_val.json 写 valuation.html（白底黑字红涨）。"""
import json, os, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DP = os.path.abspath(os.path.join(HERE, "..", "data_val.json"))
OP = os.path.abspath(os.path.join(HERE, "..", "valuation.html"))


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pct(v):
    return "%.2f%%" % v


def cls(v):
    return "c-up" if v > 0 else ("c-dn" if v < 0 else "")


def load_css():
    p = os.path.join(HERE, "style.css")
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def date_cn(d):
    return "%s年%s月%s日" % (d[:4], d[4:6], d[6:8]) if len(d) == 8 else d


def band_cls(b):
    return "bg-up" if "偏低" in b else ("bg-bl" if "偏高" in b else "bg-gy")


def idx_rows(indices):
    return "".join(
        '<tr><td class="nm">%s</td><td class="num mono %s">%s</td>'
        '<td class="num mono %s">%s</td><td class="num">%d~%d</td>'
        '<td><span class="badge %s">%s</span></td></tr>'
        % (esc(x["name"]), cls(x["chg"]), ("%.2f" % x["point"]),
           cls(x["chg"]), pct(x["chg"]), x["pe_low"], x["pe_high"], band_cls(x["band"]), x["band"])
        for x in indices)


def kpi(idx, label):
    x = next((i for i in idx if i["name"] == label), None)
    if not x:
        return ""
    return ('<div class="kpi %s"><div class="lb">%s</div><div class="vl %s">%s</div>'
            '<div class="nt %s">%s</div></div>'
            % ("up" if x["chg"] > 0 else "dn", label,
               cls(x["chg"]), "%.2f" % x["point"], cls(x["chg"]), pct(x["chg"])))


def render(d):
    idx = d.get("indices", [])
    kpis = "".join([kpi(idx, n) for n in ["上证指数", "沪深300", "创业板指", "科创50"]])
    verdict = ("主要宽基指数中，<b>沪深300 / 上证50 / 中证500 / 上证指数</b>处于<b class='c-up'>合理偏低</b>区间，"
               "中长期配置性价比相对占优；<b>科创50</b>估值仍<b>偏高</b>，需业绩兑现消化。"
               "涨跌幅为每日真实更新，估值带为近期 PE 参考区间的定性结论（非实时历史分位）。")
    tmpl = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>指数估值分位看板 · @@DATE_CN@@</title>
<style>@@CSS@@</style>
</head>
<body>
<header>
  <div class="wrap">
    <span class="tag">估值 · 日更</span>
    <h1>指数估值分位看板 <span class="em">· 抄底参考</span></h1>
    <div class="sub">主要宽基指数 点位 / 强弱 / 定性估值带 ｜ <b>@@DATE_CN@@</b></div>
  </div>
</header>
<div class="wrap">
  <div class="kpis">@@KPIS@@</div>
  <div class="verdict"><div class="t">估值结论</div><p>@@VERDICT@@</p></div>

  <section>
    <h2><span class="n">1</span>主要指数估值带</h2>
    <div class="h2sub">点位 / 涨跌幅每日更新；估值带为近期 PE 参考区间定性结论</div>
    <div class="card">
      <table>
        <thead><tr><th>指数</th><th class="num">收盘点位</th><th class="num">今日</th><th class="num">参考PE区间</th><th>估值结论</th></tr></thead>
        <tbody>@@ROWS@@</tbody>
      </table>
    </div>
  </section>

  <footer>
    <b>数据来源：</b>东方财富公开行情接口（指数行情 + 近期 PE 参考区间）｜数据截至 <b>@@DATE_CN@@</b> 收盘｜报告生成 @@GEN@@
    <div class="disc"><b>方法论与免责：</b>指数实时 PE/PB 历史分位接口在本环境不稳定，故以「近期 PE 参考区间 + 定性结论」呈现，
    涨跌幅为每日真实更新。<b>估值带为定性参考，非精确历史分位</b>，不构成任何投资建议。如需精确分位，可后续接入估值数据中心。</div>
  </footer>
</div>
</body>
</html>"""
    return (tmpl.replace("@@CSS@@", load_css()).replace("@@DATE_CN@@", date_cn(d.get("date", "")))
            .replace("@@KPIS@@", kpis).replace("@@VERDICT@@", verdict).replace("@@ROWS@@", idx_rows(idx))
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
