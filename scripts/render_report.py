#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股主线与情绪复盘 — HTML 渲染器
读 data.json → 生成 index.html（单文件、离线可看、涨红跌灰）

用法: python scripts/render_report.py [--data data.json] [--out index.html]
"""

import json
import os
import argparse
from collections import Counter

# ------------------------------------------------------------------ 工具

def esc(s):
    if s is None:
        return ""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def num(v, nd=2):
    if v is None:
        return "—"
    try:
        return ("%." + str(nd) + "f") % float(v)
    except Exception:
        return "—"


def pct(v, nd=2):
    if v is None:
        return "—"
    try:
        return "%+.2f%%" % float(v)
    except Exception:
        return "—"


def yi(v, nd=2):
    if v is None:
        return "—"
    try:
        return "%+.2f 亿" % (float(v) / 1e8)
    except Exception:
        return "—"


def cls(v):
    try:
        f = float(v)
    except Exception:
        return ""
    if f > 0:
        return "c-up"
    if f < 0:
        return "c-dn"
    return ""


def amt_str(v):
    if v is None:
        return "—"
    try:
        v = float(v)
    except Exception:
        return "—"
    if v >= 1e12:
        return "%.2f 万亿" % (v / 1e12)
    return "%.2f 亿" % (v / 1e8)


def vol_str(v):
    """成交量（手）→ 亿手"""
    if v is None:
        return "—"
    try:
        return "%.2f 亿手" % (float(v) / 1e8)
    except Exception:
        return "—"


def bar_w(v, vmax, minw=2.0):
    try:
        v = abs(float(v))
        vmax = abs(float(vmax)) or 1
    except Exception:
        return minw
    return max(minw, min(100.0, v / vmax * 100))


def date_cn(d8):
    return "%s-%s-%s" % (d8[:4], d8[4:6], d8[6:]) if d8 and len(d8) == 8 else (d8 or "")


# ------------------------------------------------------------------ 主线识别

EMOTION_KW = [
    "昨日", "连板", "涨停", "跌停", "ST", "次新", "破净", "高送转", "含可转债", "举牌",
    "重仓", "低价", "高价", "大盘", "小盘", "融资融券", "标的", "成份", "成股", "指数",
    "AH", "B股", "GDR", "转债", "新股", "龙虎榜", "机构", "基金", "社保", "QFII",
    "券商", "北向", "再融资", "增发", "配股", "解禁", "分红", "送转", "预盈", "预亏",
    "摘帽", "扭亏", "壳资源", "分拆", "参股", "创投", "独角兽", "MSCI", "富时", "标普",
    "反转股", "超跌", "强势股", "活跃股", "题材股", "业绩", "预增", "预减", "同花顺",
    "东方财富", "热股", "人气", "妖股", "庄股", "游资",
]


def is_industry_concept(name):
    if not name:
        return False
    return not any(k in name for k in EMOTION_KW)


def spread_ratio(b):
    u = b.get("up") or 0
    d = b.get("down") or 0
    return (u / (u + d)) if (u + d) else 0.0


def line_score(b, zt_n=0, max_zt=1, kind="concept"):
    """主线得分：涨幅 + 资金 + 扩散度 + 涨停贡献"""
    s_day = min(max(b.get("pct") or 0, 0) * 7, 30)
    s_flow = min(max(b.get("netflow") or 0, 0) / 1e9 * 11, 30)
    s_spread = spread_ratio(b) * 20
    s_zt = ((zt_n / max_zt) * 25) if max_zt else 0
    w_zt = 0.25 if kind == "industry" else 0.08
    return round(s_day * 0.22 + s_flow * 0.30 + s_spread * 0.28 + s_zt * w_zt * 4, 1)


def pick_mainlines(data):
    inds = data.get("industries", [])
    cons = data.get("concepts", [])
    zt_pool = data.get("zt_pool", [])
    zt_map = Counter((s.get("hybk") or "其他").strip() for s in zt_pool)
    max_zt = max(zt_map.values()) if zt_map else 1

    c_clean = [dict(c) for c in cons
               if c.get("pct") is not None and c.get("pct") > 0
               and is_industry_concept(c.get("name"))]
    for c in c_clean:
        c["spread"] = round(spread_ratio(c) * 100, 1)
        c["score"] = line_score(c, 0, 1, "concept")
    c_clean.sort(key=lambda x: x["score"], reverse=True)
    concept_lines = c_clean[:4]

    i_clean = [dict(b) for b in inds if b.get("pct") is not None and b.get("pct") > 0]
    seen, i_uniq = set(), []
    for b in i_clean:
        key = (b.get("name") or "").rstrip("ⅠⅡⅢⅣⅤⅥ")
        if key in seen:
            continue
        seen.add(key)
        i_uniq.append(b)
    for b in i_uniq:
        b["zt_n"] = zt_map.get((b.get("name") or "").strip(), 0)
        b["spread"] = round(spread_ratio(b) * 100, 1)
        b["score"] = line_score(b, b["zt_n"], max_zt, "industry")
    i_uniq.sort(key=lambda x: x["score"], reverse=True)
    industry_lines = i_uniq[:4]
    enriched = sorted(i_uniq, key=lambda x: x.get("pct") or 0, reverse=True)

    fake = [b for b in i_uniq
            if (b.get("pct") or 0) > 0.8
            and ((b.get("netflow") or 0) < 0 or spread_ratio(b) < 0.35)
            and b.get("zt_n", 0) == 0]
    fake.sort(key=lambda x: x.get("pct") or 0, reverse=True)

    return concept_lines, industry_lines, fake[:4], enriched, zt_map


# ------------------------------------------------------------------ 预警 / 判断

def build_alerts(data, senti):
    warns, oks = [], []

    amt = data.get("amount_hist") or []
    if len(amt) >= 2:
        cur_a, prev_a = amt[-1][1], amt[-2][1]
        if prev_a:
            chg = (cur_a / prev_a - 1) * 100
            if chg < -8:
                warns.append(("量能明显萎缩，市场缺少安全垫",
                              "两市成交量 %s，较前一交易日 %s（%s）。缩量之下主线之外几乎没有承接，"
                              "一旦主线出现放量阴线或龙头跌停，指数回撤速度会快于普涨市场。"
                              % (vol_str(cur_a), vol_str(prev_a), pct(chg))))
            elif chg > 8:
                oks.append(("量能放大，增量资金入场",
                            "两市成交量 %s，较前一交易日 %s（%s）。放量配合主线走强，"
                            "说明有增量资金参与，而非纯存量博弈。"
                            % (vol_str(cur_a), vol_str(prev_a), pct(chg))))

    lb = data.get("max_lb") or 0
    if lb <= 3:
        warns.append(("连板高度偏低，赚钱效应天花板被压低",
                      "最高连板仅 %d 板，缺少更高标的空间。说明资金不愿意在高度上做接力，"
                      "情绪若要升温，必须先看到高度回补。" % lb))
    elif lb >= 5:
        oks.append(("连板高度健康，情绪空间打开",
                    "最高连板达 %d 板，说明高位仍有资金愿意接力，短线空间未被压死。" % lb))

    seal = senti["seal_rate"]
    if seal < 60:
        warns.append(("封板率偏低，涨停质量不高",
                      "封板率仅 %.1f%%（涨停 %d 家 / 炸板 %d 家）。封板率低于 60%% 说明盘中反复开板，"
                      "追高者容易承接失败，涨停的含金量下降。"
                      % (seal, data.get("zt_count", 0), data.get("zb_count", 0))))
    elif seal >= 78:
        oks.append(("封板率健康，涨停含金量高",
                    "封板率 %.1f%%（涨停 %d 家 / 炸板 %d 家），封板资金坚决，涨停结构相对扎实。"
                    % (seal, data.get("zt_count", 0), data.get("zb_count", 0))))

    pr = data.get("promote_rate") or 0
    if pr < 20:
        warns.append(("连板晋级率低，高位接力意愿弱",
                      "昨日涨停 %d 家，今日仅 %d 家实现连板，晋级率 %.1f%%。"
                      "低晋级率反映资金不愿为高位买单，追涨连板的盈亏比不佳。"
                      % (data.get("zt_prev_count", 0), data.get("promote_count", 0), pr)))
    elif pr >= 35:
        oks.append(("连板晋级率较高，情绪延续性好",
                    "晋级率 %.1f%%（昨日涨停 %d 家 → 今日连板 %d 家），接力资金活跃，"
                    "赚钱效应具备延续基础。"
                    % (pr, data.get("zt_prev_count", 0), data.get("promote_count", 0))))

    dt = data.get("dt_count") or 0
    zt = data.get("zt_count") or 0
    if dt > zt * 0.6 and dt > 5:
        warns.append(("跌停家数偏多，亏钱效应在扩散",
                      "跌停 %d 家，与涨停 %d 家相比结构偏弱。跌停偏多说明有资金在坚决离场，"
                      "市场情绪并非全面转暖。" % (dt, zt)))

    br = data.get("breadth") or {}
    if (br.get("up") or 0) and (br.get("down") or 0):
        if br["down"] > br["up"] * 2:
            warns.append(("市场广度极差，赚钱效应集中在少数方向",
                          "全市场上涨 %d 家 / 下跌 %d 家，跌家数是涨家数的 %.1f 倍。"
                          "多数个股在下跌，赚钱效应高度集中在少数方向。"
                          % (br["up"], br["down"], br["down"] / br["up"])))

    if not oks:
        oks.append(("涨停结构仍有承接",
                    "涨停 %d 家、最高连板 %d 板，仍有资金愿意在强方向承接，未出现全面退潮。"
                    % (zt, data.get("max_lb") or 0)))

    return warns[:3], oks[:2]


def overnight_checklist(data, senti):
    lb = data.get("max_lb") or 0
    items = [
        ("a", "<b>成交量能否回升</b>——量能是主线能否延续的先行指标：缩量持续 = 主线独木难支，放量 = 增量资金认可主线。"),
    ]
    if lb >= 2:
        items.append(("a", "<b>最高板（%d 板）能否继续晋级</b>——连板高度是否回补，直接决定短线情绪升温还是退潮。" % lb))
    else:
        items.append(("a", "<b>是否出现 2 板以上个股</b>——当前高度仅 %d 板，需要看到高度重建。" % lb))

    items.append(("a", "<b>主线方向能否连续第二天获资金净流入</b>——验证今日流入是「趋势建仓」还是「一日反抽」。"))
    items.append(("a", "<b>封板率能否维持在 60%% 以上</b>——当前 %.1f%%，若继续下滑说明涨停质量恶化。" % senti["seal_rate"]))

    br = data.get("breadth") or {}
    if br.get("up") is not None:
        items.append(("a", "<b>涨跌家数比能否改善</b>——当前 %d 涨 / %d 跌，广度决定行情是「结构性」还是「全面性」。"
                      % (br.get("up") or 0, br.get("down") or 0)))

    zb = data.get("zb_pool") or []
    if zb:
        top_zb = sorted(zb, key=lambda x: x.get("zf") or 0, reverse=True)[:2]
        names = "、".join(esc(s.get("n", "")) for s in top_zb)
        items.append(("r", "<b>关注今日炸板股（如 %s）明日表现</b>——炸板股次日反包说明情绪未坏；继续走弱则是退潮确认。" % names))

    return items[:6]


def overnight_stance(data, senti, concept_lines, industry_lines):
    out = []
    names = "、".join(esc(b["name"]) for b in (concept_lines[:3] or industry_lines[:3]))
    if names:
        out.append(("g", "宜", "在 <b>%s</b> 等方向内，优先关注「当日上涨 + 资金净流入为正 + 板块内扩散度较高」的品种，"
                             "沿趋势跟随，回踩低吸优于追高。" % names))
    out.append(("a", "慎", "对「涨幅靠前但主力资金净流出」的方向保持谨慎——这类上涨多由承接口径驱动，而非布局型资金。"))

    if senti["seal_rate"] < 65:
        out.append(("r", "忌", "追高封板率偏低（%.1f%%）环境下的一字板与高位连板，封板质量不足，盈亏比差。" % senti["seal_rate"]))
    else:
        out.append(("r", "忌", "追高已连续多板的高位股，尤其在晋级率仅 %.1f%% 的环境下。" % (data.get("promote_rate") or 0)))

    downs = sorted([b for b in (data.get("industries") or []) if (b.get("pct") or 0) < -1],
                   key=lambda x: x.get("pct") or 0)[:3]
    if downs:
        out.append(("r", "避", "仍在失血的方向——<b>%s</b>，无企稳信号前不宜参与。"
                    % "、".join(esc(b["name"]) for b in downs)))

    if senti["temp"] >= 6:
        out.append(("a", "仓", "情绪偏热，总仓位不宜满仓；主线既是利润来源也是风险来源，见放量阴线即减。"))
    else:
        out.append(("a", "仓", "情绪不亢奋，以结构性机会为主；总仓位保持克制，等待情绪升温的明确信号再考虑加仓。"))
    return out


# ------------------------------------------------------------------ 渲染

def make_headline(d, concept_lines, industry_lines, senti):
    """根据当日结构动态生成主标题，突出「指数 vs 主线」的核心矛盾。"""
    idx = {i["name"]: i for i in d.get("indexes", [])}
    valid = [i for i in d.get("indexes", []) if i.get("pct") is not None]
    sh = (idx.get("上证指数") or {}).get("pct") or 0
    br = d.get("breadth") or {}
    up, down = br.get("up") or 0, br.get("down") or 0
    strong = max(valid, key=lambda x: x["pct"]) if valid else None
    main = concept_lines[0]["name"] if concept_lines else (
        industry_lines[0]["name"] if industry_lines else None)

    narrow = bool(up and down and down > up * 1.5)
    if narrow and main:
        return ('指数在退，<span class="em">%s</span>在进<br>'
                '资金正从「多数方向」切向「单一主线」' % esc(main))
    if strong and strong["pct"] > 0.5 and sh < 0:
        return ('指数分化，<span class="em">%s</span>领跑<br>'
                '结构强于指数，选方向比看指数更重要' % esc(strong["name"]))
    if sh > 0.3 and up and up > down:
        return ('指数收红，赚钱效应扩散<br><span class="em">%s</span>方向领涨'
                % esc(main or "强势"))
    if sh < -0.3:
        return ('指数整理，缩量等待方向<br>情绪温度 %.1f / 10（%s）'
                % (senti["temp"], senti["label"]))
    return '市场窄幅整理<br>主线与情绪待明朗'


def render_header(d):
    idx = {i["name"]: i for i in d.get("indexes", [])}
    sh = idx.get("上证指数", {})
    turnover = d.get("turnover_today")
    return """
