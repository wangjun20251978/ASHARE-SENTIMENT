#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股主线与情绪复盘 — 每日数据抓取器

数据源分工（全部为公开接口，纯标准库实现）：
  · 东方财富 push2delay  → 指数快照、板块行情、板块资金流（延迟行情，收盘后口径一致）
  · 东方财富 push2ex     → 涨停池 / 炸板池 / 跌停池（含连板数、所属行业、封板时间）
  · 东方财富 push2his    → 板块 5日/20日 涨幅（失败自动降级）
  · 腾讯行情             → 交易日序列、量能趋势

产出：data.json

用法：
    python scripts/fetch_data.py                 # 最近交易日
    python scripts/fetch_data.py --date 20260915 # 指定日期
"""

import urllib.request
import json
import time
import random
import socket
import sys
import os
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone

socket.setdefaulttimeout(25)

# ---------------------------------------------------------------- 网络基础

UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

# 延迟镜像对高频访问更宽容，放首位
HOST_PUSH2 = [
    "push2delay.eastmoney.com",
    "push2.eastmoney.com",
    "82.push2.eastmoney.com",
    "1.push2.eastmoney.com",
]
HOST_PUSH2EX = ["push2ex.eastmoney.com"]
HOST_HIS = ["push2his.eastmoney.com", "63.push2his.eastmoney.com"]

FETCH_GAP = 1.6
UT = "7eea3edcaed734bea9cbfc24409ed989"

_req_count = 0
_errors = []


def _raw(url, referer, tries, gap):
    """单 URL 带重试请求"""
    global _req_count
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": random.choice(UAS),
                "Referer": referer,
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Connection": "close",
            })
            with urllib.request.urlopen(req) as r:
                txt = r.read().decode("utf-8", errors="replace")
            _req_count += 1
            time.sleep(gap)
            return txt
        except Exception as e:
            last = e
            time.sleep(0.8 + i * 1.1 + random.random() * 0.4)
    raise RuntimeError(str(last))


def fetch_rotated(hosts, path, referer="https://quote.eastmoney.com/", tries=6):
    """在多个镜像域名间轮换重试，返回解析后的 JSON"""
    last = None
    for i in range(tries):
        h = hosts[i % len(hosts)]
        try:
            return json.loads(_raw("https://%s/%s" % (h, path), referer, tries=1, gap=FETCH_GAP))
        except Exception as e:
            last = e
            time.sleep(0.6 + i * 0.8)
    raise RuntimeError("mirror-exhausted %s | %s" % (path[:90], last))


def fetch_tencent(path, referer="https://gu.qq.com/", tries=4):
    return json.loads(_raw("https://web.ifzq.gtimg.cn/%s" % path, referer, tries=tries, gap=0.8))


def _seq(diff):
    if diff is None:
        return []
    if isinstance(diff, list):
        return diff
    return [diff[k] for k in sorted(diff.keys(), key=lambda x: int(x))]


def note_err(msg):
    _errors.append(msg)
    print("  [warn] " + msg, file=sys.stderr)


# ---------------------------------------------------------------- 交易日 / 量能

def tencent_kline(code="sh000001", n=30):
    """腾讯日K：返回 [(date, open, close, high, low, volume), ...]"""
    d = fetch_tencent("appstock/app/fqkline/get?param=%s,day,,,%d,qfq" % (code, n))
    node = d["data"][code]
    arr = node.get("qfqday") or node.get("day") or []
    out = []
    for row in arr:
        try:
            out.append((row[0], float(row[1]), float(row[2]), float(row[3]),
                        float(row[4]), float(row[5])))
        except Exception:
            continue
    return out


def trade_days(code="sh000001", n=30):
    kl = tencent_kline(code, n)
    return [r[0].replace("-", "") for r in kl]


# ---------------------------------------------------------------- 抓取

def grab_indexes():
    """指数快照。f104/f105/f106 = 该指数覆盖市场的上涨/下跌/平盘家数。"""
    secids = "1.000001,0.399001,0.399006,1.000688,0.399905,1.000016"
    path = ("api/qt/ulist.np/get?fltt=2&secids=%s&fields=f2,f3,f4,f6,f12,f14,f104,f105,f106" % secids)
    d = fetch_rotated(HOST_PUSH2, path)
    out = []
    for r in _seq(d["data"]["diff"]):
        out.append({
            "code": r.get("f12"), "name": r.get("f14"),
            "price": r.get("f2"), "pct": r.get("f3"),
            "chg": r.get("f4"), "amount": r.get("f6"),
            "up": r.get("f104"), "down": r.get("f105"), "flat": r.get("f106"),
        })
    return out


def grab_pool(kind, date):
    """kind: ZT 涨停 / ZB 炸板 / DT 跌停"""
    path = ("getTopic%sPool?ut=%s&dpt=wz.ztzt&Pageindex=0&pagesize=400&sort=fbt%%3Aasc&date=%s"
            % (kind, UT, date))
    d = fetch_rotated(HOST_PUSH2EX, path)
    data = d.get("data") or {}
    return int(data.get("tc") or 0), (data.get("pool") or [])


def grab_boards(fs, pages=6, pz=90):
    fields = "f3,f12,f14,f62,f104,f105,f184"
    rows = []
    for pn in range(1, pages + 1):
        path = ("api/qt/clist/get?pn=%d&pz=%d&po=1&np=1&fltt=2&invt=2&fid=f3&fs=%s&fields=%s"
                % (pn, pz, fs, fields))
        try:
            d = fetch_rotated(HOST_PUSH2, path)
        except Exception as e:
            note_err("板块分页 %d 失败: %s" % (pn, str(e)[:80]))
            break
        data = d.get("data") or {}
        seq = _seq(data.get("diff"))
        rows.extend(seq)
        if len(seq) < pz:
            break
    return [{
        "code": r.get("f12"), "name": r.get("f14"),
        "pct": r.get("f3"), "netflow": r.get("f62"),
        "up": r.get("f104"), "down": r.get("f105"),
        "netrate": r.get("f184"),
    } for r in rows]


def grab_board_kline(bkcode, lmt=25):
    path = ("api/qt/stock/kline/get?secid=90.%s&fields1=f1,f2,f3&fields2=f51,f53"
            "&klt=101&fqt=1&end=20500101&lmt=%d" % (bkcode, lmt))
    d = fetch_rotated(HOST_HIS, path, tries=3)
    kl = d["data"].get("klines") or []
    return [(k.split(",")[0], float(k.split(",")[1])) for k in kl]


# ---------------------------------------------------------------- 指标

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def compute_sentiment(zt_cnt, zb_cnt, max_lb, promote_rate):
    """情绪温度 0-10：涨停家数30 + 封板率25 + 连板高度25 + 晋级率20"""
    seal_rate = zt_cnt / (zt_cnt + zb_cnt) if (zt_cnt + zb_cnt) else 0.0
    s_zt = clamp(zt_cnt / 100.0)
    s_seal = clamp((seal_rate - 0.40) / 0.50)
    s_lb = clamp((max_lb - 2) / 6.0)
    s_prom = clamp((promote_rate - 0.10) / 0.45)
    raw = s_zt * 30 + s_seal * 25 + s_lb * 25 + s_prom * 20
    temp = round(raw / 10.0, 1)
    if temp < 2:
        label, tone = "冰点", "cold"
    elif temp < 3.5:
        label, tone = "冷", "cold"
    elif temp < 5.5:
        label, tone = "中性", "mid"
    elif temp < 7.5:
        label, tone = "热", "hot"
    else:
        label, tone = "沸腾", "hot"
    return {
        "temp": temp, "label": label, "tone": tone,
        "seal_rate": round(seal_rate * 100, 1),
        "detail": {
            "zt": round(s_zt * 30, 1), "seal": round(s_seal * 25, 1),
            "lb": round(s_lb * 25, 1), "prom": round(s_prom * 20, 1),
        },
    }


# ---------------------------------------------------------------- 主流程

def build(args):
    today = args.date
    log = []

    # --- 交易日序列（腾讯）
    days = []
    try:
        days = trade_days("sh000001", 30)
        log.append("交易日序列 %d 个（腾讯），最新 %s" % (len(days), days[-1] if days else "?"))
    except Exception as e:
        note_err("交易日序列失败: %s" % str(e)[:90])

    if not days:
        days = [today]
    days = [d for d in days if d <= today]
    if not days:
        days = [today]
    cur = days[-1]
    prev = days[-2] if len(days) >= 2 else None
    log.append("复盘日期 %s，前一交易日 %s" % (cur, prev or "—"))

    # --- 指数快照
    indexes = []
    try:
        indexes = grab_indexes()
        log.append("指数 %d 个" % len(indexes))
    except Exception as e:
        note_err("指数快照失败: %s" % str(e)[:90])

    # --- 三池
    zt_cnt, zt_pool = 0, []
    zb_cnt, zb_pool = 0, []
    dt_cnt, dt_pool = 0, []
    for kind, holder in (("ZT", "zt"), ("ZB", "zb"), ("DT", "dt")):
        try:
            c, p = grab_pool(kind, cur)
            if kind == "ZT":
                zt_cnt, zt_pool = c, p
            elif kind == "ZB":
                zb_cnt, zb_pool = c, p
            else:
                dt_cnt, dt_pool = c, p
        except Exception as e:
            note_err("%s池失败: %s" % (kind, str(e)[:90]))
    log.append("涨停 %d / 炸板 %d / 跌停 %d" % (zt_cnt, zb_cnt, dt_cnt))

    zt_prev_cnt = 0
    if prev:
        try:
            zt_prev_cnt, _ = grab_pool("ZT", prev)
            log.append("昨日(%s)涨停 %d 家" % (prev, zt_prev_cnt))
        except Exception as e:
            note_err("昨日涨停池失败: %s" % str(e)[:90])

    # --- 连板结构
    lb_counter = Counter()
    for s in zt_pool:
        lb_counter[int(s.get("lbc") or 0)] += 1
    max_lb = max(lb_counter) if lb_counter else 0
    promote_cnt = sum(c for k, c in lb_counter.items() if k >= 2)
    promote_rate = (promote_cnt / zt_prev_cnt) if zt_prev_cnt else 0.0

    sentiment = compute_sentiment(zt_cnt, zb_cnt, max_lb, promote_rate)

    # --- 板块
    industries, concepts = [], []
    try:
        industries = grab_boards("m:90+t:2", pages=6, pz=90)
        log.append("行业板块 %d 个" % len(industries))
    except Exception as e:
        note_err("行业板块失败: %s" % str(e)[:90])
    try:
        concepts = grab_boards("m:90+t:3", pages=2, pz=40)
        log.append("概念板块 %d 个" % len(concepts))
    except Exception as e:
        note_err("概念板块失败: %s" % str(e)[:90])

    # --- 市场广度：取沪深两市指数的涨跌家数（不重叠，口径准确）
    up_total = down_total = flat_total = 0
    try:
        idx_map = {i["name"]: i for i in indexes}
        for nm in ("上证指数", "深证成指"):
            node = idx_map.get(nm) or {}
            up_total += int(node.get("up") or 0)
            down_total += int(node.get("down") or 0)
            flat_total += int(node.get("flat") or 0)
        if up_total or down_total:
            log.append("市场广度 涨 %d / 跌 %d / 平 %d" % (up_total, down_total, flat_total))
        else:
            note_err("广度字段为空")
    except Exception as e:
        note_err("广度计算失败: %s" % str(e)[:80])

    # --- 涨幅榜补 5日/20日（push2his，失败自动降级）
    top_boards = sorted([b for b in industries if b.get("pct") is not None],
                        key=lambda x: x["pct"], reverse=True)[:10]
    top_concepts = sorted([c for c in concepts if c.get("pct") is not None],
                          key=lambda x: x["pct"], reverse=True)[:8]
    his_ok = 0
    targets = top_boards[:6] + top_concepts[:4]
    his_available = bool(targets)
    if targets:
        # 先探测一次，数据源不可用则整体跳过，避免无谓重试
        try:
            grab_board_kline(targets[0]["code"], lmt=5)
        except Exception:
            his_available = False
            note_err("板块多周期数据源不可用，跳过 5日/20日")
    if his_available:
        for b in targets:
            try:
                kl = grab_board_kline(b["code"], lmt=25)
                if len(kl) >= 6 and kl[-6][1]:
                    b["pct5"] = round((kl[-1][1] / kl[-6][1] - 1) * 100, 2)
                if len(kl) >= 21 and kl[-21][1]:
                    b["pct20"] = round((kl[-1][1] / kl[-21][1] - 1) * 100, 2)
                his_ok += 1
            except Exception:
                pass
            time.sleep(0.3)
    log.append("板块多周期涨幅：成功 %d / 尝试 %d" % (his_ok, len(targets)))

    # --- 量能趋势（腾讯成交量，单位：手）
    amt_hist = []
    try:
        kl_sh = tencent_kline("sh000001", 12)
        kl_sz = tencent_kline("sz399001", 12)
        sz_map = {r[0]: r[5] for r in kl_sz}
        for r in kl_sh[-6:]:
            amt_hist.append([r[0], r[5] + sz_map.get(r[0], 0.0)])
        log.append("量能序列 %d 日" % len(amt_hist))
    except Exception as e:
        note_err("量能序列失败: %s" % str(e)[:90])

    # 当日两市成交额（东财指数快照 f6 = 各自成交额）
    turnover_today = None
    try:
        idx = {i["name"]: i for i in indexes}
        a1 = (idx.get("上证指数") or {}).get("amount")
        a2 = (idx.get("深证成指") or {}).get("amount")
        if a1 and a2:
            turnover_today = float(a1) + float(a2)
    except Exception:
        pass

    # --- 涨停行业分布
    hy_counter = Counter((s.get("hybk") or "其他").strip() for s in zt_pool)

    # --- 高度龙头
    leaders = sorted(zt_pool, key=lambda x: (int(x.get("lbc") or 0), x.get("lbt") or 0), reverse=True)[:8]

    data = {
        "date": cur,
        "prev_date": prev,
        "generated": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M"),
        "indexes": indexes,
        "amount_hist": amt_hist,
        "turnover_today": turnover_today,
        "zt_count": zt_cnt, "zb_count": zb_cnt, "dt_count": dt_cnt,
        "zt_prev_count": zt_prev_cnt,
        "lb_counter": {str(k): v for k, v in lb_counter.items()},
        "max_lb": max_lb,
        "promote_count": promote_cnt,
        "promote_rate": round(promote_rate * 100, 1),
        "sentiment": sentiment,
        "industries": industries,
        "concepts": concepts,
        "top_boards": top_boards,
        "top_concepts": top_concepts,
        "breadth": {"up": up_total, "down": down_total},
        "zt_pool": zt_pool,
        "zb_pool": zb_pool,
        "dt_pool": dt_pool,
        "hy_counter": dict(hy_counter),
        "leaders": leaders,
        "log": log,
        "errors": _errors,
    }
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYYMMDD")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if not args.date:
        args.date = datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d")

    data = build(args)

    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.abspath(args.out or os.path.join(here, "..", "data.json"))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("=" * 62)
    for line in data["log"]:
        print("  " + line)
    print("=" * 62)
    print("日期 %s | 前一交易日 %s" % (data["date"], data["prev_date"]))
    s = data["sentiment"]
    print("情绪温度 %.1f/10 (%s) | 封板率 %.1f%%" % (s["temp"], s["label"], s["seal_rate"]))
    print("连板高度 %d 板 | 晋级率 %.1f%% (%d家连板/%d家昨涨停)"
          % (data["max_lb"], data["promote_rate"], data["promote_count"], data["zt_prev_count"]))
    print("涨停行业 Top5:", Counter(data["hy_counter"]).most_common(5))
    print("请求数 %d | 警告 %d" % (_req_count, len(_errors)))

    # --- 健康检查：关键数据缺失则视为失败，避免产出空报告
    problems = []
    if not data["indexes"]:
        problems.append("指数数据为空")
    if not data["industries"]:
        problems.append("行业板块为空")
    if data["zt_count"] == 0 and data["dt_count"] == 0 and data["zb_count"] == 0:
        problems.append("涨停/炸板/跌停三池全空（数据源异常或休市）")
    if data["sentiment"]["temp"] == 0 and data["zt_count"] == 0:
        problems.append("情绪指标无法计算")
    if problems:
        print()
        print("!! 健康检查未通过: " + "；".join(problems))
        print("!! 已写出 data.json 供排查，但请勿据此发布。")
        sys.exit(2)

    print("已写入:", out)


if __name__ == "__main__":
    main()
