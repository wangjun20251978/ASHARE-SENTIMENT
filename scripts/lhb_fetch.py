# -*- coding: utf-8 -*-
"""龙虎榜席位动向 — datacenter RPT_DAILYBILLBOARD_DETAILS。
注意：datacenter 接口在本沙箱环境可能被出口拦截，抓取失败则返回空列表（页面显示「数据暂缺」），
日更任务运行于海外服务器时通常可正常获取。输出 data_lhb.json。"""
import json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "data_lhb.json"))

COLS = ("SECURITY_CODE,SECURITY_NAME_ABBR,TRADE_DATE,EXPLAIN,CLOSE_PRICE,CHANGE_RATE,"
        "BILLBOARD_NET_AMT,BILLBOARD_BUY_AMT,BILLBOARD_SELL_AMT,ACCUM_AMOUNT,TURNOVERRATE,"
        "DEAL_NET_AMT,INTERVENE_LIST")


def fetch_lhb(timeout=25):
    url = ("https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_DAILYBILLBOARD_DETAILS"
           "&columns=%s&sortColumns=TRADE_DATE&sortTypes=-1&pageSize=50&source=WEB&client=WEB" % COLS)
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"})
            d = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore"))
            data = d.get("data")
            if isinstance(data, list):
                return data, True
            if isinstance(data, dict):
                x = data.get("diff")
                if isinstance(x, dict):
                    return list(x.values()), True
                if isinstance(x, list):
                    return x, True
            return [], False
        except Exception:
            time.sleep(2.2)
    return [], False


def main():
    raw, ok = fetch_lhb()
    items = []
    for it in raw:
        items.append({
            "code": it.get("SECURITY_CODE"),
            "name": it.get("SECURITY_NAME_ABBR"),
            "date": str(it.get("TRADE_DATE") or "")[:10],
            "reason": it.get("EXPLAIN") or "",
            "price": float(it.get("CLOSE_PRICE") or 0),
            "chg": float(it.get("CHANGE_RATE") or 0),
            "net": float(it.get("BILLBOARD_NET_AMT") or 0),
            "buy": float(it.get("BILLBOARD_BUY_AMT") or 0),
            "sell": float(it.get("BILLBOARD_SELL_AMT") or 0),
            "amount": float(it.get("ACCUM_AMOUNT") or 0),
            "turnover": float(it.get("TURNOVERRATE") or 0),
            "seats": it.get("INTERVENE_LIST") or "",
        })
    items.sort(key=lambda x: -x["net"])
    out = {
        "date": time.strftime("%Y%m%d"),
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "ok": ok,
        "count": len(items),
        "items": items,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("龙虎榜已生成: %d 条, 源可用=%s" % (len(items), ok))


if __name__ == "__main__":
    main()
