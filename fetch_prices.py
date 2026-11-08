import json, os, sys, time, datetime
import yfinance as yf

mode = sys.argv[1] if len(sys.argv) > 1 else "quotes"
NOW = datetime.datetime.now(datetime.timezone.utc)
TODAY = NOW.strftime("%Y-%m-%d")
AFTER_CLOSE = NOW.hour * 60 + NOW.minute >= 16 * 60 + 10   # po zamknieciu GPW takze zima (16:05 UTC)
SUF = {".pl": ".WA", ".uk": ".L", ".de": ".DE", ".us": ""}


def norm(t):
    return t if ("." in t or (len(t) == 6 and t.endswith("pln"))) else t + ".pl"


def ysym(s):
    if len(s) == 6 and s.endswith("pln"):
        return s.upper() + "=X"
    for k, v in SUF.items():
        if s.endswith(k):
            return s[:-len(k)].upper() + v
    return s.upper()


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
        df = yf.Ticker(y).history(period="3y" if mode == "all" else "5d", interval="1d", auto_adjust=False)
        df = df.dropna(subset=["Close"])
        if df.empty:
            raise Exception("Yahoo nie zwrocilo danych dla symbolu " + y)
        closes = {i.strftime("%Y-%m-%d"): float(c) for i, c in zip(df.index, df["Close"])}
        price = float(df["Close"].iloc[-1])
        p[s] = price
        if mode == "all":
            d = h.setdefault(s, {})
            for date, c in closes.items():
                if date < TODAY or AFTER_CLOSE:
                    d[date] = c
        print("OK   %-14s %10.2f  (%s)  dni=%d ostatni=%s" % (s, price, y, len(closes), max(closes)))
    except Exception as e:
        errs.append(s)
        print("BLAD %-14s (%s) %s" % (s, y, str(e)[:200]))
    time.sleep(1)

if not p:
    sys.exit("Brak notowan - nie zapisuje plikow")
now = NOW.strftime("%Y-%m-%dT%H:%M")
json.dump({"u": now, "p": p}, open("prices.json", "w"))
if mode == "all":
    json.dump({"u": now, "h": h}, open("history.json", "w"), separators=(",", ":"))
print("Zapisano:", len(p), "z", len(items), "symboli; bledy:", errs)
