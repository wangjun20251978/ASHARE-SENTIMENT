# -*- coding: utf-8 -*-
"""转债市场温度计渲染器 — 读 data_bond.json 写 bond.html（白底黑字红涨）。"""
import json, os, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DP = os.path.abspath(os.path.join(HERE, "..", "data_bond.json"))
OP = os.path.abspath(os.path.join(HERE, "..", "bond.html"))


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


def bond_rows(rows):
    return "".join(
        '<tr><td class="nm">%s <span class="badge bg-gy">%s</span></td>'
        '<td class="num mono">%.2f</td><td class="num mono %s">%s</td>'
        '<td class="num mono %s">%.1f</td><td class="num mono">%.1f</td></tr>'
        % (esc(r["name"]), esc(r["code"]), r["price"], cls(r["chg"]), pct(r["chg"]),
           cls(r["prem"]), r["prem"], r["dual"])
        for r in rows)


def render(d):
    left = max(3, min(97, d.get("temp_val", 50)))
    kpis = ('<div class="kpi up"><div class="lb">转债数量</div><div class="vl">%d</div><div class="nt">只上市转债</div></div>'
            '<div class="kpi %s"><div class="lb">平均转股溢价率</div><div class="vl %s">%.1f%%</div><div class="nt">越高越贵</div></div>'
            '<div class="kpi %s"><div class="lb">中位溢价率</div><div class="vl %s">%.1f%%</div><div class="nt">中位数</div></div>'
            '<div class="kpi %s"><div class="lb">温度计</div><div class="vl %s">%s</div><div class="nt">股性/债性</div></div>'
            % (d.get("count", 0),
               "dn" if d.get("avg_prem", 0) >= 40 else "up", cls(d.get("avg_prem", 0)), d.get("avg_prem", 0),
               "dn" if d.get("med_prem", 0) >= 40 else "up", cls(d.get("med_prem", 0)), d.get("med_prem", 0),
               "bl", "", d.get("temp_lb", "")))
    verdict = ("全市场 <b>%d</b> 只转债，平均转股溢价率 <b class='%s'>%.1f%%</b>、中位 <b>%.1f%%</b>，"
               "转债温度计指向<b>%s</b>。溢价率越高代表债性越强、股性越弱（估值偏贵）；"
               "双低（价格+溢价率）靠前的转债攻守兼备，是低位布局的常规观察池。"
               % (d.get("count", 0), cls(d.get("avg_prem", 0)), d.get("avg_prem", 0),
                  d.get("med_prem", 0), d.get("temp_lb", "")))
    tmpl = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>转债市场温度计 · @@DATE_CN@@</title>
<style>@@CSS@@</style>
</head>
<body>
<header>
  <div class="wrap">
    <span class="tag">转债 · 日更</span>
    <h1>转债市场温度计 <span class="em">· 低风险投资</span></h1>
    <div class="sub">等权估值 / 双低池 / 涨幅榜 ｜ <b>@@DATE_CN@@</b></div>
  </div>
