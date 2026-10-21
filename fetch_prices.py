import json, os, sys, datetime, urllib.request, urllib.parse
mode = sys.argv[1] if len(sys.argv) > 1 else "quotes"
NOW = datetime.datetime.utcnow()
TODAY = NOW.strftime("%Y-%m-%d")
AFTER_CLOSE = NOW.hour * 60 + NOW.minute >= 16 * 60 + 10   # po zamknieciu GPW takze zima (16:05 UTC)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36", "Accept": "*/*"}
SUF = {".pl": ".WA", ".uk": ".L", ".de": ".DE", ".us": ""}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "replace")


def norm(t):
    return t if ("." in t or (len(t) == 6 and t.endswith("pln"))) else t + ".pl"


def ysym(s):
    if len(s) == 6 and s.endswith("pln"):
        return s.upper() + "=X"
    for k, v in SUF.items():
        if s.endswith(k):
            return s[:-len(k)].upper() + v
    return s.upper()


def yahoo(sym):
    err = "brak odpowiedzi"
    for host in ("query1", "query2"):
        try:
            j = json.loads(get("https://%s.finance.yahoo.com/v8/finance/chart/%s?range=3y&interval=1d" % (host, urllib.parse.quote(sym))))
            r = j["chart"]["result"][0]
            m = r["meta"]
            price, off, closes = float(m["regularMarketPrice"]), m.get("gmtoffset", 0), {}
            for ts, c in zip(r.get("timestamp", []), r["indicators"]["quote"][0]["close"]):
                if c is not None:
                    closes[datetime.datetime.utcfromtimestamp(ts + off).strftime("%Y-%m-%d")] = float(c)
            return price, closes
        except Exception as e:
            err = "yahoo %s: %s" % (host, e)
    raise Exception(err)


def stooq(s):
    err = "brak danych"
    for host in ("stooq.pl", "stooq.com"):
        try:
            row = get("https://%s/q/l/?s=%s&f=sd2t2ohlcv&h&e=csv" % (host, s)).strip().split("\n")[1].split(",")
            v = float(row[6])
            if v > 0:
                closes = {}
                if mode == "all":
                    try:
                        txt = get("https://stooq.com/q/d/l/?s=%s&i=d&d1=20230101&d2=%s" % (s, NOW.strftime("%Y%m%d")))
                        if txt.startswith("Date"):
                            for l in txt.strip().split("\n")[1:]:
                                c = l.split(",")
                                closes[c[0]] = float(c[4])
                    except Exception:
                        pass
                return v, closes
        except Exception as e:
            err = "stooq %s: %s" % (host, e)
    raise Exception(err)


items = []
for line in open("tickers.txt", encoding="utf-8"):
    t = line.split("#")[0].strip().lower()
    if not t:
        continue
    k, _, y = t.partition("=")
    k = norm(k.strip())
    items.append((k, y.strip().upper() or ysym(k)))
p, errs, h = {}, [], {}
if os.path.exists("history.json"):
    try:
        h = json.load(open("history.json", encoding="utf-8")).get("h", {})
    except Exception:
        h = {}
for s, y in items:
    try:
        try:
            price, closes = yahoo(y)
            src = "yahoo " + y
        except Exception as e1:
            try:
                price, closes = stooq(s)
                src = "stooq (yahoo: %s)" % str(e1)[:60]
            except Exception as e2:
                raise Exception("%s | %s" % (e1, e2))
        p[s] = price
        if mode == "all":
            d = h.setdefault(s, {})
            for date, c in closes.items():
                if date < TODAY or AFTER_CLOSE:
                    d[date] = c
        last = max(closes) if closes else "-"
        print("OK  %-14s %10.2f  %s  historia=%d ostatnia=%s" % (s, price, src, len(closes), last))
    except Exception as e:
        errs.append(s)
        print("BLAD %-14s %s" % (s, e))
if not p:
    sys.exit("Brak notowan - nie zapisuje plikow")
now = NOW.isoformat(timespec="minutes")
json.dump({"u": now, "p": p}, open("prices.json", "w"))
if mode == "all":
    json.dump({"u": now, "h": h}, open("history.json", "w"), separators=(",", ":"))
print("Zapisano:", len(p), "z", len(items), "symboli; bledy:", errs)
