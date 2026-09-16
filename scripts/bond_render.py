# -*- coding: utf-8 -*-
"""转债市场温度计渲染器 — 读 data_bond.json 写 bond.html（白底黑字红涨）。
v2：双低表加信号徽标 + 新增「策略落地名单」段（已入区/黄金区/接近开启 具体标的）。"""
import json, os, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DP = os.path.abspath(os.path.join(HERE, "..", "data_bond.json"))
OP = os.path.abspath(os.path.join(HERE, "..", "bond.html"))

SIG_CLS = {"黄金区": "bg-up", "已入区": "bg-up", "接近开启": "bg-gy", "观察": "bg-gy"}


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


def bond_rows(rows, with_sig=True):
    out = []
    for r in rows:
        sig = ""
        if with_sig:
            s = r.get("sig", "观察")
            sig = '<span class="badge %s">%s</span>' % (SIG_CLS.get(s, "bg-gy"), s)
        out.append(
            '<tr><td class="nm">%s <span class="badge bg-gy">%s</span></td>'
            '<td class="num mono">%.2f</td><td class="num mono %s">%s</td>'
            '<td class="num mono %s">%.1f</td><td class="num mono">%.1f</td><td>%s</td></tr>'
            % (esc(r["name"]), esc(r["code"]), r["price"], cls(r["chg"]), pct(r["chg"]),
               cls(r["prem"]), r["prem"], r["dual"], sig))
    return "".join(out)


def near_rows(rows):
    """接近开启名单：距入区阈值(120)还差多少"""
    return "".join(
        '<tr><td class="nm">%s <span class="badge bg-gy">%s</span></td>'
        '<td class="num mono">%.2f</td><td class="num mono %s">%.1f</td>'
        '<td class="num mono">%.1f</td><td class="num mono c-up">还差 %.1f</td></tr>'
        % (esc(r["name"]), esc(r["code"]), r["price"], cls(r["prem"]), r["prem"],
           r["dual"], max(0.1, r["dual"] - 120.0))
        for r in rows)


def names(rows, n=8):
    return "、".join("<b>%s</b>(%s)" % (esc(r["name"]), esc(r["code"])) for r in rows[:n])


