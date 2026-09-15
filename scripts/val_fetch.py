# -*- coding: utf-8 -*-
"""指数估值分位看板 — 主要指数 ulist（push2delay）+ 定性估值带。输出 data_val.json。
说明：指数 PE/PB 在公开 push2 接口取不到实时分位，故以「近期 PE 参考区间 + 定性结论」呈现，
涨跌幅为每日真实更新。如需精确历史分位，需接入估值数据中心（本环境不稳）。"""
import json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "data_val.json"))

# 主要指数（secid: 1.=沪 0.=深）；ulist 返回 f12 为 6 位代码
IDX = [
    ("1.000001", "000001", "上证指数"),
    ("1.000300", "000300", "沪深300"),
    ("0.399006", "399006", "创业板指"),
    ("1.000905", "000905", "中证500"),
    ("1.000688", "000688", "科创50"),
    ("1.000016", "000016", "上证50"),
    ("1.000852", "000852", "中证1000"),
    ("0.399001", "399001", "深证成指"),
]
# 定性估值带（参考近期 PE 区间，2026-09 参考值）：低估上限 / 合理上限；>合理上限=偏高
VAL = {
    "上证指数": (13, 15), "沪深300": (12, 14), "创业板指": (32, 45), "中证500": (22, 28),
    "科创50": (45, 60), "上证50": (10, 12), "中证1000": (30, 40), "深证成指": (24, 30),
}
# 定性结论（基于近期 PE 水平的静态判断，非实时分位）
VERDICT = {
    "上证指数": "合理偏低", "沪深300": "合理偏低", "创业板指": "合理", "中证500": "合理偏低",
    "科创50": "偏高", "上证50": "合理偏低", "中证1000": "合理", "深证成指": "合理",
}


def fetch(url, timeout=20):
    last = None
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore"))
        except Exception as e:
            last = e
            time.sleep(1.6)
    raise last


def ulist(secids, fields="f12,f14,f2,f3"):
    url = ("https://push2delay.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields=%s&secids=%s"
           % (fields, secids))
    d = fetch(url)
    data = d.get("data") or {}
    diff = data.get("diff")
    if isinstance(diff, dict):
        diff = list(diff.values())
    return diff if isinstance(diff, list) else []


def main():
    secids = ",".join(c for c, _, _ in IDX)
    rows = ulist(secids)
    m = {it.get("f12"): it for it in rows}
    out_idx = []
    for _, code, name in IDX:
        it = m.get(code)
        lo, hi = VAL.get(name, (0, 0))
        out_idx.append({
            "code": code,
            "name": name,
            "point": float(it.get("f2") or 0) if it else 0,
            "chg": float(it.get("f3") or 0) if it else 0,
            "pe_low": lo,
            "pe_high": hi,
            "band": VERDICT.get(name, "—"),
        })
    out = {
        "date": time.strftime("%Y%m%d"),
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "indices": out_idx,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("估值看板已生成: %d 个指数" % len(out_idx))


if __name__ == "__main__":
    main()