<header>
  <div class="wrap">
    <div class="tag">A股 · 主线与情绪复盘</div>
    <h1>%s</h1>
    <div class="sub">
      数据截至 <b>%s 收盘</b> ｜ 上证 <b class="%s">%s&nbsp;%s</b>
      ｜ 两市成交 <b>%s</b> ｜ 报告生成 %s
    </div>
  </div>
</header>""" % (
        d.get("headline", ""),
        date_cn(d.get("date", "")),
        cls(sh.get("pct")), num(sh.get("price")), pct(sh.get("pct")),
        amt_str(turnover) if turnover else "—",
        esc(d.get("generated", "")),
    )


def render_kpis(d, senti, concept_lines, industry_lines):
    cards = []
    valid = [i for i in d.get("indexes", []) if i.get("pct") is not None]
    if valid:
        best = max(valid, key=lambda x: x["pct"])
        cards.append(("up", esc(best["name"]) + "（最强指数）", pct(best["pct"]), "样本内表现最强"))
    if concept_lines:
        b = concept_lines[0]
        cards.append(("up", esc(b["name"]) + "（最强题材）", pct(b.get("pct")),
                      "主力 %s ｜ 扩散度 %.0f%%" % (yi(b.get("netflow")), b.get("spread") or 0)))
    elif industry_lines:
        b = industry_lines[0]
        cards.append(("up", esc(b["name"]) + "（最强行业）", pct(b.get("pct")),
                      "主力 %s" % yi(b.get("netflow"))))
    if valid:
        worst = min(valid, key=lambda x: x["pct"])
        cards.append(("dn", esc(worst["name"]) + "（最弱指数）", pct(worst["pct"]), "样本内表现最弱"))
    cards.append(("ac", "情绪温度", "%.1f / 10" % senti["temp"],
                  "%s ｜ 封板率 %.1f%%" % (senti["label"], senti["seal_rate"])))

    html = ['<div class="kpis">']
    for tone, lb, vl, nt in cards[:4]:
        c = {"up": "c-up", "dn": "c-dn", "ac": "c-ac"}.get(tone, "c-bl")
        html.append('<div class="kpi %s"><div class="lb">%s</div>'
                    '<div class="vl %s">%s</div><div class="nt">%s</div></div>'
                    % (tone, lb, c, vl, nt))
    html.append("</div>")
    return "\n".join(html)


def render_verdict(d, senti, concept_lines, industry_lines):
    zt = d.get("zt_count") or 0
    dt = d.get("dt_count") or 0
    lb = d.get("max_lb") or 0
    br = d.get("breadth") or {}
    turnover = d.get("turnover_today")

    main = "、".join(esc(b["name"]) for b in (concept_lines[:2] or industry_lines[:2])) or "尚不明确"
    tone_txt = {"cold": "情绪偏冷", "mid": "情绪中性", "hot": "情绪偏热"}.get(senti["tone"], "情绪中性")
    breadth_txt = ""
    if br.get("up") and br.get("down"):
        breadth_txt = "全市场上涨 <b>%d</b> 家 / 下跌 <b>%d</b> 家。" % (br["up"], br["down"])

    return """
  <div class="verdict">
    <div class="t">档位判断：结构性行情 · %s</div>
    <p>
      今日涨停 <b>%d 家</b>、炸板 <b>%d 家</b>、跌停 <b>%d 家</b>，封板率 <b>%.1f%%</b>，
      最高连板 <b>%d 板</b>，连板晋级率 <b>%.1f%%</b>，两市成交 <b>%s</b>。
      综合判定情绪温度 <b>%.1f / 10（%s）</b>。%s资金主线指向 <b>%s</b>。
    </p>
  </div>""" % (
        tone_txt, zt, d.get("zb_count") or 0, dt, senti["seal_rate"], lb,
        d.get("promote_rate") or 0, amt_str(turnover) if turnover else "—",
        senti["temp"], senti["label"], breadth_txt, main,
    )


def render_index_bars(d):
    valid = [i for i in d.get("indexes", []) if i.get("pct") is not None]
    if not valid:
        return ""
    valid.sort(key=lambda x: x["pct"], reverse=True)
    vmax = max(abs(i["pct"]) for i in valid) or 1
    rows = []
    for i in valid:
        p = i["pct"]
        tone = "up" if p > 0 else ("dn" if p < 0 else "mix")
        rows.append('<div class="bar-row"><div class="bar-lb">%s</div>'
                    '<div class="bar-track"><div class="bar-fill %s" style="width:%.1f%%"></div></div>'
                    '<div class="bar-vl %s">%s</div></div>'
                    % (esc(i["name"]), tone, bar_w(p, vmax), cls(p), pct(p)))
    return ('<div class="card"><div class="ct">主要指数当日涨跌 '
            '<span class="badge bg-ac">涨红跌灰</span></div><div class="bars">%s</div></div>'
            % "".join(rows))


def render_amount_chart(d):
    amt = d.get("amount_hist") or []
    if not amt:
        return ""
    vmax = max(a for _, a in amt) or 1
    rows = []
    for dt, a in amt:
        rows.append('<div class="bar-row"><div class="bar-lb">%s</div>'
                    '<div class="bar-track"><div class="bar-fill mix" style="width:%.1f%%"></div></div>'
                    '<div class="bar-vl" style="color:var(--blue)">%s</div></div>'
                    % (esc(dt[5:]), a / vmax * 100, vol_str(a)))
    turnover = d.get("turnover_today")
    note = ('<p class="body" style="margin-top:14px;margin-bottom:0">当日两市成交额约 <b>%s</b>。'
            '柱状为沪深两市成交量合计（口径为手），用于观察量能趋势。%s</p>'
            % (amt_str(turnover), "")) if turnover else ""
    return ('<div class="card"><div class="ct">近 %d 个交易日量能趋势</div><div class="bars">%s</div>%s</div>'
            % (len(amt), "".join(rows), note))


def render_breadth(d):
    br = d.get("breadth") or {}
    up, down = br.get("up") or 0, br.get("down") or 0
    tot = up + down
    if not tot:
        return ""
    upr = up / tot * 100
    return """
