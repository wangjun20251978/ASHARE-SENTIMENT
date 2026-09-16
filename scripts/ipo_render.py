# -*- coding: utf-8 -*-
"""新股/次新复盘渲染器 — 读 data_ipo.json 写 ipo.html（白底黑字红涨）。"""
import json, os, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DP = os.path.abspath(os.path.join(HERE, "..", "data_ipo.json"))
OP = os.path.abspath(os.path.join(HERE, "..", "ipo.html"))


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


def mem_rows(members):
    return "".join(
        '<tr><td class="nm">%s <span class="badge bg-gy">%s</span></td>'
        '<td class="num mono %s">%s</td></tr>'
        % (esc(m["name"]), esc(m["code"]), cls(m["chg"]), pct(m["chg"]))
        for m in members)


def render(d):
    cnt = d.get("count", 0)
    upr = (d.get("up", 0) / cnt * 100) if cnt else 0
    kpis = ('<div class="kpi %s"><div class="lb">%s 概念</div><div class="vl %s">%s</div><div class="nt">板块涨跌</div></div>'
            '<div class="kpi"><div class="lb">成分数量</div><div class="vl">%d</div><div class="nt">只</div></div>'
            '<div class="kpi %s"><div class="lb">上涨占比</div><div class="vl %s">%.0f%%</div><div class="nt">%d 涨</div></div>'
            '<div class="kpi %s"><div class="lb">均涨</div><div class="vl %s">%s</div><div class="nt">成分均值</div></div>'
            % (esc(d.get("concept_name", "")), "up" if d.get("concept_chg", 0) > 0 else "dn",
               cls(d.get("concept_chg", 0)), pct(d.get("concept_chg", 0)), cnt,
               "up" if upr >= 50 else "dn", cls(upr), upr, d.get("up", 0),
               "up" if d.get("avg", 0) > 0 else "dn", cls(d.get("avg", 0)), pct(d.get("avg", 0))))
    verdict = ("近端次新板块「<b>%s</b>」当日<b class='%s'>%s</b>，成分 <b>%d</b> 只中 <b>%d</b> 只上涨（占比 %.0f%%）。"
               "次新强度是市场风险偏好的敏感指标：次新越强，说明资金敢追高、情绪越热。"
               % (esc(d.get("concept_name", "")), cls(d.get("avg", 0)), pct(d.get("avg", 0)),
                  cnt, d.get("up", 0), upr))
    tmpl = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>新股/次新复盘 · @@DATE_CN@@</title>
<style>@@CSS@@</style>
</head>
<body>
<header>
  <div class="wrap">
    <span class="tag">次新 · 日更</span>
    <h1>新股 / 次新复盘 <span class="em">· 情绪先锋</span></h1>
    <div class="sub">近端次新强度 ｜ <b>@@DATE_CN@@</b></div>
  </div>
</header>
<div class="wrap">
  <div class="kpis">@@KPIS@@</div>
  <div class="verdict"><div class="t">次新强度</div><p>@@VERDICT@@</p></div>

  <section>
    <h2><span class="n">1</span>近端次新涨跌幅榜</h2>
    <div class="h2sub">按当日涨跌幅排序（前 40）</div>
    <div class="card">
      <table>
        <thead><tr><th>个股</th><th class="num">涨跌幅</th></tr></thead>
        <tbody>@@ROWS@@</tbody>
      </table>
    </div>
  </section>

  <footer>
    <b>数据来源：</b>东方财富公开行情接口（概念板块·次新股）｜数据截至 <b>@@DATE_CN@@</b> 收盘｜报告生成 @@GEN@@
    <div class="disc"><b>说明与免责：</b>本页以「次新股」概念成分股强度替代打新日历（打新日历所需数据中心接口在本环境不稳定）。
    次新波动大、风险高，仅供情绪观察，不构成任何投资建议。</div>
  </footer>
</div>
</body>
</html>"""
    return (tmpl.replace("@@CSS@@", load_css()).replace("@@DATE_CN@@", date_cn(d.get("date", "")))
            .replace("@@KPIS@@", kpis).replace("@@VERDICT@@", verdict)
            .replace("@@ROWS@@", mem_rows(d.get("members", [])))
            .replace("@@GEN@@", d.get("generated", "")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DP)
    ap.add_argument("--out", default=OP)
    a = ap.parse_args()
    d = json.load(open(a.data, encoding="utf-8"))
    html = render(d)
    html = html.replace("</body>", '<div class="wrap" style="margin-top:26px"><a href="index.html" style="color:var(--up);font-weight:700;text-decoration:none">← 返回总览</a></div>' + "</body>", 1)
    open(a.out, "w", encoding="utf-8").write(html)
    print("已生成: %s (%d bytes)" % (a.out, len(html.encode("utf-8"))))


if __name__ == "__main__":
    main()
