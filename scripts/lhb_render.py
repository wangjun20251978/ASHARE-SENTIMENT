# -*- coding: utf-8 -*-
"""龙虎榜席位动向渲染器 — 读 data_lhb.json 写 lhb.html（白底黑字红涨）。"""
import json, os, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DP = os.path.abspath(os.path.join(HERE, "..", "data_lhb.json"))
OP = os.path.abspath(os.path.join(HERE, "..", "lhb.html"))


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def date_cn(d):
    return "%s年%s月%s日" % (d[:4], d[4:6], d[6:8]) if len(d) == 8 else d


def item_rows(items):
    return "".join(
        '<tr><td class="nm">%s <span class="badge bg-gy">%s</span></td>'
        '<td class="num mono %s">%s</td><td class="num mono %s">%s</td>'
        '<td class="num mono %s">%s</td><td>%s</td></tr>'
        % (esc(it["name"]), esc(it["code"]), cls(it["chg"]), pct(it["chg"]),
           cls(it["net"]), yi(it["net"]), cls(it["net"]), esc(it["reason"] or "—"))
        for it in items)


def render(d):
    items = d.get("items", [])
    ok = d.get("ok", False)
    if not ok or not items:
        body = ('<div class="verdict"><div class="t">数据暂缺</div>'
                '<p>龙虎榜数据源（东方财富数据中心）在本环境当前无法稳定获取，页面已生成但无数据。'
                '<b>日更任务运行于海外服务器时通常可正常拉取</b>，次日 16:30 自动更新后即可看到完整榜单。'
                '也可手动重跑 GitHub Actions 验证。</p></div>')
        rows = ""
    else:
        top = items[0]
        body = ('<div class="verdict"><div class="t">龙虎榜焦点</div>'
                '<p>当日上榜 <b>%d</b> 只，净买入榜首 <b>%s</b>（净额 %s，涨跌幅 %s）。'
                '龙虎榜反映的是机构与游资的主动买卖方向，是观察「聪明钱」动向的高频窗口。</p></div>'
                % (len(items), esc(top["name"]), yi(top["net"]), pct(top["chg"])))
        rows = item_rows(items)
    tmpl = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>龙虎榜席位动向 · @@DATE_CN@@</title>
<style>@@CSS@@</style>
</head>
<body>
<header>
  <div class="wrap">
    <span class="tag">龙虎榜 · 日更</span>
    <h1>龙虎榜席位动向 <span class="em">· 聪明钱去向</span></h1>
    <div class="sub">机构 / 游资 主动买卖 ｜ <b>@@DATE_CN@@</b></div>
  </div>
</header>
<div class="wrap">
  @@BODY@@
  <section>
    <h2><span class="n">1</span>龙虎榜净买入榜</h2>
    <div class="h2sub">按席位净买入额排序</div>
    <div class="card">
      <table>
        <thead><tr><th>个股</th><th class="num">涨跌幅</th><th class="num">席位净买入</th><th class="num">净额</th><th>上榜原因</th></tr></thead>
        <tbody>@@ROWS@@</tbody>
      </table>
    </div>
  </section>

  <footer>
    <b>数据来源：</b>东方财富数据中心（龙虎榜明细）｜数据截至 <b>@@DATE_CN@@</b>｜报告生成 @@GEN@@
    <div class="disc"><b>免责声明：</b>龙虎榜为公开披露数据，仅反映当日上榜个股的席位买卖汇总，不代表后续走势。
    游资风格波动大、风险高，仅供观察资金动向，不构成任何投资建议。</div>
  </footer>
</div>
</body>
</html>"""
    return (tmpl.replace("@@CSS@@", load_css()).replace("@@DATE_CN@@", date_cn(d.get("date", "")))
            .replace("@@BODY@@", body).replace("@@ROWS@@", rows).replace("@@GEN@@", d.get("generated", "")))


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