<div class="card">
  <div class="ct">市场广度（沪深两市涨跌家数）</div>
  <div class="bar-track" style="height:26px;display:flex;border-radius:4px;overflow:hidden">
    <div style="width:%.1f%%;background:linear-gradient(90deg,rgba(255,43,43,.5),var(--up))"></div>
    <div style="width:%.1f%%;background:linear-gradient(90deg,var(--dn),rgba(158,158,158,.35))"></div>
  </div>
  <div style="display:flex;justify-content:space-between;margin-top:9px;font-size:12.5px">
    <span class="c-up">上涨 <b>%d</b> 家（%.1f%%）</span>
    <span class="c-dn">下跌 <b>%d</b> 家（%.1f%%）</span>
  </div>
  <p class="body" style="margin-top:12px;margin-bottom:0">%s</p>
</div>""" % (upr, 100 - upr, up, upr, down, 100 - upr,
            ("跌家数明显多于涨家数，赚钱效应集中在少数方向。" if down > up * 1.5
             else ("涨跌家数接近，市场结构相对均衡。" if down > up * 0.8
                   else "涨家数多于跌家数，赚钱效应较广泛。")))


def render_sector_tables(d, enriched):
    """概念条形图 + 行业表"""
    cons = [c for c in (d.get("top_concepts") or [])
            if c.get("pct") is not None and is_industry_concept(c.get("name"))][:8]
    con_html = ""
    if cons:
        vb = abs(cons[0]["pct"]) or 1
        bars = "".join(
            '<div class="bar-row"><div class="bar-lb">%s</div>'
            '<div class="bar-track"><div class="bar-fill %s" style="width:%.1f%%"></div></div>'
            '<div class="bar-vl %s">%s</div></div>'
            % (esc(b["name"]), "up" if b["pct"] > 0 else "dn",
               bar_w(b["pct"], vb), cls(b["pct"]), pct(b["pct"])) for b in cons)
        con_html = ('<div class="card"><div class="ct">概念板块涨幅 TOP'
                    '<span class="badge bg-ac">已排除情绪类伪概念</span></div>'
                    '<div class="bars">%s</div></div>' % bars)

    rows = []
    vmax = max((abs(b.get("pct") or 0) for b in enriched[:12]), default=1) or 1
    for b in enriched[:10]:
        zt_n = b.get("zt_n", 0)
        zt_badge = (' <span class="badge bg-up">%d涨停</span>' % zt_n) if zt_n else ""
        rows.append('<tr><td class="nm">%s%s</td>'
                    '<td class="num mono %s">%s</td>'
                    '<td class="num mono %s">%s</td>'
                    '<td class="num mono %s">%s</td>'
                    '<td class="num mono %s">%s</td>'
                    '<td class="num">%s / %s</td></tr>'
                    % (esc(b["name"]), zt_badge,
                       cls(b.get("pct")), pct(b.get("pct")),
                       cls(b.get("pct5")), pct(b.get("pct5")),
                       cls(b.get("pct20")), pct(b.get("pct20")),
                       cls(b.get("netflow")), yi(b.get("netflow")),
                       int(b.get("up") or 0), int(b.get("down") or 0)))
    ind_html = """
