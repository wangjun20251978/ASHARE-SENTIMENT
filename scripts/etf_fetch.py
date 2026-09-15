# -*- coding: utf-8 -*-
"""ETF 每日轮动信号抓取器 — 三因子：当日动能 / 主力净流入 / 主力净流入占比。
输出 data_etf.json 供 etf_render.py 使用。纯标准库，走东财延迟镜像。"""
import json, os, time, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "data_etf.json"))

# ETF 池：secid = 市场.代码（沪=1 深=0），带分类标签
POOL = [
    # 宽基
    ("1.510300", "沪深300ETF", "宽基"), ("1.510500", "中证500ETF", "宽基"),
    ("1.510050", "上证50ETF", "宽基"), ("0.159915", "创业板ETF", "宽基"),
    ("1.588000", "科创50ETF", "宽基"), ("0.159901", "深100ETF", "宽基"),
    ("0.159919", "沪深300ETF", "宽基"),
    # 海外
    ("1.513100", "纳指ETF", "海外"), ("1.513500", "标普500ETF", "海外"),
    ("1.513180", "恒生科技ETF", "海外"), ("1.513050", "中概互联ETF", "海外"),
    # 行业
    ("1.512480", "半导体ETF", "行业"), ("1.512760", "芯片ETF", "行业"),
    ("1.512660", "军工ETF", "行业"), ("1.512010", "医药ETF", "行业"),
    ("1.512690", "酒ETF", "行业"), ("0.159928", "消费ETF", "行业"),
    ("1.512000", "券商ETF", "行业"), ("1.512800", "银行ETF", "行业"),
    ("1.512200", "地产ETF", "行业"), ("1.515220", "煤炭ETF", "行业"),
    ("1.512400", "有色ETF", "行业"), ("1.515790", "光伏ETF", "行业"),
    ("0.159755", "电池ETF", "行业"), ("1.512980", "传媒ETF", "行业"),
    ("1.515050", "通信ETF", "行业"), ("0.159865", "养殖ETF", "行业"),
    ("1.515980", "人工智能ETF", "行业"), ("1.562500", "机器人ETF", "行业"),
    ("1.516110", "汽车ETF", "行业"), ("0.159996", "家电ETF", "行业"),
    ("1.516150", "稀土ETF", "行业"), ("1.515230", "软件ETF", "行业"),
    ("0.159870", "化工ETF", "行业"), ("0.159611", "电力ETF", "行业"),
    ("0.159647", "中药ETF", "行业"), ("1.515030", "化工ETF", "行业"),
    ("1.560260", "电力ETF", "行业"), ("1.516160", "芯片ETF", "行业"),
    # 商品 / 债券
    ("1.518880", "黄金ETF", "商品"), ("0.159980", "有色ETF", "商品"),
    ("0.159981", "能源化工ETF", "商品"), ("1.511380", "转债ETF", "债券"),
    ("1.511010", "国债ETF", "债券"), ("1.511260", "十年国债ETF", "债券"),
]

CATA_CN = {"宽基": "宽基指数", "行业": "行业/主题", "海外": "跨境/海外",
           "商品": "商品", "债券": "债券"}


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore"))


def grab_etfs():
    secids = ",".join(c[0] for c in POOL)
    url = ("https://push2delay.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2"
           "&fields=f12,f13,f14,f2,f3,f62,f184,f20&secids=%s" % secids)
    d = fetch(url)
    diff = (d.get("data") or {}).get("diff") or []
    name_map = {c[0]: (c[1], c[2]) for c in POOL}
    rows = []
    for it in diff:
        sec = "%s.%s" % (it.get("f13"), it.get("f12"))
        nm, cata = name_map.get(sec, (it.get("f14"), "行业"))
        rows.append({
            "code": it.get("f12"),
            "name": nm or it.get("f14"),
            "cata": cata,
            "pct": float(it.get("f3") or 0),          # 当日涨跌%
            "price": float(it.get("f2") or 0),
            "mainflow": float(it.get("f62") or 0),     # 主力净流入(元)
            "mainflow_pct": float(it.get("f184") or 0),  # 主力净流入占比%
            "mktcap": float(it.get("f20") or 0),       # 总市值(元)
        })
    return rows


def score(rows):
    if not rows:
        return rows
    n = len(rows)

    def rank(vals, reverse=False):
        order = sorted(range(n), key=lambda i: vals[i], reverse=not reverse)
        r = [0] * n
        for pos, idx in enumerate(order):
            r[idx] = pos / max(1, n - 1) * 100
        return r

    rp = rank([r["pct"] for r in rows])               # 动能
    rm = rank([r["mainflow"] for r in rows])          # 资金绝对
    rmp = rank([r["mainflow_pct"] for r in rows])     # 资金强度
    for i, r in enumerate(rows):
        r["s_mom"] = round(rp[i], 1)
        r["s_flow"] = round(rm[i], 1)
        r["s_flowpct"] = round(rmp[i], 1)
        r["score"] = round(0.40 * rp[i] + 0.30 * rm[i] + 0.30 * rmp[i], 1)
    return rows


def main():
    rows = grab_etfs()
    rows = score(rows)
    up = sum(1 for r in rows if r["pct"] > 0)
    dn = sum(1 for r in rows if r["pct"] < 0)
    total_flow = sum(r["mainflow"] for r in rows)
    top = sorted(rows, key=lambda x: x["score"], reverse=True)
    bot = sorted(rows, key=lambda x: x["score"])[:6]
    by_cata = {}
    for r in rows:
        by_cata.setdefault(r["cata"], []).append(r["pct"])
    cata_sum = {k: (sum(v) / len(v), len(v)) for k, v in by_cata.items()}

    out = {
        "date": time.strftime("%Y%m%d"),
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "count": len(rows),
        "up": up, "dn": dn,
        "total_flow": total_flow,
        "top": top[:12],
        "bot": bot,
        "cata": {k: {"avg": round(v[0], 2), "n": v[1]} for k, v in cata_sum.items()},
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("ETF 数据已生成: %s (%d 只, 涨%d/跌%d, 净流入%.2f亿)"
          % (OUT, len(rows), up, dn, total_flow / 1e8))


if __name__ == "__main__":
    main()