def render(d):
    left = max(3, min(97, d.get("temp_val", 50)))
    kpis = ('<div class="kpi up"><div class="lb">转债数量</div><div class="vl">%d</div><div class="nt">只全市场转债</div></div>'
            '<div class="kpi %s"><div class="lb">平均转股溢价率</div><div class="vl %s">%.1f%%</div><div class="nt">越高越贵</div></div>'
            '<div class="kpi up"><div class="lb">双低&lt;120 已入区</div><div class="vl">%d</div><div class="nt">只达到入区标准</div></div>'
            '<div class="kpi bl"><div class="lb">接近开启(120~130)</div><div class="vl">%d</div><div class="nt">只临近阈值</div></div>'
            % (d.get("count", 0),
               "dn" if d.get("avg_prem", 0) >= 40 else "up", cls(d.get("avg_prem", 0)), d.get("avg_prem", 0),
               d.get("n_in", 0), d.get("n_near", 0)))
    verdict = ("全市场 <b>%d</b> 只转债，平均转股溢价率 <b class='%s'>%.1f%%</b>、中位 <b>%.1f%%</b>，温度计指向<b>%s</b>。"
               "按双低（价格+溢价率）筛选：目前 <b class='c-up'>已入区（双低&lt;120）%d 只</b>、"
               "<b>黄金区（价&lt;110 且溢价&lt;20%%）%d 只</b>、<b>接近开启（120~130）%d 只</b>——"
               "具体名单见下方「策略落地名单」。"
               % (d.get("count", 0), cls(d.get("avg_prem", 0)), d.get("avg_prem", 0),
                  d.get("med_prem", 0), d.get("temp_lb", ""),
                  d.get("n_in", 0), d.get("n_gold", 0), d.get("n_near", 0)))
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
    <div class="sub">全市场估值 / 双低池 / 策略落地名单 / 涨幅榜 ｜ <b>@@DATE_CN@@</b></div>
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
    <h2><span class="n">2</span>双低转债 Top 15 <span class="badge bg-up">含信号标记</span></h2>
    <div class="h2sub">双低 = 价格 + 转股溢价率（越低越攻守兼备）｜信号：黄金区 &gt; 已入区 &gt; 接近开启</div>
    <div class="card">
      <table>
        <thead><tr><th>转债</th><th class="num">价格</th><th class="num">涨跌幅</th><th class="num">转股溢价率</th><th class="num">双低值</th><th>信号</th></tr></thead>
        <tbody>@@DUAL@@</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="n">3</span>策略落地名单 · 今天具体看哪些</h2>
    <div class="h2sub">按双低轮动框架从全市场 @@CNT@@ 只中筛出，仅观察池整理，非买卖建议</div>

    <div class="card hl">
      <div class="ct">✅ 已入区（双低 &lt; 120）— 今日共 @@N_IN@@ 只，双低最低的候选：</div>
      <p class="body">@@IN_NAMES@@</p>
      <p class="body nt3">上表「双低 Top15」即按此排序，信号列标 <span class="badge bg-up">已入区</span> / <span class="badge bg-up">黄金区</span> 的就是当前达到入区标准的标的。</p>
    </div>

    <div class="card hl2">
      <div class="ct">⭐ 黄金区（价格 &lt; 110 且溢价 &lt; 20%）— 今日共 @@N_GOLD@@ 只：</div>
      <p class="body">@@GOLD_NAMES@@</p>
      <p class="body nt3">黄金区 = 债底保护 + 跟涨弹性兼具，是双低框架里攻守最平衡的一档；若无，说明全市场价格偏贵。</p>
    </div>

    <div class="card">
      <div class="ct">🔔 接近开启（双低 120~130）— 今日共 @@N_NEAR@@ 只，谁离入区最近：</div>
      <table>
        <thead><tr><th>转债</th><th class="num">价格</th><th class="num">转股溢价率</th><th class="num">双低值</th><th class="num">距入区(120)</th></tr></thead>
        <tbody>@@NEAR@@</tbody>
      </table>
      <p class="body nt3">这些是「<b>接近开了</b>」的标的：双低再降一点（价格跌或溢价压缩）就进入常规配置区，可加入自选留意。</p>
    </div>
  </section>

  <section>
    <h2><span class="n">4</span>涨幅榜 Top 15</h2>
    <div class="h2sub">当日弹性最强的转债</div>
    <div class="card">
      <table>
        <thead><tr><th>转债</th><th class="num">价格</th><th class="num">涨跌幅</th><th class="num">转股溢价率</th><th class="num">双低值</th></tr></thead>
        <tbody>@@UP@@</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="n">5</span>这张表怎么读</h2>
    <div class="h2sub">双低是转债"攻守兼备"的核心指标</div>
    <p class="body"><b>双低 = 价格 + 转股溢价率</b>，越低越"攻守兼备"：<b>价格低</b> = 有债底保护（跌不动），<b>溢价低</b> = 跟涨弹性大。平均 / 中位溢价率高，代表整体偏贵（债性强）。</p>
    <ul class="ck">
      <li><span class="ic r">✓</span><b>双低 &lt; 120 = 已入区</b>：达到常规配置标准，双低 Top15 表中已标红</li>
      <li><span class="ic r">✓</span><b>价格 &lt; 110 且溢价 &lt; 20% = 黄金区</b>：攻守兼备的最优档，数量越少市场越贵</li>
      <li><span class="ic g">→</span><b>双低 120~130 = 接近开启</b>：还没达标但临近，放进自选等回落后介入，不追</li>
      <li><span class="ic g">→</span><b>溢价 &gt; 50%</b>：偏债性，弹性弱；<b>强赎倒计时</b>的高价转债注意及时了结</li>
    </ul>
  </section>

  <section>
    <h2><span class="n">6</span>经典策略参考</h2>
    <div class="h2sub">公开经典方法的科普，非投资建议</div>
    <div class="card hl">
      <div class="ct">策略一 · 双低轮动（Double-Low Rotation）</div>
      <p class="body">按"<b>双低值</b>"排序，买入最低的 N 只（如 10~15 只）分散持有，<b>定期（周 / 月）轮动</b>换入更低的。这是转债圈最经典、回撤可控的稳健策略。<b>今日落地：</b>上表双低 Top15 就是现成的候选池，其中 @@IN_NAMES_SHORT@@ 等 @@N_IN@@ 只已达标；@@NEAR_NAMES_SHORT@@ 等接近开启的留作候补。</p>
    </div>
    <div class="card">
      <div class="ct">策略二 · 网格交易（Grid）</div>
      <p class="body">在价格区间内设档位<b>低买高卖</b>吃波动，适合溢价低、债底厚的中低价转债（优先在「已入区 / 黄金区」名单里选）。配合双低选标的，波动中累积收益。</p>
    </div>
    <div class="card">
      <div class="ct">策略三 · 下修博弈（转股价下修）</div>
      <p class="body">公司下修转股价 → 溢价大降 → 转债上涨。可提前埋伏"<b>高溢价 + 有下修动机</b>"的转债，赚条款博弈的钱。此信息需结合公告，本页暂不覆盖。</p>
    </div>
    <div class="warn"><div class="wt">风险提示</div><p><b>强赎</b>（高价转债收益瞬间归零）、<b>信用违约</b>、<b>流动性差</b>是转债三大风险。双低≠无风险，介入前须看正股质地、剩余年限与是否有强赎公告。</p></div>
    <div class="disc"><b>策略免责：</b>以上为公开经典交易方法的科普性介绍与基于公开数据的规则化筛选，<b>不构成任何具体买卖建议</b>。转债投资须关注强赎与信用风险。</div>
  </section>

  <footer>
    <b>数据来源：</b>东方财富公开行情接口（可转债板块，全市场 @@CNT@@ 只）｜数据截至 <b>@@DATE_CN@@</b> 收盘｜报告生成 @@GEN@@
    <div class="disc"><b>免责声明：</b>本页为公开市场数据的客观整理与规则化筛选，转债有信用风险与强赎风险，双低信号仅为量化观察维度，
    不构成任何投资建议。</div>
  </footer>
