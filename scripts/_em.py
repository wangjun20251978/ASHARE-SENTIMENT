# -*- coding: utf-8 -*-
"""东财公开接口多镜像容错请求器 — 供各 fetch 脚本复用。

背景：东财对 GitHub Actions 的出口 IP 有偶发限流，单域名脚本一抖就崩、
导致整份数据停在旧缓存。本模块在多个 push2/push2delay 镜像间轮换重试，
大幅提升在 Actions 上的成功率。接口返回已解析的 JSON；全部镜像耗尽则抛 RuntimeError。
"""
import json
import time
import random
import urllib.request

# 多个镜像域名轮换（push2delay 为延迟镜像，对高频更宽容，放首位）
HOSTS = [
    "push2delay.eastmoney.com",
    "push2.eastmoney.com",
    "82.push2.eastmoney.com",
    "1.push2.eastmoney.com",
    "7.push2.eastmoney.com",
    "13.push2.eastmoney.com",
    "push2his.eastmoney.com",
    "63.push2his.eastmoney.com",
]

UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def fetch_json(url, timeout=20, tries=8):
    """在多个东财镜像域名间轮换重试，返回解析后的 JSON。失败抛 RuntimeError。"""
    if "://" in url:
        scheme, rest = url.split("://", 1)
    else:
        scheme, rest = "https", url
    if "/" in rest:
        host, path = rest.split("/", 1)
    else:
        host, path = rest, ""
    path = "/" + path

    last = None
    for i in range(tries):
        h = HOSTS[i % len(HOSTS)]
        full = "%s://%s%s" % (scheme, h, path)
        try:
            req = urllib.request.Request(full, headers={
                "User-Agent": random.choice(UAS),
                "Referer": "https://quote.eastmoney.com/",
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Connection": "close",
            })
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "ignore"))
        except Exception as e:
            last = e
            time.sleep(0.6 + i * 0.7 + random.random() * 0.4)
    raise RuntimeError("em-mirror-exhausted %s | %s" % (url[:90], last))


if __name__ == "__main__":
    d = fetch_json("https://push2delay.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fltt=2&invt=2&fid=f62&fs=m:90+t:2&fields=f12,f14,f3")
    print("self-test OK, diff:", len((d.get("data") or {}).get("diff") or []))
