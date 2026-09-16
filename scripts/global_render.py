# -*- coding: utf-8 -*-
"""大类资产夜盘温度计渲染器 — 读 data_global.json 写 global.html（白底黑字红涨）。"""
import json, os, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DP = os.path.abspath(os.path.join(HERE, "..", "data_global.json"))
OP = os.path.abspath(os.path.join(HERE, "..", "global.html"))


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


def fnum(v):
    return "{:,.2f}".format(v)


def rows_html(assets):
    return "".join(
        '<tr><td class="nm">%s</td><td>%s</td>'
        '<td class="num mono %s">%s</td><td class="num mono %s">%s</td></tr>'
        % (esc(a["name"]), esc(a["group"]), cls(a["chg"]), pct(a["chg"]),
           cls(a["chg"]), fnum(a["price"]))
        for a in sorted(assets, key=lambda x: (x["group"], -x["chg"])))


def render(d):
    us = d.get("us_avg", 0)
    left = max(3, min(97, (us + 3) / 6 * 100))
    temp_lb = "偏暖" if us > 0.3 else ("偏冷" if us < -0.3 else "中性")
    rh = rows_html(d.get("assets", []))
    verdict = ("隔夜外盘美股<b class='%s'>%s</b>（道指/标普/纳指均值），大类资产夜盘温度计指向"
               "<b>%s</b>。美元指数、黄金、原油同步异动需重点关注——它们往往提前反映次日 A 股风险偏好。"
               % (cls(us), pct(us), temp_lb))
    tmpl = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>大类资产夜盘温度计 · @@DATE_CN@@</title>
<style>@@CSS@@</style>
</head>
<body>
<header>
  <div class="wrap">
    <span class="tag">外盘 · 日更</span>
    <h1>大类资产夜盘温度计 <span class="em">· 睡前一眼</span></h1>
    <div class="sub">美股 / 亚太（港股·日经）/ 外汇 ｜ <b>@@DATE_CN@@</b></div>
  </div>
</header>
<div class="wrap">
  <div class="verdict"><div class="t">夜盘信号</div><p>@@VERDICT@@</p></div>

  <section>
    <h2><span class="n">1</span>夜盘温度计</h2>
    <div class="h2sub">美股三大指数均涨为基准，映射次日风险偏好</div>
    <div class="gauge">
      <div class="gauge-track"></div>
      <div class="gauge-mark" style="left:%.1f%%" data-lb="%s"></div>
    </div>
    <div class="gauge-scale"><span>偏冷 -3%%</span><span>中性</span><span>偏暖 +3%%</span></div>
  </section>

  <section>
    <h2><span class="n">2</span>大类资产一览</h2>
    <div class="h2sub">涨跌幅为最新交易时点的变动</div>
    <div class="card">
      <table>
        <thead><tr><th>资产</th><th>类别</th><th class="num">涨跌幅</th><th class="num">最新价</th></tr></thead>
        <tbody>@@ROWS@@</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="n">3</span>这张表怎么读</h2>
    <div class="h2sub">外盘是全球风险偏好的"锚"</div>
    <p class="body"><b>美股（道指 / 标普 / 纳指）</b>是全球风险偏好的锚；A 股次日开盘，尤其创业板 / 科技成长，常受牵连——纳指强则成长风格占优，纳指弱则防守为主。</p>
    <p class="body"><b>美元走强</b>→ 大宗商品与新兴市场承压；<b>黄金走强</b>→ 避险情绪升温；汇率与商品常联动。看懂外盘，等于提前知道次日 A 股情绪的"底色"。</p>
    <ul class="ck">
      <li><span class="ic g">→</span><b>美股三指齐涨</b>：风险偏好回升，A 股易高开</li>
      <li><span class="ic g">→</span><b>纳指单独强</b>：科技 / 成长风格占优</li>
      <li><span class="ic g">→</span><b>美元 + 黄金同涨</b>：避险模式，降低风险仓位</li>
      <li><span class="ic g">→</span><b>外盘大跌</b>：A 股低开概率高，控制仓位</li>
    </ul>
  </section>

  <section>
    <h2><span class="n">4</span>经典策略参考</h2>
    <div class="h2sub">公开经典方法的科普，非投资建议</div>
    <div class="card hl">
      <div class="ct">策略一 · 海龟交易法则（Turtle / Donchian 通道突破）</div>
      <p class="body">以 <b>N 日（如 20 / 55 日）高点突破为买点、跌破为卖点</b>，配 <b>ATR 头寸管理</b>。适合商品 / 指数 ETF 的趋势市——不预测方向，只跟随已发生的突破。</p>
    </div>
    <div class="card">
      <div class="ct">策略二 · 全天候 / 风险平价（Ray Dalio All Weather）</div>
      <p class="body">按<b>风险</b>而非金额配置（股 / 债 / 商品 / 黄金），使任一宏观环境都有资产对冲。适合作为底仓，降低单一市场波动。</p>
    </div>
    <div class="card">
      <div class="ct">策略三 · Larry Connors RSI(2) 用于美股 / ETF</div>
      <p class="body">标普 ETF（SPY）在 <b>RSI(2) &lt; 10 且创新低</b>时买入，反弹至 <b>RSI(2) &gt; 50</b> 卖出。历史胜率高，但须严格止损，避免在单边崩盘中死扛。</p>
    </div>
    <div class="warn"><div class="wt">逆向提示</div><p>黄金急涨 + 美股急跌 = 恐惧极值，常是中期买点（别人恐惧我贪婪）。但极值可能持续，须分批而非一把梭。</p></div>
    <div class="disc"><b>策略免责：</b>以上为公开经典交易方法的科普性介绍，<b>不构成任何具体买卖建议</b>。跨境 / 商品交易涉及汇率与隔夜风险，须审慎。</div>
  </section>

  <footer>
    <b>数据来源：</b>东方财富公开行情接口（外盘延迟镜像）｜数据截至 <b>@@DATE_CN@@</b> 最近收盘｜报告生成 @@GEN@@
    <div class="disc"><b>口径说明：</b>黄金 / 原油 / 美债等商品与债券，因历史接口在本环境被限流暂缺，将于海外日更环境补全；当前以美股、亚太、外汇为主。<b>免责声明：</b>本页为公开市场数据的客观整理，仅供观察外盘情绪参考，不构成任何投资建议。</div>
  </footer>
</div>
</body>
</html>"""
    return (tmpl.replace("@@CSS@@", load_css()).replace("@@DATE_CN@@", date_cn(d.get("date", "")))
            .replace("@@VERDICT@@", verdict).replace("@@ROWS@@", rh).replace("@@GEN@@", d.get("generated", ""))
            .replace("%.1f", "%.1f" % left).replace("%s", temp_lb))


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
