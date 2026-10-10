# -*- coding: utf-8 -*-
"""本机一键更新器 —— 抓取 fundflow（资金流）/ ipo（次新股）两页并推送 GitHub。

为什么需要它：东方财富把 GitHub 服务器 IP 段封了，行业/概念/次新股板块接口
（m:90+t:2 / m:90+t:3 / b:BKxxxx）全部连不上，所以云端自动更新抓不到这 2 页。
你电脑的家庭宽带 IP 东财不封，在本机跑就能抓全量数据，再推回 GitHub 让网页更新。

用法：
  1) 装 Python 3.11（勾选 "Add to PATH"）
  2) 在 config.json 填你的 GitHub token（见 setup.md）
  3) 双击 run.bat，或在命令行 python local_update.py
可选：用 Windows 任务计划设每天 16:30 自动跑（setup.md 有步骤）
"""
import json, os, time, base64, urllib.request, sys

REPO = "wangjun20251978/ASHARE-SENTIMENT"
HERE = os.path.dirname(os.path.abspath(__file__))
# 东财延迟镜像，逐个重试提高成功率
MIRRORS = [
    "https://push2delay.eastmoney.com",
    "https://push2.eastmoney.com",
    "https://82.push2.eastmoney.com",
    "https://push2his.eastmoney.com",
]


def get_token():
    t = os.environ.get("GITHUB_TOKEN")
    if t:
        return t
    cfg = os.path.join(HERE, "config.json")
    if os.path.exists(cfg):
        try:
            return json.load(open(cfg, encoding="utf-8")).get("token")
        except Exception:
            pass
    return None


def em_get(path, timeout=20, tries=3):
    last = None
    for _ in range(tries):
        for host in MIRRORS:
            url = host + path
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0",
                             "Referer": "https://quote.eastmoney.com/"})
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    return json.loads(r.read().decode("utf-8", "ignore"))
            except Exception as e:
                last = e
                time.sleep(1.2)
    raise last


def clist(fs, pz, po, fields):
    sort_fid = "f62" if "f62" in fields else "f3"
    path = ("/api/qt/clist/get?pn=1&pz=%d&po=%d&np=1&fltt=2&invt=2&fid=%s"
            "&fs=%s&fields=%s" % (pz, po, sort_fid, fs, fields))
    d = em_get(path)
    return (d.get("data") or {}).get("diff") or []


def grab_flow():
    industry = [{"name": i.get("f14"), "pct": float(i.get("f3") or 0),
                 "mainflow": float(i.get("f62") or 0),
                 "mainflow_pct": float(i.get("f184") or 0)}
                for i in clist("m:90+t:2", 15, 1, "f12,f14,f3,f62,f184")]
    concept = [{"name": i.get("f14"), "pct": float(i.get("f3") or 0),
                "mainflow": float(i.get("f62") or 0),
                "mainflow_pct": float(i.get("f184") or 0)}
               for i in clist("m:90+t:3", 15, 1, "f12,f14,f3,f62,f184")]

    def stocks(po):
        out = []
        for it in clist("m:0+t:6,m:1+t:2", 20, po, "f12,f14,f3,f62,f184"):
            out.append({"code": it.get("f12"), "name": it.get("f14"),
                        "pct": float(it.get("f3") or 0),
                        "mainflow": float(it.get("f62") or 0),
                        "mainflow_pct": float(it.get("f184") or 0)})
        return out

    return {
        "date": time.strftime("%Y%m%d"),
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "industry_in": industry,
        "concept_in": concept,
        "stock_in": stocks(1),
        "stock_out": stocks(0),
    }


def grab_ipo():
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
    mem = [{"code": it.get("f12"), "name": it.get("f14"),
            "chg": float(it.get("f3") or 0)} for it in members]
    mem.sort(key=lambda x: -x["chg"])
    chgs = [x["chg"] for x in mem]
    avg = round(sum(chgs) / len(chgs), 2) if chgs else 0.0
    up = len([c for c in chgs if c > 0])
    return {
        "date": time.strftime("%Y%m%d"),
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "concept_name": concept.get("f14") if concept else "次新股",
        "concept_chg": float(concept.get("f3") or 0) if concept else 0,
        "count": len(mem),
        "up": up,
        "avg": avg,
        "members": mem[:40],
    }


def push(local_path, github_path):
    token = get_token()
    if not token:
        print("  [跳过推送] 缺少 GitHub token")
        return False
    sha = None
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/%s/contents/%s" % (REPO, github_path),
            headers={"Authorization": "token %s" % token,
                     "User-Agent": "local-updater",
                     "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            sha = json.loads(r.read()).get("sha")
    except Exception:
        pass
    data = open(local_path, "rb").read()
    body = {"message": "local update %s" % github_path,
            "content": base64.b64encode(data).decode()}
    if sha:
        body["sha"] = sha
    req = urllib.request.Request(
        "https://api.github.com/repos/%s/contents/%s" % (REPO, github_path),
        data=json.dumps(body).encode(),
        headers={"Authorization": "token %s" % token,
                 "User-Agent": "local-updater",
                 "Content-Type": "application/json",
                 "Accept": "application/vnd.github+json"},
        method="PUT")
    with urllib.request.urlopen(req, timeout=20) as r:
        print("  推送 %s -> HTTP %d" % (github_path, r.status))
    return True


def main():
    print("=== A股看板 本机更新器 ===")
    if not get_token():
        print("缺少 GitHub token：请在 local-updater 目录放 config.json "
              "（{\"token\":\"ghp_xxx\"}），或设环境变量 GITHUB_TOKEN")
        input("按回车退出")
        return
    ok = True
    try:
        fd = grab_flow()
        json.dump(fd, open(os.path.join(HERE, "data_flow.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("fundflow 抓取完成：行业%d / 概念%d / 个股净流入%d"
              % (len(fd["industry_in"]), len(fd["concept_in"]), len(fd["stock_in"])))
    except Exception as e:
        ok = False
        print("fundflow 失败：", e)
    try:
        ip = grab_ipo()
        json.dump(ip, open(os.path.join(HERE, "data_ipo.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("ipo 抓取完成：%s 成员%d 均涨%.2f%%"
              % (ip["concept_name"], ip["count"], ip["avg"]))
    except Exception as e:
        ok = False
        print("ipo 失败：", e)
    if ok:
        push(os.path.join(HERE, "data_flow.json"), "data_flow.json")
        push(os.path.join(HERE, "data_ipo.json"), "data_ipo.json")
        print("全部完成，网页几分钟后刷新。")
    else:
        print("部分失败，检查网络后重跑。")
    if sys.stdout.isatty():
        input("按回车退出")


if __name__ == "__main__":
    main()