<div class="card">
  <div class="ct">行业板块涨幅榜</div>
  <table>
    <thead><tr><th>行业</th><th class="num">当日</th><th class="num">5日</th>
    <th class="num">20日</th><th class="num">主力净流入</th><th class="num">涨/跌家数</th></tr></thead>
    <tbody>%s</tbody>
  </table>
  %s
</div>""" % ("".join(rows),
            "" if any(b.get("pct5") is not None for b in enriched[:10])
            else '<p class="body" style="margin-top:12px;margin-bottom:0;color:var(--txt3);font-size:12px">'
                 '注：5日 / 20日 列本次未取到（数据源不可用），不影响当日判断。</p>')
    return con_html, ind_html


def render_mainlines(d, concept_lines, industry_lines, fake_lines, zt_map):
    total_zt = d.get("zt_count") or 1

    crows = "".join(
        '<tr><td class="nm">%s</td><td class="num mono c-up">%s</td>'
        '<td class="num mono %s">%s</td><td class="num">%s / %s</td>'
        '<td class="num mono %s">%.0f%%</td></tr>'
        % (esc(b["name"]), pct(b.get("pct")),
           cls(b.get("netflow")), yi(b.get("netflow")),
           int(b.get("up") or 0), int(b.get("down") or 0),
           "c-up" if (b.get("spread") or 0) >= 60 else "c-ac", b.get("spread") or 0)
        for b in concept_lines)
    concept_html = ("""
