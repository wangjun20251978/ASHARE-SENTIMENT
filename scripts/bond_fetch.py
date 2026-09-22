# -*- coding: utf-8 -*-
"""转债市场温度计 — 可转债 clist（b:MK0354, push2delay）。
字段：f2 价格, f3 涨跌%, f238 转股溢价率, f239 纯债溢价率。输出 data_bond.json。
v2：抓全市场（pz=650），并生成双低观察池信号（已入区 / 接近开启 / 黄金区）。"""
import json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "data_bond.json"))

TH_IN = 120.0    # 双低入区阈值
TH_NEAR = 130.0  # 接近开启上界


def sf(v):
    try:
        return float(v)
    except Exception:
        return 0.0


def fetch(url, timeout=20):
    import _em
    return _em.fetch_json(url, timeout=timeout)


def clist_all(fs, fields="f12,f14,f2,f3,f238,f239", page=100, max_pages=12):
    """clist 单页上限 100 条，翻页抓全"""
    rows, pn = [], 1
    while pn <= max_pages:
        url = ("https://push2delay.eastmoney.com/api/qt/clist/get?pn=%d&pz=%d&po=1&np=1"
               "&fltt=2&invt=2&fid=f12&fs=%s&fields=%s" % (pn, page, fs, fields))
        batch = (fetch(url).get("data") or {}).get("diff") or []
        if isinstance(batch, dict):
            batch = list(batch.values())
        rows.extend(batch)
        if len(batch) < page:
            break
        pn += 1
        time.sleep(1.2)
    return rows


def signal_of(b):
    """双低策略信号：黄金区 > 已入区 > 接近开启 > 观察"""
    if 0 < b["price"] < 110 and b["prem"] < 20:
        return "黄金区"
    if b["dual"] < TH_IN:
        return "已入区"
    if b["dual"] < TH_NEAR:
        return "接近开启"
    return "观察"


def main():
    rows = clist_all("b:MK0354")
    bonds = []
    for it in rows:
        price = sf(it.get("f2"))
        if price <= 0:
            continue
        b = {
            "code": it.get("f12"),
            "name": it.get("f14"),
            "price": price,
            "chg": sf(it.get("f3")),
            "prem": sf(it.get("f238")),     # 转股溢价率
            "pure": sf(it.get("f239")),      # 纯债溢价率
        }
        b["dual"] = round(b["price"] + b["prem"], 1)
        b["sig"] = signal_of(b)
        bonds.append(b)

    prems = [b["prem"] for b in bonds if b["prem"] != 0]
    prems_sorted = sorted(prems)
    med_prem = round(prems_sorted[len(prems_sorted) // 2], 1) if prems_sorted else 0
    avg_prem = round(sum(prems) / len(prems), 1) if prems else 0

    dual_sorted = sorted(bonds, key=lambda x: x["dual"])
    dual_low = dual_sorted[:15]                       # 双低 Top15（带信号）
    near_open = [b for b in dual_sorted if b["sig"] == "接近开启"][:10]   # 接近开启名单
    gold = [b for b in dual_sorted if b["sig"] == "黄金区"][:10]          # 黄金区名单
    n_in = len([b for b in bonds if b["sig"] == "已入区"])
    n_gold = len([b for b in bonds if b["sig"] == "黄金区"])
    n_near = len([b for b in bonds if b["sig"] == "接近开启"])
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
        "n_in": n_in, "n_gold": n_gold, "n_near": n_near,
        "dual_low": dual_low,
        "near_open": near_open,
        "gold": gold,
        "up_top": up_top,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("转债已生成: %d 只, 平均溢价率 %.1f%%, 中位 %.1f%% | 已入区%d 黄金区%d 接近开启%d"
          % (len(bonds), avg_prem, med_prem, n_in, n_gold, n_near))


if __name__ == "__main__":
    main()
