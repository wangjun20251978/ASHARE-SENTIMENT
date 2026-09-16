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

    # —— 聪明钱观察名单（具体标的，规则化筛选）——
    def focus_rows():
        rows = []
        for r in d.get("industry_in", [])[:3]:
            rows.append('<tr><td class="nm">%s <span class="badge bg-up">行业</span></td>'
                        '<td class="num mono %s">%s</td><td class="num mono %s">%s</td><td>%s</td></tr>'
                        % (esc(r["name"]), cls(r["pct"]), pct(r["pct"]), cls(r["mainflow"]), yi(r["mainflow"]),
                           '<span class="badge bg-up">进攻方向</span>' if r["pct"] > 0 else '<span class="badge bg-gy">仅资金流入</span>'))
        for r in d.get("concept_in", [])[:3]:
            rows.append('<tr><td class="nm">%s <span class="badge bg-gy">概念</span></td>'
                        '<td class="num mono %s">%s</td><td class="num mono %s">%s</td><td>%s</td></tr>'
                        % (esc(r["name"]), cls(r["pct"]), pct(r["pct"]), cls(r["mainflow"]), yi(r["mainflow"]),
                           '<span class="badge bg-up">题材主线</span>' if r["pct"] > 0 else '<span class="badge bg-gy">仅资金流入</span>'))
        for r in d.get("stock_in", [])[:5]:
            strong = r.get("mainflow_pct", 0) >= 10
            rows.append('<tr><td class="nm">%s <span class="badge bg-gy">%s</span></td>'
                        '<td class="num mono %s">%s</td><td class="num mono %s">%s</td><td>%s</td></tr>'
                        % (esc(r["name"]), esc(r["code"]), cls(r["pct"]), pct(r["pct"]),
                           cls(r["mainflow"]), yi(r["mainflow"]),
                           '<span class="badge bg-up">强吸筹(占比≥10%)</span>' if strong else '<span class="badge bg-gy">观察</span>'))
        return "".join(rows)

    ind_names = "、".join("<b>%s</b>" % esc(r["name"]) for r in d.get("industry_in", [])[:3]) or "暂无"
    stk_names = "、".join("<b>%s</b>(%s)" % (esc(r["name"]), esc(r["code"]))
                          for r in d.get("stock_in", [])[:3] if r.get("mainflow_pct", 0) >= 10) or "今日无主力占比≥10%的个股"

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
    <h2><span class="n">1</span>聪明钱观察名单 · 今天具体看哪些</h2>
    <div class="h2sub">按"行业 Top3 + 概念 Top3 + 个股 Top5"规则化筛出，仅观察池整理，非买卖建议</div>
    <div class="card hl">
      <table>
        <thead><tr><th>标的 / 方向</th><th class="num">当日</th><th class="num">主力净流入</th><th>信号</th></tr></thead>
        <tbody>@@FOCUS@@</tbody>
      </table>
      <p class="body" style="margin-top:13px"><b>用法：</b>进攻方向（行业+概念 + 当日同涨）列入中线观察池，<b>等回踩 5/10 日线再介入，不追单日脉冲</b>；
      标 <span class="badge bg-up">强吸筹(占比≥10%)</span> 的个股是主力净流入占成交额比例高的"真金白银"标的。当前行业观察池：@@IND_NAMES@@；强吸筹个股：@@STK_NAMES@@。</p>
    </div>
  </section>

  <section>
    <h2><span class="n">2</span>行业资金净流入 Top 15</h2>
    <div class="h2sub">按主力净流入排序（单位：元）</div>
    <div class="card">
      <table>
        <thead><tr><th>行业</th><th class="num">当日</th><th class="num">主力净流入</th><th class="num">主力占比</th></tr></thead>
        <tbody>@@IND@@</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="n">3</span>概念资金净流入 Top 15</h2>
    <div class="h2sub">按主力净流入排序</div>
    <div class="card">
      <table>
        <thead><tr><th>概念</th><th class="num">当日</th><th class="num">主力净流入</th><th class="num">主力占比</th></tr></thead>
        <tbody>@@CON@@</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="n">4</span>个股主力净流入 Top 20</h2>
    <div class="h2sub">沪A + 深A 主板，按主力净流入排序</div>
    <div class="card">
      <table>
        <thead><tr><th>个股</th><th class="num">当日</th><th class="num">主力净流入</th><th class="num">主力占比</th></tr></thead>
        <tbody>@@SIN@@</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="n">5</span>个股主力净流出 Top 20</h2>
    <div class="h2sub">资金出逃方向，规避参考</div>
    <div class="card">
      <table>
        <thead><tr><th>个股</th><th class="num">当日</th><th class="num">主力净流入</th><th class="num">主力占比</th></tr></thead>
        <tbody>@@SOUT@@</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="n">6</span>这张表怎么读</h2>
    <div class="h2sub">主力资金流是"谁在买 / 卖"的第一信号</div>
    <p class="body">主力净流入 = 超大单 + 大单<b>主动买入</b>的净额估算，反映机构与大户动向；散户小单不计入，所以它比"成交额"更能看出<b>钱往哪去</b>。注意：这是基于逐笔成交的<b>推演口径</b>，不同平台算法略有差异。</p>
    <p class="body">读这张表看三点：① <b>行业榜与概念榜是否共振</b>——同方向才更可信；② <b>持续性比单日金额重要</b>——连续多日流入的方向才有趋势意义；③ <b>净流出榜 = 资金出逃方向</b>，常是高位股派发的前兆。</p>
    <ul class="ck">
      <li><span class="ic g">→</span><b>行业 + 概念双榜同向</b>：强主线候选，可信度最高</li>
      <li><span class="ic g">→</span><b>主力净流入但股价不涨</b>：对倒或内部分歧，警惕</li>
      <li><span class="ic g">→</span><b>连续 3 日同行业流入</b>：趋势性信号，列入观察</li>
      <li><span class="ic g">→</span><b>净流出榜首多为近期强势股</b>：补跌风险上升</li>
    </ul>
  </section>

  <section>
    <h2><span class="n">7</span>经典策略参考</h2>
    <div class="h2sub">公开经典方法的科普，非个股建议，须结合自身风险承受力</div>
    <div class="card hl">
      <div class="ct">策略一 · 跟随聪明钱（Follow the Smart Money）</div>
      <p class="body">把"<b>行业净流入 Top</b>"与"<b>概念净流入 Top</b>"共振的方向列为中线观察池；<b>不追单日脉冲</b>，等回踩 5 / 10 日线、量能萎缩时再介入，止损设于前低。</p>
    </div>
    <div class="card">
      <div class="ct">策略二 · 板块轮动（Sector Rotation / 美林时钟简化）</div>
      <p class="body">宏观按<b>复苏 → 过热 → 滞胀 → 衰退</b>切换进攻 / 防御板块。资金流是"轮动是否真发生"的<b>实时验证</b>：钱进有色 / 能源 = 顺周期占优；钱进医药 / 公用 = 防御占优。</p>
    </div>
    <div class="card">
      <div class="ct">策略三 · Larry Connors RSI(2) 回调买法（A股化）</div>
      <p class="body">在<b>资金持续流入的强势板块</b>内，等成分股 <b>RSI(2) 回落到 10~15</b> 且出现 3 日新低时低吸，反弹至 RSI(2) &gt; 50 减仓。这是美国短线大师的均值回归框架，需严格止损。</p>
    </div>
    <div class="warn"><div class="wt">背离预警</div><p>价涨 + 主力净流出 = <b>诱多派发</b>；价跌 + 净流入 = 低位吸筹（需结合股价位置判断）。出现背离时，信号比单纯涨跌更值得重视。</p></div>
    <div class="disc"><b>策略免责：</b>以上为公开经典交易方法的科普性介绍，用于建立分析框架，<b>不构成任何具体买卖建议</b>。实际投资须结合自身风险承受力、仓位与止损纪律。</div>
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
            .replace("@@FOCUS@@", focus_rows())
            .replace("@@IND_NAMES@@", ind_names)
            .replace("@@STK_NAMES@@", stk_names)
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
    html = html.replace("</body>", '<div class="wrap" style="margin-top:26px"><a href="index.html" style="color:var(--up);font-weight:700;text-decoration:none">← 返回总览</a></div>' + "</body>", 1)
    open(a.out, "w", encoding="utf-8").write(html)
    print("已生成: %s (%d bytes)" % (a.out, len(html.encode("utf-8"))))


if __name__ == "__main__":
    main()
