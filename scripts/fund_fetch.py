# -*- coding: utf-8 -*-
"""基金净值/重仓追踪 — ETF 走 ulist 直查 secid（push2delay，稳健）；
开放式基金（如 015071 专特新量化）走 fundgz 净值接口（best-effort，本环境可能不通，海外日更或通）。
输出 data_fund.json。"""
import json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "data_fund.json"))

# ETF：secid 1.=沪 0.=深
ETF_TRACK = [
    ("515260", "1.515260", "电子ETF华宝", "电子化学品·持有"),
    ("588000", "1.588000", "科创50ETF", "关注·宽基"),
    ("510300", "1.510300", "沪深300ETF", "关注·宽基"),
    ("512100", "1.512100", "中证1000ETF", "关注·宽基"),
    ("159915", "0.159915", "创业板ETF", "关注·宽基"),
    ("518880", "1.518880", "黄金ETF", "关注·避险"),
]
# 开放式基金（非交易，需净值接口）
OPEN_TRACK = [
    ("015071", "鑫元专精特新混合A", "专特新量化·持有"),
]


def fetch(url, timeout=20, ref="https://quote.eastmoney.com/"):
    last = None
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": ref})
            return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
        except Exception as e:
            last = e
            time.sleep(1.6)
    return ""


def ulist(secids, fields="f12,f14,f2,f3"):
    url = ("https://push2delay.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields=%s&secids=%s"
           % (fields, secids))
    d = json.loads(fetch(url) or "{}")
    data = d.get("data") or {}
    diff = data.get("diff")
    if isinstance(diff, dict):
        diff = list(diff.values())
    return diff if isinstance(diff, list) else []


def fundgz(code):
    """开放式基金净值（best-effort）。返回 (nav, chg) 或 (None, None)。"""
    url = "https://fundgz.eastmoney.com/fsjj?code=%s" % code
    raw = fetch(url, ref="https://fundf10.eastmoney.com/")
    if not raw:
        return None, None
    s = raw.strip()
    if s.startswith("jsonp"):
        s = s[s.index("(") + 1:]
        if s.rstrip().endswith(");"):
            s = s.rstrip()[:-2]
    try:
        d = json.loads(s)
    except Exception:
        return None, None
    dwjz = float(d.get("dwjz") or 0)
    gsz = float(d.get("gsz") or 0)
    chg = round((gsz - dwjz) / dwjz * 100, 2) if dwjz else 0.0
    return dwjz, chg


def main():
    out_funds = []
    # ETF（稳健）
    secids = ",".join(s for _, s, _, _ in ETF_TRACK)
    rows = ulist(secids)
    m = {it.get("f12"): it for it in rows}
    for code, _, name, tag in ETF_TRACK:
        it = m.get(code)
        if not it:
            continue
        out_funds.append({
            "code": code, "name": name, "tag": tag,
            "nav": float(it.get("f2") or 0),
            "chg": float(it.get("f3") or 0),
            "y1": 0,
        })
    # 开放式（best-effort）
    for code, name, tag in OPEN_TRACK:
        nav, chg = fundgz(code)
        out_funds.append({
            "code": code, "name": name, "tag": tag,
            "nav": nav if nav is not None else 0,
            "chg": chg if chg is not None else 0,
            "y1": 0, "ok": nav is not None,
        })
    out = {
        "date": time.strftime("%Y%m%d"),
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "funds": out_funds,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("基金已生成: %d 只" % len(out_funds))


if __name__ == "__main__":
    main()
