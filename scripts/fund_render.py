# -*- coding: utf-8 -*-
"""基金净值/重仓追踪渲染器 — 读 data_fund.json 写 fund.html（白底黑字红涨）。"""
import json, os, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DP = os.path.abspath(os.path.join(HERE, "..", "data_fund.json"))
OP = os.path.abspath(os.path.join(HERE, "..", "fund.html"))


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


def tag_cls(t):
    return "bg-up" if "持有" in t else "bg-gy"


def fund_rows(funds):
    return "".join(
        '<tr><td class="nm">%s</td><td><span class="badge %s">%s</span></td>'
        '<td class="num mono">%s</td><td class="num mono %s">%s</td>'
        '<td class="num mono %s">%s</td></tr>'
        % (esc(f["name"]), tag_cls(f["tag"]), esc(f["tag"]),
           ("%.4f" % f["nav"]) if f["nav"] else "—",
           cls(f["chg"]), pct(f["chg"]),
           cls(f["y1"]), (pct(f["y1"]) if f["y1"] else "—"))
        for f in funds)


def render(d):
    funds = d.get("funds", [])
    hold = [f for f in funds if "持有" in f["tag"]]
    watch = [f for f in funds if "持有" not in f["tag"]]
    hn = "、".join("<b>%s</b>（%s）" % (esc(f["name"]), pct(f["chg"])) for f in hold) or "—"
    verdict = ("重点持有：%s。基金净值每日更新，关注「持有」标签为你的实仓，"
               "「关注」为常看宽基/避险标的，便于一眼掌握整体权益仓位的当日表现。"
               % hn)
    tmpl = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>基金净值追踪 · @@DATE_CN@@</title>
<style>@@CSS@@</style>
</head>
<body>
<header>
  <div class="wrap">
    <span class="tag">基金 · 日更</span>
    <h1>基金净值 / 重仓追踪 <span class="em">· 你的仓位</span></h1>
    <div class="sub">持有 + 关注基金 净值 / 涨跌 ｜ <b>@@DATE_CN@@</b></div>
  </div>
</header>
<div class="wrap">
  <div class="verdict"><div class="t">今日持仓</div><p>@@VERDICT@@</p></div>

  <section>
    <h2><span class="n">1</span>追踪基金</h2>
    <div class="h2sub">「持有」=你的实仓；「关注」=常看标的</div>
    <div class="card">
      <table>
        <thead><tr><th>基金</th><th>标签</th><th class="num">单位净值</th><th class="num">当日</th><th class="num">近1年</th></tr></thead>
        <tbody>@@ROWS@@</tbody>
      </table>
    </div>
  </section>

  <footer>
    <b>数据来源：</b>东方财富公开行情接口（基金净值）｜数据截至 <b>@@DATE_CN@@</b>｜报告生成 @@GEN@@
    <div class="disc"><b>说明与免责：</b>追踪列表为固定关注池（可在 fund_fetch.py 的 TRACK 中增删）。
    近1年字段以接口返回为准。「持有」标签仅用于你本人区分，不构成任何投资建议。</div>
  </footer>
</div>
</body>
</html>"""
    return (tmpl.replace("@@CSS@@", load_css()).replace("@@DATE_CN@@", date_cn(d.get("date", "")))
            .replace("@@VERDICT@@", verdict).replace("@@ROWS@@", fund_rows(funds))
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