</header>
<div class="wrap">
  <div class="kpis">@@KPIS@@</div>
  <div class="verdict"><div class="t">转债温度计</div><p>@@VERDICT@@</p></div>

  <section>
    <h2><span class="n">1</span>估值温度计</h2>
    <div class="h2sub">转股溢价率均值映射股性/债性强弱</div>
    <div class="gauge">
      <div class="gauge-track"></div>
      <div class="gauge-mark" style="left:%d%%" data-lb="%s"></div>
    </div>
    <div class="gauge-scale"><span>进攻性强·便宜</span><span>中性</span><span>债性强·偏贵</span></div>
  </section>

  <section>
    <h2><span class="n">2</span>双低转债 Top 15</h2>
    <div class="h2sub">双低 = 价格 + 转股溢价率（越低越攻守兼备）</div>
    <div class="card">
      <table>
        <thead><tr><th>转债</th><th class="num">价格</th><th class="num">涨跌幅</th><th class="num">转股溢价率</th><th class="num">双低值</th></tr></thead>
        <tbody>@@DUAL@@</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="n">3</span>涨幅榜 Top 15</h2>
    <div class="h2sub">当日弹性最强的转债</div>
    <div class="card">
      <table>
        <thead><tr><th>转债</th><th class="num">价格</th><th class="num">涨跌幅</th><th class="num">转股溢价率</th><th class="num">双低值</th></tr></thead>
        <tbody>@@UP@@</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="n">4</span>这张表怎么读</h2>
    <div class="h2sub">双低是转债"攻守兼备"的核心指标</div>
    <p class="body"><b>双低 = 价格 + 转股溢价率</b>，越低越"攻守兼备"：<b>价格低</b> = 有债底保护（跌不动），<b>溢价低</b> = 跟涨弹性大。平均 / 中位溢价率高，代表整体偏贵（债性强）。</p>
    <p class="body">温度计映射股性 / 债性：偏暖 = 股性强、弹性大但贵；偏冷 = 债性强、安全但弹性弱。下表双低 Top15 是常规观察池，涨幅榜反映当日弹性。</p>
    <ul class="ck">
      <li><span class="ic g">→</span><b>双低 &lt; 120</b>：常规配置区，稳健优先</li>
      <li><span class="ic g">→</span><b>价格 &lt; 110 且溢价 &lt; 20%</b>：攻守兼备的"黄金区"</li>
      <li><span class="ic g">→</span><b>溢价 &gt; 50%</b>：偏债性，弹性弱</li>
      <li><span class="ic g">→</span><b>强赎倒计时</b>：高价转债注意及时卖出</li>
    </ul>
  </section>

  <section>
    <h2><span class="n">5</span>经典策略参考</h2>
    <div class="h2sub">公开经典方法的科普，非投资建议</div>
    <div class="card hl">
      <div class="ct">策略一 · 双低轮动（Double-Low Rotation）</div>
      <p class="body">按"<b>双低值</b>"排序，买入最低的 N 只（如 10~15 只）分散持有，<b>定期（周 / 月）轮动</b>换入更低的。这是转债圈最经典、回撤可控的稳健策略。</p>
    </div>
    <div class="card">
      <div class="ct">策略二 · 网格交易（Grid，你已在用）</div>
      <p class="body">在价格区间内设档位<b>低买高卖</b>吃波动，适合溢价低、债底厚的中低价转债。配合双低选标的，波动中累积收益。</p>
    </div>
    <div class="card">
      <div class="ct">策略三 · 下修博弈（Put-back / 转股价下修）</div>
      <p class="body">公司下修转股价 → 溢价大降 → 转债上涨。可提前埋伏"<b>高溢价 + 有下修动机</b>"的转债，赚条款博弈的钱。</p>
    </div>
    <div class="warn"><div class="wt">风险提示</div><p><b>强赎</b>（高价转债收益瞬间归零）、<b>信用违约</b>、<b>流动性差</b>是转债三大风险。双低≠无风险，须看正股质地与剩余年限。</p></div>
    <div class="disc"><b>策略免责：</b>以上为公开经典交易方法的科普性介绍，<b>不构成任何具体买卖建议</b>。转债投资须关注强赎与信用风险。</div>
  </section>

  <footer>
    <b>数据来源：</b>东方财富公开行情接口（可转债板块）｜数据截至 <b>@@DATE_CN@@</b> 收盘｜报告生成 @@GEN@@
    <div class="disc"><b>免责声明：</b>本页为公开市场数据的客观整理，转债有信用风险与强赎风险，双低仅为量化观察维度，
    不构成任何投资建议。</div>
  </footer>
</div>
</body>
</html>"""
    return (tmpl.replace("@@CSS@@", load_css()).replace("@@DATE_CN@@", date_cn(d.get("date", "")))
            .replace("@@KPIS@@", kpis).replace("@@VERDICT@@", verdict)
            .replace("@@DUAL@@", bond_rows(d.get("dual_low", [])))
            .replace("@@UP@@", bond_rows(d.get("up_top", [])))
            .replace("%d", "%d" % left).replace("%s", d.get("temp_lb", ""))
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
