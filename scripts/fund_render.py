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

  <section>
    <h2><span class="n">2</span>这张表怎么读</h2>
    <div class="h2sub">一眼掌握你的整体权益仓位表现</div>
    <p class="body"><b>"持有"</b> = 你的实仓，重点盯当日与近1年；<b>"关注"</b> = 常看的宽基 / 避险标的，用于判断大环境。<b>单位净值</b>每日更新，ETF 看跟踪误差，主动基看长期超额。</p>
    <p class="body">近1年收益仅作参考（过往不预示未来）。把关注池当成"<b>市场温度计</b>"：宽基集体走弱 = 防守为主；避险资产走强 = 风险偏好下降。</p>
    <ul class="ck">
      <li><span class="ic g">→</span><b>持有基金集体大跌</b>：检查仓位，触发止损纪律</li>
      <li><span class="ic g">→</span><b>关注标的进入低估</b>：定投加仓的时机</li>
      <li><span class="ic g">→</span><b>ETF 折溢价异常</b>：注意申赎与套利风险</li>
      <li><span class="ic g">→</span><b>债基 / 货基走强</b>：资金避险，降权益仓位</li>
    </ul>
  </section>

  <section>
    <h2><span class="n">3</span>经典策略参考</h2>
    <div class="h2sub">公开经典方法的科普，非投资建议</div>
    <div class="card hl">
      <div class="ct">策略一 · 定投（Dollar-Cost Averaging）</div>
      <p class="body">固定金额、固定周期买入，天然平滑成本。<b>估值越低越加大额</b>，把低位买得多。适合没有择时能力的普通投资者，用纪律对抗情绪。</p>
    </div>
    <div class="card">
      <div class="ct">策略二 · 核心-卫星（Core-Satellite）</div>
      <p class="body"><b>核心</b>用宽基（沪深300 / 中证500）打底，<b>卫星</b>用行业 / 主题 ETF 增强。控制卫星仓位 ≤ 20~30%，既赚 beta 又留弹性。</p>
    </div>
    <div class="card">
      <div class="ct">策略三 · 再平衡（Rebalancing）</div>
      <p class="body">当某类资产偏离目标比例 ±5% 时<b>调回原比例</b>——涨多的卖、跌多的买，实现"<b>止盈不止损</b>"的纪律化锁利。</p>
    </div>
    <div class="warn"><div class="wt">配置提示</div><p>股 / 债 / 现金 / 黄金按<b>风险预算</b>分配（全天候思路），任一环境都有对冲。基金是"买资产"而非"炒代码"，长期持有 + 再平衡胜过频繁择时。</p></div>
    <div class="disc"><b>策略免责：</b>以上为公开经典投资方法的科普性介绍，<b>不构成任何具体买卖建议</b>。基金有波动风险，过往业绩不预示未来。</div>
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
    html = html.replace("</body>", '<div class="wrap" style="margin-top:26px"><a href="index.html" style="color:var(--up);font-weight:700;text-decoration:none">← 返回总览</a></div>' + "</body>", 1)
    open(a.out, "w", encoding="utf-8").write(html)
    print("已生成: %s (%d bytes)" % (a.out, len(html.encode("utf-8"))))


if __name__ == "__main__":
    main()