<div class="card hl">
  <div class="ct"><span class="badge bg-up">题材主线</span>概念口径 · 已排除「昨日连板」等情绪类伪概念</div>
  <table>
    <thead><tr><th>概念</th><th class="num">当日</th><th class="num">主力净流入</th>
    <th class="num">涨/跌家数</th><th class="num">扩散度</th></tr></thead>
    <tbody>%s</tbody>
  </table>
  <p class="body" style="margin-top:14px;margin-bottom:0">
    扩散度 = 板块内上涨家数 ÷（上涨+下跌）。<b>扩散度越高，说明板块内部分歧越小、资金合力越强</b>；
    涨幅高但扩散度低，多为少数龙头拉动，持续性存疑。
  </p>
</div>""" % crows) if crows else (
        '<div class="card"><div class="ct"><span class="badge bg-up">题材主线</span></div>'
        '<p class="body" style="margin:0">今日未识别出符合产业逻辑的强势概念。</p></div>')

    irows = "".join(
        '<tr><td class="nm">%s%s</td><td class="num mono c-up">%s</td>'
        '<td class="num mono %s">%s</td><td class="num mono %s">%d</td>'
        '<td class="num">%s / %s</td><td class="num">%.1f%%</td></tr>'
        % (esc(b["name"]),
           (' <span class="badge bg-up">%d涨停</span>' % b["zt_n"]) if b.get("zt_n") else "",
           pct(b.get("pct")),
           cls(b.get("netflow")), yi(b.get("netflow")),
           "c-up" if (b.get("zt_n") or 0) >= 2 else ("c-ac" if b.get("zt_n") == 1 else "c-dn"),
           b.get("zt_n") or 0,
           int(b.get("up") or 0), int(b.get("down") or 0),
           (b.get("zt_n") or 0) / total_zt * 100)
        for b in industry_lines)
    industry_html = ("""