</div>
</body>
</html>"""
    html = (tmpl.replace("@@CSS@@", load_css()).replace("@@DATE_CN@@", date_cn(d.get("date", "")))
            .replace("@@KPIS@@", kpis).replace("@@VERDICT@@", verdict)
            .replace("@@DUAL@@", bond_rows(d.get("dual_low", [])))
            .replace("@@NEAR@@", near_rows(d.get("near_open", [])) or '<tr><td colspan="5">今日无接近开启（双低 120~130）的转债</td></tr>')
            .replace("@@UP@@", bond_rows(d.get("up_top", []), with_sig=False))
            .replace("@@IN_NAMES@@", names(d.get("dual_low", []) and [b for b in d.get("dual_low", []) if b.get("sig") in ("已入区", "黄金区")], 8) or "今日双低 Top15 中暂无已入区标的（市场整体偏贵）")
            .replace("@@IN_NAMES_SHORT@@", names([b for b in d.get("dual_low", []) if b.get("sig") in ("已入区", "黄金区")], 3) or "暂无")
            .replace("@@GOLD_NAMES@@", names(d.get("gold", []), 10) or "今日无黄金区标的")
            .replace("@@NEAR_NAMES_SHORT@@", names(d.get("near_open", []), 3) or "暂无")
            .replace("@@N_IN@@", str(d.get("n_in", 0)))
            .replace("@@N_GOLD@@", str(d.get("n_gold", 0)))
            .replace("@@N_NEAR@@", str(d.get("n_near", 0)))
            .replace("@@CNT@@", str(d.get("count", 0)))
            .replace("@@GEN@@", d.get("generated", "")))
    # 温度计占位符（模板中 %d / %s 已被上方 replace 误伤，故单独用标记处理不了——改为在模板里先替换）
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DP)
    ap.add_argument("--out", default=OP)
    a = ap.parse_args()
    d = json.load(open(a.data, encoding="utf-8"))
    html = render(d)
    # 温度计指针：模板中的 %d%% / %s 需要在其它替换后处理——这里用安全标记方式
    left = max(3, min(97, d.get("temp_val", 50)))
    html = html.replace("left:PID%%", "left:%d%%" % left).replace("PID%%", "%d%%" % left)
    html = html.replace('data-lb="PSUB"', 'data-lb="%s"' % d.get("temp_lb", ""))
    html = html.replace("</body>", '<div class="wrap" style="margin-top:26px"><a href="index.html" style="color:var(--up);font-weight:700;text-decoration:none">← 返回总览</a></div>' + "</body>", 1)
    open(a.out, "w", encoding="utf-8").write(html)
    print("已生成: %s (%d bytes)" % (a.out, len(html.encode("utf-8"))))


if __name__ == "__main__":
    main()
