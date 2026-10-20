import json, os, sys, datetime, urllib.request
mode = sys.argv[1] if len(sys.argv) > 1 else "quotes"
TODAY = datetime.date.today()


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")


def norm(t):
    return t if ("." in t or (len(t) == 6 and t.endswith("pln"))) else t + ".pl"


syms = []
for line in open("tickers.txt", encoding="utf-8"):
    t = line.split("#")[0].strip().lower()
    if t:
        syms.append(norm(t))
p, errs, h = {}, [], {}
if os.path.exists("history.json"):
    try:
        h = json.load(open("history.json", encoding="utf-8")).get("h", {})
    except Exception:
        h = {}
for s in syms:
    last, err = None, "brak danych"
    for host in ("stooq.pl", "stooq.com"):
        try:
            row = get("https://%s/q/l/?s=%s&f=sd2t2ohlcv&h&e=csv" % (host, s)).strip().split("\n")[1].split(",")
            v = float(row[6])
            if v > 0:
                last = (v, row[1])
                break
        except Exception as e:
            err = host + ": " + str(e)
    if not last:
        errs.append(s + " notowanie: " + err)
        continue
    p[s] = last[0]
    if mode == "all":
        d = h.setdefault(s, {})
        if len(last[1]) == 10:
            d[last[1]] = last[0]
        if len(d) < 30:
            try:
                txt = get("https://stooq.com/q/d/l/?s=%s&i=d&d1=20230101&d2=%s" % (s, TODAY.strftime("%Y%m%d")))
                if not txt.startswith("Date"):
                    raise Exception(txt.strip()[:80])
                for l in txt.strip().split("\n")[1:]:
                    c = l.split(",")
                    d[c[0]] = float(c[4])
            except Exception as e:
                errs.append(s + " historia: " + str(e))
if errs:
    print("Bledy:\n" + "\n".join(errs))
if not p:
    sys.exit("Brak notowan - nie zapisuje plikow")
now = datetime.datetime.utcnow().isoformat(timespec="minutes")
json.dump({"u": now, "p": p}, open("prices.json", "w"))
if mode == "all":
    json.dump({"u": now, "h": h}, open("history.json", "w"), separators=(",", ":"))
print("OK", mode, p)