<div class="card hl">
  <div class="ct"><span class="badge bg-up">产业主线</span>行业口径 · 结合板块内涨停家数</div>
  <table>
    <thead><tr><th>行业</th><th class="num">当日</th><th class="num">主力净流入</th>
    <th class="num">板块内涨停</th><th class="num">涨/跌家数</th><th class="num">占全日涨停</th></tr></thead>
    <tbody>%s</tbody>
  </table>
</div>""" % irows) if irows else (
        '<div class="card"><div class="ct"><span class="badge bg-up">产业主线</span></div>'
        '<p class="body" style="margin:0">今日未识别出成规模的上涨行业。</p></div>')

    hy = Counter(d.get("hy_counter") or {})
    top_hy = hy.most_common(6)
    dist = ""
    if top_hy:
        palette = ["#ff2b2b", "#ffffff", "#8f8f8f", "#d9d9d9", "#5a5a5a", "#ff6b6b"]
        segs = "".join('<div style="width:%.2f%%;background:%s" title="%s %d家"></div>'
                       % (c / total_zt * 100, palette[i % len(palette)], esc(nm), c)
                       for i, (nm, c) in enumerate(top_hy))
        legend = "".join(
            '<div><span class="dot" style="background:%s"></span>%s · <b style="color:#e8edf5">%d 家</b></div>'
            % (palette[i % len(palette)], esc(nm), c) for i, (nm, c) in enumerate(top_hy))
        share = top_hy[0][1] / total_zt * 100
        dist = """
<div class="card">
  <div class="ct">涨停归属分布（按所属行业）</div>
  <div style="display:flex;height:26px;border-radius:6px;overflow:hidden;margin-bottom:14px">%s</div>
  <div class="legend">%s</div>
  <p class="body" style="margin-top:14px;margin-bottom:0">
    最大集中方向为 <b>%s</b>，占全部涨停的 <b>%.1f%%</b>。%s
  </p>
</div>""" % ("".join(segs), legend, esc(top_hy[0][0]), share,
            "占比过半，涨停高度集中于单一方向，属「抱团」而非「全面扩散」。"
            if share >= 50 else "占比未过半，涨停分布相对分散，属偏扩散的结构。")

    if fake_lines:
        def fake_reason(b):
            rs = []
            if (b.get("netflow") or 0) < 0:
                rs.append("主力资金净流出")
            if (b.get("spread") or 0) < 45:
                rs.append("内部分歧大")
            if not b.get("zt_n"):
                rs.append("无涨停支撑")
            return " ＋ ".join(rs) or "缺乏持续动能"

        frows = "".join(
            '<tr><td class="nm">%s</td><td class="num mono c-up">%s</td>'
            '<td class="num mono c-dn">%s</td><td class="num mono %s">%.0f%%</td>'
            '<td class="num">%s / %s</td><td class="c-ac">%s</td></tr>'
            % (esc(b["name"]), pct(b.get("pct")), yi(b.get("netflow")),
               "c-dn" if (b.get("spread") or 0) < 45 else "c-ac", b.get("spread") or 0,
               int(b.get("up") or 0), int(b.get("down") or 0), fake_reason(b))
            for b in fake_lines)
        fake_html = """
<div class="card">
  <div class="ct"><span class="badge bg-gy">疑似诱多 / 需警惕</span>上涨但资金或扩散度不支持</div>
  <table>
    <thead><tr><th>行业</th><th class="num">当日</th><th class="num">主力净流入</th>
    <th class="num">扩散度</th><th class="num">涨/跌家数</th><th>性质判断</th></tr></thead>
    <tbody>%s</tbody>
  </table>
  <p class="body" style="margin-top:14px;margin-bottom:0">
    这些方向当日收红，但<b>主力资金净流出、或板块内部分歧明显（扩散度低）、且板块内无涨停个股</b> ——
    缺乏资金合力与产业联动，属单点脉冲，追高盈亏比不佳。
  </p>
</div>""" % frows
    else:
        fake_html = """
<div class="card">
  <div class="ct"><span class="badge bg-gy">疑似诱多 / 需警惕</span></div>
  <p class="body" style="margin:0">今日未识别出「上涨但资金流出且无涨停支撑」的典型诱多方向。</p>
