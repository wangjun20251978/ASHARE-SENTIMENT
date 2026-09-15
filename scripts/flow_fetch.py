# -*- coding: utf-8 -*-
"""主力资金净流入榜抓取器 — 行业 / 概念 / 个股 净流入与净流出。
输出 data_flow.json 供 flow_render.py 使用。纯标准库，走东财延迟镜像。"""
import json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "data_flow.json"))


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore"))


def clist(fs, pz, po, fields="f12,f14,f3,f62,f184"):
    url = ("https://push2delay.eastmoney.com/api/qt/clist/get?pn=1&pz=%d&po=%d&np=1"
           "&fltt=2&invt=2&fid=f62&fs=%s&fields=%s" % (pz, po, fs, fields))
    d = fetch(url)
    return (d.get("data") or {}).get("diff") or []


def grab_board(kind):
    # 行业 m:90+t:2 ；概念 m:90+t:3
    fs = "m:90+t:2" if kind == "industry" else "m:90+t:3"
    rows = clist(fs, 12, 1)
    out = []
    for it in rows:
        out.append({
            "name": it.get("f14"),
            "pct": float(it.get("f3") or 0),
            "mainflow": float(it.get("f62") or 0),
            "mainflow_pct": float(it.get("f184") or 0),
        })
    return out


def grab_stock(po, pz=20):
    fs = "m:0+t:6,m:1+t:2"  # 沪A主板 + 深A主板
    rows = clist(fs, pz, po)
    out = []
    for it in rows:
        out.append({
            "code": it.get("f12"),
            "name": it.get("f14"),
            "pct": float(it.get("f3") or 0),
            "mainflow": float(it.get("f62") or 0),
            "mainflow_pct": float(it.get("f184") or 0),
        })
    return out


def main():
    industry_in = grab_board("industry")
    concept_in = grab_board("concept")
    stock_in = grab_stock(1, 20)     # 净流入 Top20
    stock_out = grab_stock(0, 20)    # 净流出 Top20

    out = {
        "date": time.strftime("%Y%m%d"),
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "industry_in": industry_in,
        "concept_in": concept_in,
        "stock_in": stock_in,
        "stock_out": stock_out,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("资金榜已生成: 行业%d / 概念%d / 个股净流入%d / 净流出%d"
          % (len(industry_in), len(concept_in), len(stock_in), len(stock_out)))


if __name__ == "__main__":
    main()
