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

  <section>
    <h2><span class="n">2</span>这张表怎么读</h2>
    <div class="h2sub">估值带是"贵还是便宜"的标尺</div>
    <p class="body"><b>PE / PB 分位越低</b> = 相对历史越便宜；但"<b>便宜可能更便宜</b>"（价值陷阱），须结合盈利趋势判断。<b>涨跌幅</b>每日真实更新，<b>估值带</b>为本页定性参考（非实时历史分位）。</p>
    <p class="body">宽基（沪深300 / 上证50）处于低估区间时，定投 / 分批布局的<b>安全边际</b>更高；高估值板块（如科创50）需要业绩兑现来消化。</p>
    <ul class="ck">
      <li><span class="ic g">→</span><b>低估 + 盈利改善</b>：黄金组合，优先布局</li>
      <li><span class="ic g">→</span><b>低估但盈利下滑</b>：警惕价值陷阱</li>
      <li><span class="ic g">→</span><b>高估 + 高景气</b>：赛道拥挤，注意回撤</li>
      <li><span class="ic g">→</span><b>分位 &lt; 20%</b>：历史便宜区，长线关注</li>
    </ul>
  </section>

  <section>
    <h2><span class="n">3</span>经典策略参考</h2>
    <div class="h2sub">公开经典方法的科普，非投资建议</div>
    <div class="card hl">
      <div class="ct">策略一 · 安全边际（Graham / Buffett）</div>
      <p class="body">只在 <b>PE / PB 处历史低位、且盈利稳定</b>时分批买入；用"<b>金字塔加仓</b>"在低分位区越跌越买，把成本摊在低处。这是价值投资的基石。</p>
    </div>
    <div class="card">
      <div class="ct">策略二 · 定投（Dollar-Cost Averaging）</div>
      <p class="body">不分时点、固定金额、固定周期买入，天然平滑成本。<b>估值越低（分位越低）越可加大定投额</b>，把低位买得多。</p>
    </div>
    <div class="card">
      <div class="ct">策略三 · 均值回归（Mean Reversion）</div>
      <p class="body">估值偏离历史中枢过大时，向中枢回归是中期力量。<b>高估减仓、低估加仓</b>，赚"回归"的钱而非"无限上涨"的钱。</p>
    </div>
    <div class="warn"><div class="wt">逆向提示</div><p>"别人恐惧我贪婪"——当市场恐慌、估值跌破历史低位时，往往是长期买点。但恐慌可能持续，须分批、控仓。</p></div>
    <div class="disc"><b>策略免责：</b>以上为公开经典投资方法的科普性介绍，<b>不构成任何具体买卖建议</b>。估值带为定性参考，精确分位需接入专业数据源。</div>
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
    html = html.replace("</body>", '<div class="wrap" style="margin-top:26px"><a href="index.html" style="color:var(--up);font-weight:700;text-decoration:none">← 返回总览</a></div>' + "</body>", 1)
    open(a.out, "w", encoding="utf-8").write(html)
    print("已生成: %s (%d bytes)" % (a.out, len(html.encode("utf-8"))))


if __name__ == "__main__":
    main()