</div>"""

    return concept_html, industry_html, dist, fake_html


def render_sentiment(d, senti):
    lbc = {}
    for k, v in (d.get("lb_counter") or {}).items():
        try:
            lbc[int(k)] = v
        except Exception:
            pass
    max_lb = max(lbc) if lbc else 0

    pos = max(2.0, min(98.0, senti["temp"] * 10))
    gauge = """
    <div class="gauge">
      <div class="gauge-track">
        <div class="gauge-mark" style="left:%.1f%%" data-lb="当前 %.1f"></div>
      </div>
      <div class="gauge-scale">
        <span>0 冰点</span><span>2</span><span>4 中性</span><span>6</span><span>8 热</span><span>10 沸腾</span>
      </div>
    </div>""" % (pos, senti["temp"])

    zt = d.get("zt_count") or 0
    zb = d.get("zb_count") or 0
    dt = d.get("dt_count") or 0
    boxes = """
    <div class="mgrid">
      <div class="mbox"><div class="mv c-up">%d</div><div class="ml">涨停家数<br>（跌停 %d 家）</div></div>
      <div class="mbox"><div class="mv %s">%.1f%%</div><div class="ml">封板率<br>涨停/(涨停+炸板)</div></div>
      <div class="mbox"><div class="mv c-ac">%d 板</div><div class="ml">连板高度<br>（最高连板）</div></div>
      <div class="mbox"><div class="mv %s">%.1f%%</div><div class="ml">连板晋级率<br>%d家连板/%d家昨涨停</div></div>
    </div>""" % (
        zt, dt,
        "c-up" if senti["seal_rate"] >= 70 else ("c-ac" if senti["seal_rate"] >= 55 else "c-dn"),
        senti["seal_rate"], max_lb,
        "c-up" if (d.get("promote_rate") or 0) >= 30 else ("c-ac" if (d.get("promote_rate") or 0) >= 18 else "c-dn"),
        d.get("promote_rate") or 0, d.get("promote_count") or 0, d.get("zt_prev_count") or 0)

    zt_pool = d.get("zt_pool") or []
    rungs = []
    for lv in sorted(lbc.keys(), reverse=True):
        if lv < 1:
            continue
        members = [s for s in zt_pool if int(s.get("lbc") or 0) == lv]
        members.sort(key=lambda x: x.get("lbt") or 0)
        chips = "".join(
            '<span class="%s">%s<span class="s">%s</span></span>'
            % ("stk" if lv >= 2 else "stk g", esc(s.get("n")),
               esc((s.get("hybk") or "")[:6]))
            for s in members[:14])
        rungs.append("""
        <div class="rung">
          <div class="rung-h %s"><div class="n">%d</div><div class="t">板</div></div>
          <div class="rung-b">%s</div>
        </div>""" % ("low" if lv == max_lb else "", lv, chips))
    ladder = '<div class="ladder">%s</div>' % "".join(rungs) if rungs else \
             '<p class="body" style="margin:0">今日无涨停个股。</p>'

    return gauge, boxes, ladder


def render_alerts(warns, oks):
    w = "".join("""
    <div class="warn">
      <div class="wt">⚠️ 预警：%s</div>
      <p>%s</p>
    </div>""" % (esc(t), body) for t, body in warns)
    o = "".join("""
    <div class="ok">
      <div class="wt">✓ 支撑：%s</div>
      <p>%s</p>
    </div>""" % (esc(t), body) for t, body in oks)
    return w, o


def render_checklist(items):
    li = "".join('<li><span class="ic %s">%d</span><div>%s</div></li>'
                 % (t, i + 1, body) for i, (t, body) in enumerate(items))
    return '<div class="card"><ul class="ck">%s</ul></div>' % li


def render_stance(items):
    li = "".join('<li><span class="ic %s">%s</span><div>%s</div></li>'
                 % (t, esc(lbl), body) for t, lbl, body in items)
    return '<div class="card"><ul class="ck">%s</ul></div>' % li


def render_reverse(d, senti, concept_lines):
    n = esc(concept_lines[0]["name"]) if concept_lines else "当前最强方向"
    parts = []
    if senti["temp"] < 4:
        parts.append("情绪温度仅 <b>%.1f / 10</b>，处于偏冷区间——"
                     "「主线独强」有时是资金无处可去的结果，而不是主动选择的结果。" % senti["temp"])
    br = d.get("breadth") or {}
    if (br.get("down") or 0) > (br.get("up") or 0) * 2:
        parts.append("全市场 <b>%d 涨 / %d 跌</b>，多数个股在失血。"
                     "这种结构下，主线的韧性建立在「别处更差」之上，而非「增量入场」。" % (br["up"], br["down"]))
    if (d.get("promote_rate") or 0) < 25:
        parts.append("连板晋级率仅 <b>%.1f%%</b>，接力的钱不多，"
                     "高位股的持续性需要用「第二天是否有人接」来验证。" % (d.get("promote_rate") or 0))
    parts.append("别把「只有它涨」误读为「它一定还会涨」——<b>抱团越极致，破团越剧烈</b>。")
    return """
    <div class="card hl2" style="margin-top:16px">
      <div class="ct"><span class="badge bg-ac">反向声音</span></div>
      <p class="body" style="margin-bottom:0">%s</p>
    </div>""" % "".join(parts)


# ------------------------------------------------------------------ 主模板

def load_css():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "style.css")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read()
    return ""


def render(d):
    senti = d["sentiment"]
    concept_lines, industry_lines, fake_lines, enriched, zt_map = pick_mainlines(d)
    d["headline"] = make_headline(d, concept_lines, industry_lines, senti)
    warns, oks = build_alerts(d, senti)
    checklist = overnight_checklist(d, senti)
    stance = overnight_stance(d, senti, concept_lines, industry_lines)

    con_html, ind_html = render_sector_tables(d, enriched)
    c_html, i_html, dist, f_html = render_mainlines(d, concept_lines, industry_lines, fake_lines, zt_map)
    gauge, mboxes, ladder = render_sentiment(d, senti)
    warn_html, ok_html = render_alerts(warns, oks)

    tmpl = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A股主线与情绪温度 · @@DATE_CN@@ 收盘复盘</title>
<style>@@CSS@@</style>
</head>
<body>

@@HEADER@@

<div class="wrap">

  @@KPIS@@

  @@VERDICT@@

  <section>
    <h2><span class="n">1</span>市场温度：指数、量能与广度</h2>
    <div class="h2sub">先看「水位」——今天赚钱的人多不多</div>
    @@INDEX_BARS@@
    @@AMOUNT_CHART@@
    @@BREADTH@@
  </section>

  <section>
    <h2><span class="n">2</span>板块强弱：资金往哪个方向挤</h2>
    <div class="h2sub">概念与行业涨幅对照，识别资金聚集方向</div>
    @@CON@@
    @@IND@@
  </section>

  <section>
    <h2><span class="n">3</span>主线识别：真主线 vs 诱多</h2>
    <div class="h2sub">用「资金 + 扩散度 + 涨停支撑」三条筛，区分真主线与单点脉冲</div>
    @@CONCEPT_LINES@@
    @@INDUSTRY_LINES@@
    @@DIST@@
    @@FAKE@@
  </section>

  <section>
    <h2><span class="n">4</span>情绪温度计：@@TEMP@@ / 10（@@SENTI_LABEL@@）</h2>
    <div class="h2sub">涨停家数、封板率、连板高度、晋级率——四维定位情绪位置</div>
    @@GAUGE@@
    @@MBOXES@@
    <h3>涨停梯队（按连板高度分层）</h3>
    <div class="card">@@LADDER@@</div>
  </section>

  <section>
    <h2><span class="n">5</span>延续性预警 · 隔夜判断</h2>
    <div class="h2sub">主线能不能续、情绪往哪走（非投资建议）</div>
    @@WARN@@
    @@OK@@
    <h3>下一交易日观察清单</h3>
    @@CHECKLIST@@
    <h3>操作含义（非投资建议）</h3>
    @@STANCE@@
    @@REVERSE@@
  </section>

  <footer>
    <b>数据来源：</b>东方财富公开行情接口（指数快照 / 涨停池 / 炸板池 / 跌停池 / 板块行情 / 板块资金流）＋
    腾讯行情（交易日与量能序列）｜数据截至 <b>@@DATE_CN@@ 收盘</b>｜报告生成 @@GENERATED@@
    <div class="disc">
      <b>免责声明：</b>本页面为公开市场数据的客观整理与结构化呈现，
      所有「情绪温度」「主线判定」「延续性预警」「操作含义」均为基于历史数据的<b>框架化推演</b>，
      不构成任何证券投资咨询或投资建议，亦不构成买卖要约。
      涨停／炸板／连板统计口径以数据源披露为准；板块涨跌幅为板块指数口径，与个股简单平均可能存在差异。
      市场数据可能存在延迟，请以交易所官方数据为准。
      <b>投资有风险，决策须谨慎。</b>
    </div>
  </footer>

</div>
</body>
</html>"""

    repl = {
        "@@CSS@@": load_css(),
        "@@DATE_CN@@": date_cn(d.get("date", "")),
        "@@HEADER@@": render_header(d),        "@@KPIS@@": render_kpis(d, senti, concept_lines, industry_lines),
        "@@VERDICT@@": render_verdict(d, senti, concept_lines, industry_lines),
        "@@INDEX_BARS@@": render_index_bars(d),
        "@@AMOUNT_CHART@@": render_amount_chart(d),
        "@@BREADTH@@": render_breadth(d),
        "@@CON@@": con_html,
        "@@IND@@": ind_html,
        "@@CONCEPT_LINES@@": c_html,
        "@@INDUSTRY_LINES@@": i_html,
        "@@DIST@@": dist,
        "@@FAKE@@": f_html,
        "@@TEMP@@": "%.1f" % senti["temp"],
        "@@SENTI_LABEL@@": senti["label"],
        "@@GAUGE@@": gauge,
        "@@MBOXES@@": mboxes,
        "@@LADDER@@": ladder,
        "@@WARN@@": warn_html,
        "@@OK@@": ok_html,
        "@@CHECKLIST@@": render_checklist(checklist),
        "@@STANCE@@": render_stance(stance),
        "@@REVERSE@@": render_reverse(d, senti, concept_lines),
        "@@GENERATED@@": d.get("generated", ""),
    }
    for k, v in repl.items():
        tmpl = tmpl.replace(k, v)
    return tmpl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    dp = os.path.abspath(args.data or os.path.join(here, "..", "data.json"))
    op = os.path.abspath(args.out or os.path.join(here, "..", "index.html"))

    with open(dp, encoding="utf-8") as f:
        d = json.load(f)

    html = render(d)
    with open(op, "w", encoding="utf-8") as f:
        f.write(html)
    print("已生成: %s (%d bytes)" % (op, len(html.encode("utf-8"))))


if __name__ == "__main__":
    main()
