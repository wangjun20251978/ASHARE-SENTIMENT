# -*- coding: utf-8 -*-
"""主力资金净流入榜渲染器 — 读 data_flow.json 写 fundflow.html（白底黑字红涨）。"""
import json, os, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DP = os.path.abspath(os.path.join(HERE, "..", "data_flow.json"))
OP = os.path.abspath(os.path.join(HERE, "..", "fundflow.html"))


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def pct(v):
    return "%.2f%%" % v


def yi(v):
    a = abs(v)
    if a >= 1e8:
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


def board_rows(rows):
    return "".join(
        '<tr><td class="nm">%s</td><td class="num mono %s">%s</td>'
        '<td class="num mono %s">%s</td><td class="num mono %s">%s</td></tr>'
        % (esc(r["name"]), cls(r["pct"]), pct(r["pct"]),
           cls(r["mainflow"]), yi(r["mainflow"]),
           cls(r["mainflow_pct"]), pct(r["mainflow_pct"]))
        for r in rows)


def stock_rows(rows):
    return "".join(
        '<tr><td class="nm">%s <span class="badge bg-gy">%s</span></td>'
        '<td class="num mono %s">%s</td><td class="num mono %s">%s</td>'
        '<td class="num mono %s">%s</td></tr>'
        % (esc(r["name"]), esc(r["code"]), cls(r["pct"]), pct(r["pct"]),
           cls(r["mainflow"]), yi(r["mainflow"]),
           cls(r["mainflow_pct"]), pct(r["mainflow_pct"]))
        for r in rows)


def render(d):
    ind_html = board_rows(d["industry_in"])
    con_html = board_rows(d["concept_in"])
    sin_html = stock_rows(d["stock_in"])
    sout_html = stock_rows(d["stock_out"])

    top_in = d["industry_in"][0] if d["industry_in"] else {}
    verdict = ("今日主力资金最集中的行业为 <b class='c-up'>%s</b>（净流入 %s），"
               "概念方向最强 <b class='c-up'>%s</b>（净流入 %s）。"
               "个股侧，主力净流入榜首 <b>%s</b>（%s），净流出榜首 <b>%s</b>（%s）——"
               "资金净流入代表主动买入占比高，是观察「钱往哪去」的第一信号。"
               % (esc(top_in.get("name", "")), yi(top_in.get("mainflow", 0)),
                  esc(d["concept_in"][0]["name"] if d["concept_in"] else ""),
                  yi(d["concept_in"][0]["mainflow"] if d["concept_in"] else 0),
                  esc(d["stock_in"][0]["name"] if d["stock_in"] else ""),
                  yi(d["stock_in"][0]["mainflow"] if d["stock_in"] else 0),
                  esc(d["stock_out"][0]["name"] if d["stock_out"] else ""),
                  yi(d["stock_out"][0]["mainflow"] if d["stock_out"] else 0)))

    tmpl = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>主力资金净流入榜 · @@DATE_CN@@</title>
<style>@@CSS@@</style>
</head>
<body>
<header>
  <div class="wrap">
    <span class="tag">资金 · 日更</span>
    <h1>主力资金净流入榜 <span class="em">· 钱往哪去</span></h1>
    <div class="sub">行业 / 概念 / 个股 主力净流入与净流出排行 ｜ <b>@@DATE_CN@@</b></div>
  </div>
</header>
<div class="wrap">

  <div class="verdict">
    <div class="t">今日资金焦点</div>
    <p>@@VERDICT@@</p>
  </div>

  <section>
    <h2><span class="n">1</span>行业资金净流入 Top 12</h2>
    <div class="h2sub">按主力净流入排序（单位：元）</div>
    <div class="card">
      <table>
        <thead><tr><th>行业</th><th class="num">当日</th><th class="num">主力净流入</th><th class="num">主力占比</th></tr></thead>
        <tbody>@@IND@@</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="n">2</span>概念资金净流入 Top 12</h2>
    <div class="h2sub">按主力净流入排序</div>
    <div class="card">
      <table>
        <thead><tr><th>概念</th><th class="num">当日</th><th class="num">主力净流入</th><th class="num">主力占比</th></tr></thead>
        <tbody>@@CON@@</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="n">3</span>个股主力净流入 Top 20</h2>
    <div class="h2sub">沪A + 深A 主板，按主力净流入排序</div>
    <div class="card">
      <table>
        <thead><tr><th>个股</th><th class="num">当日</th><th class="num">主力净流入</th><th class="num">主力占比</th></tr></thead>
        <tbody>@@SIN@@</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="n">4</span>个股主力净流出 Top 20</h2>
    <div class="h2sub">资金出逃方向，规避参考</div>
    <div class="card">
      <table>
        <thead><tr><th>个股</th><th class="num">当日</th><th class="num">主力净流入</th><th class="num">主力占比</th></tr></thead>
        <tbody>@@SOUT@@</tbody>
      </table>
    </div>
  </section>

  <footer>
    <b>数据来源：</b>东方财富公开行情接口（板块 / 个股主力资金流）｜数据截至 <b>@@DATE_CN@@ 收盘</b>｜报告生成 @@GEN@@
    <div class="disc">
      <b>免责声明：</b>本页为公开市场数据的客观整理，主力资金流为基于逐笔成交的<b>推演口径</b>，
      不同数据源定义可能略有差异，不构成任何投资建议。仅供观察资金动向参考，决策须谨慎。
    </div>
  </footer>

</div>
</body>
</html>"""

    return (tmpl
            .replace("@@CSS@@", load_css())
            .replace("@@DATE_CN@@", date_cn(d.get("date", "")))
            .replace("@@VERDICT@@", verdict)
            .replace("@@IND@@", ind_html)
            .replace("@@CON@@", con_html)
            .replace("@@SIN@@", sin_html)
            .replace("@@SOUT@@", sout_html)
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
