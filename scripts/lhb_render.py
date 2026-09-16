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

  <section>
    <h2><span class="n">2</span>这张表怎么读</h2>
    <div class="h2sub">龙虎榜是"聪明钱"动向的高频窗口</div>
    <p class="body">龙虎榜 = 当日异动股（涨跌停 / 振幅 / 换手达标）的<b>席位买卖明细</b>。关键看买卖方结构：<b>"机构专用"</b>多为公募 / 保险等中长线资金；<b>营业部</b>多为游资 / 短线资金。</p>
    <p class="body">净买入额大 ≠ 一定涨。要看两点：① <b>买方结构</b>（机构多 = 偏中线，游资多 = 偏短线情绪）；② <b>卖方是否集中出货</b>（卖方全是机构 = 派发信号）。</p>
    <ul class="ck">
      <li><span class="ic g">→</span><b>机构专用席位净买</b>：中期加分项，可信度最高</li>
      <li><span class="ic g">→</span><b>多家一线游资同买</b>：情绪高标，但波动与一日游风险大</li>
      <li><span class="ic g">→</span><b>卖方全为机构</b>：警惕高位派发</li>
      <li><span class="ic g">→</span><b>上榜原因 "机构买入"</b>：比"游资接力"更稳健</li>
    </ul>
  </section>

  <section>
    <h2><span class="n">3</span>经典策略参考</h2>
    <div class="h2sub">公开经典方法的科普，非个股建议</div>
    <div class="card hl">
      <div class="ct">策略一 · 机构溢价跟随（Institutional Premium）</div>
      <p class="body">研究统计显示，<b>机构专用席位大额净买</b>的个股，其后 20 日往往有显著超额收益。可把"机构净买 Top"列为观察池，<b>不追高</b>，等缩量回踩关键支撑再跟，止损设于上榜日最低价。</p>
    </div>
    <div class="card">
      <div class="ct">策略二 · 游资情绪跟随（Momentum / 打板）</div>
      <p class="body">一线游资上榜且换手健康的个股，次日溢价概率较高。可顺势参与，但必须<b>严格止损</b>——游资"一日游"是常态，次日不连板即撤。</p>
    </div>
    <div class="warn"><div class="wt">风险警示</div><p>对敲拉抬、席位伪装、利好兑现即出货，是龙虎榜常见陷阱。<b>龙虎榜是"结果"不是"原因"</b>，看到大佬买入不等于能跟赚，切勿盲从。</p></div>
    <div class="disc"><b>策略免责：</b>以上为公开经典交易方法的科普性介绍，<b>不构成任何具体买卖建议</b>。龙虎榜波动大、风险高，参与须有成熟交易体系与止损纪律。</div>
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
    html = html.replace("</body>", '<div class="wrap" style="margin-top:26px"><a href="index.html" style="color:var(--up);font-weight:700;text-decoration:none">← 返回总览</a></div>' + "</body>", 1)
    open(a.out, "w", encoding="utf-8").write(html)
    print("已生成: %s (%d bytes)" % (a.out, len(html.encode("utf-8"))))


if __name__ == "__main__":
    main()
