import json, sys, datetime, urllib.request
out, errs = {}, []
for line in open("tickers.txt", encoding="utf-8"):
    t = line.split("#")[0].strip().lower()
    if not t:
        continue
    try:
        req = urllib.request.Request("https://stooq.pl/q/l/?s=" + t + "&f=sd2t2ohlcv&h&e=csv", headers={"User-Agent": "Mozilla/5.0"})
        row = urllib.request.urlopen(req, timeout=20).read().decode().strip().split("\n")[1].split(",")
        v = float(row[6])
        if v > 0:
            out[t] = v
    except Exception as e:
        errs.append(t + ": " + str(e))
if errs:
    print("Bledy:\n" + "\n".join(errs))
if not out:
    sys.exit("Brak notowan - nie zapisuje pliku")
json.dump({"u": datetime.datetime.utcnow().isoformat(timespec="minutes"), "p": out}, open("prices.json", "w"))
print("OK:", out)
