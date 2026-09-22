# -*- coding: utf-8 -*-
"""大类资产夜盘温度计 — 外盘 ulist（push2delay）。输出 data_global.json。
确认可用：道指/标普/纳斯达克/美元指数/恒生/日经；黄金原油美债等候选项限速时可能缺失。"""
import json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "data_global.json"))

LABELS = {
    "DJIA": "道琼斯", "SPX": "标普500", "NDX": "纳斯达克", "UDI": "美元指数",
    "HSI": "恒生指数", "N225": "日经225", "GC00Y": "纽约金(COMEX)", "CL00Y": "纽约原油(WTI)",
    "USDCNY": "美元/人民币", "US10Y": "美债10年", "CN00Y": "富时中国A50",
}
GROUP = {
    "DJIA": "美股", "SPX": "美股", "NDX": "美股", "HSI": "亚太", "N225": "亚太", "CN00Y": "亚太",
    "UDI": "外汇", "USDCNY": "外汇", "GC00Y": "商品", "CL00Y": "商品", "US10Y": "债券",
}


def fetch(url, timeout=20):
    import _em
    return _em.fetch_json(url, timeout=timeout)


def ulist(secids, fields="f12,f13,f14,f2,f3,f4"):
    url = ("https://push2delay.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields=%s&secids=%s"
           % (fields, secids))
    d = fetch(url)
    data = d.get("data") or {}
    diff = data.get("diff")
    if isinstance(diff, dict):
        diff = list(diff.values())
    return diff if isinstance(diff, list) else []


def main():
    cands = ("100.DJIA,100.SPX,100.NDX,100.UDI,100.HSI,100.N225,"
             "100.GC00Y,100.CL00Y,100.USDCNY,100.US10Y,100.CN00Y")
    rows = ulist(cands)
    assets = []
    for it in rows:
        code = it.get("f12")
        if not code:
            continue
        assets.append({
            "code": code,
            "name": it.get("f14") or LABELS.get(code, code),
            "group": GROUP.get(code, "其他"),
            "price": float(it.get("f2") or 0),
            "chg": float(it.get("f3") or 0),
        })
    us = [a["chg"] for a in assets if a["group"] == "美股"]
    us_avg = round(sum(us) / len(us), 2) if us else 0.0
    out = {
        "date": time.strftime("%Y%m%d"),
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "assets": assets,
        "us_avg": us_avg,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("大类资产已生成: %d 项, 美股均涨 %.2f%%" % (len(assets), us_avg))


if __name__ == "__main__":
    main()
