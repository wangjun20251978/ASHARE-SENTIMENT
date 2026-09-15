# -*- coding: utf-8 -*-
"""新股/次新复盘 — 次新股概念强度（push2delay 概念板）。
两步：1) 概念列表找「次新股」code；2) 取该概念成员按涨跌幅排序。输出 data_ipo.json。"""
import json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "data_ipo.json"))


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


def clist(fs, pz, po, fields="f12,f14,f3"):
    url = ("https://push2delay.eastmoney.com/api/qt/clist/get?pn=1&pz=%d&po=%d&np=1"
           "&fltt=2&invt=2&fid=f3&fs=%s&fields=%s" % (pz, po, fs, fields))
    d = fetch(url)
    return (d.get("data") or {}).get("diff") or []


def main():
    # 1) 概念列表
    concepts = clist("m:90+t:3", 400, 1, "f12,f14,f3")
    cx = [c for c in concepts if "次新" in (c.get("f14") or "")]
    concept = cx[0] if cx else None
    members = []
    if concept:
        bcode = concept.get("f12")
        try:
            members = clist("b:%s" % bcode, 80, 1, "f12,f14,f3")
        except Exception:
            members = []
    mem = []
    for it in members:
        mem.append({
            "code": it.get("f12"),
            "name": it.get("f14"),
            "chg": float(it.get("f3") or 0),
        })
    mem.sort(key=lambda x: -x["chg"])
    chgs = [x["chg"] for x in mem]
    avg = round(sum(chgs) / len(chgs), 2) if chgs else 0.0
    up = len([c for c in chgs if c > 0])
    out = {
        "date": time.strftime("%Y%m%d"),
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "concept_name": concept.get("f14") if concept else "次新股",
        "concept_chg": float(concept.get("f3") or 0) if concept else 0,
        "count": len(mem),
        "up": up,
        "avg": avg,
        "members": mem[:40],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("次新已生成: 概念 %s, 成员 %d, 均涨 %.2f%%" % (out["concept_name"], len(mem), avg))


if __name__ == "__main__":
    main()
