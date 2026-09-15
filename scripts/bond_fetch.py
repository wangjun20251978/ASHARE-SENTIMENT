# -*- coding: utf-8 -*-
"""转债市场温度计 — 可转债 clist（b:MK0354, push2delay）。
字段：f2 价格, f3 涨跌%, f238 转股溢价率, f239 纯债溢价率。输出 data_bond.json。"""
import json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "data_bond.json"))


def sf(v):
    try:
        return float(v)
    except Exception:
        return 0.0


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


def clist(fs, pz, po, fields="f12,f14,f2,f3,f238,f239"):
    url = ("https://push2delay.eastmoney.com/api/qt/clist/get?pn=1&pz=%d&po=%d&np=1"
           "&fltt=2&invt=2&fid=f3&fs=%s&fields=%s" % (pz, po, fs, fields))
    d = fetch(url)
    return (d.get("data") or {}).get("diff") or []


def main():
    rows = clist("b:MK0354", 400, 1)
    bonds = []
    for it in rows:
        bonds.append({
            "code": it.get("f12"),
            "name": it.get("f14"),
            "price": sf(it.get("f2")),
            "chg": sf(it.get("f3")),
            "prem": sf(it.get("f238")),     # 转股溢价率
            "pure": sf(it.get("f239")),      # 纯债溢价率
        })
    prems = [b["prem"] for b in bonds if b["prem"] != 0]
    prems_sorted = sorted(prems)
    med_prem = round(prems_sorted[len(prems_sorted) // 2], 1) if prems_sorted else 0
    avg_prem = round(sum(prems) / len(prems), 1) if prems else 0
    for b in bonds:
        b["dual"] = round(b["price"] + b["prem"], 1)
    dual_low = sorted([b for b in bonds if b["price"] > 0], key=lambda x: x["dual"])[:15]
    up_top = sorted([b for b in bonds if b["chg"] != 0], key=lambda x: -x["chg"])[:15]
    if avg_prem >= 50:
        temp_lb, temp_val = "估值偏贵·股性弱", min(100, int((avg_prem - 30) / 0.7))
    elif avg_prem >= 30:
        temp_lb, temp_val = "估值中性", int((avg_prem - 10) / 0.5)
    else:
        temp_lb, temp_val = "估值偏低·进攻性强", int(avg_prem / 0.5)
    temp_val = max(2, min(98, temp_val))
    out = {
        "date": time.strftime("%Y%m%d"),
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "count": len(bonds),
        "avg_prem": avg_prem,
        "med_prem": med_prem,
        "temp_lb": temp_lb,
        "temp_val": temp_val,
        "dual_low": dual_low,
        "up_top": up_top,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("转债已生成: %d 只, 平均溢价率 %.1f%%, 中位 %.1f%%" % (len(bonds), avg_prem, med_prem))


if __name__ == "__main__":
    main()
