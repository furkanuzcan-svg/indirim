"""Siteleri tarar, fiyat geçmişini günceller, tablo için deals.json / deals.js yazar.

Çalıştırma (proje kökünden):
    python -m tracker.run            tam tur (tüm sayfalar)
    python -m tracker.run --quick    hızlı tur (her kategorinin 1. sayfası)
    ... --publish                    sonunda deals.json'u GitHub'a gönder (sadece masaüstü)
    python -m tracker.run --publish-only   taramadan sadece gönder (kurulum testi)
Tek sayfa ayrıştırıcı testi:
    python -m tracker.run --test trendyol dosya.html

Makineye özel dosyalar (log, kilit, engel durumu) Drive'a değil
%LOCALAPPDATA%\\indirim klasörüne yazılır.
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import (BLOCK_BACKOFF_MAX_MIN, BLOCK_BACKOFF_MIN, CATEGORIES,
                     HISTORY_DAYS, REQUEST_DELAY, SHOW_SEEN_WITHIN_MIN)
from .match import compare_across_sites
from .sites import PARSERS, Blocked, fetch

ROOT = Path(__file__).resolve().parent.parent
HISTORY_FILE = ROOT / "data" / "history.json"
DEALS_FILE = ROOT / "docs" / "deals.json"
DEALS_JS = ROOT / "docs" / "deals.js"  # index.html'in dosyadan (file://) açılabilmesi için

LOCAL_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "indirim"
LOG_FILE = LOCAL_DIR / "tracker.log"
LOCK_FILE = LOCAL_DIR / "run.lock"
BLOCK_FILE = LOCAL_DIR / "blocked.json"
LOCK_STALE_MIN = 30


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    if sys.stdout:  # pythonw altında stdout yok
        print(line, flush=True)
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    # Log dosyası şişmesin: 2 MB'ı geçince son yarısını tut
    if LOG_FILE.stat().st_size > 2_000_000:
        data = LOG_FILE.read_bytes()[-1_000_000:]
        LOG_FILE.write_bytes(data[data.find(b"\n") + 1:])


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(path)


def acquire_lock():
    """Hızlı ve tam tur aynı anda çalışmasın. Takılı kalmış kilit 30 dk sonra geçersiz."""
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        age_min = (time.time() - LOCK_FILE.stat().st_mtime) / 60
        if age_min > LOCK_STALE_MIN:
            LOCK_FILE.unlink(missing_ok=True)
            return acquire_lock()
        return False


def price_stats(prices, now):
    """Fiyat geçmişi özetleri. `prices` değişim noktalarıdır: [[zaman, fiyat], ...];
    her fiyat bir sonraki değişime kadar geçerlidir.

    tracked_days  ilk görülmeden bu yana gün
    min30/max30   son 30 günde geçerli olmuş en düşük / en yüksek fiyat (şimdiki dahil)
    avg7_prev     şimdiki fiyattan hemen önceki 7 günün zamana göre ağırlıklı ortalaması
                  (en az 6 saatlik önceki veri yoksa None)
    price_since   şimdiki fiyatın başladığı zaman
    """
    pts = [(datetime.fromisoformat(t), p) for t, p in prices]
    start30 = now - timedelta(days=30)
    in30 = [p for i, (t, p) in enumerate(pts) if i + 1 == len(pts) or pts[i + 1][0] > start30]

    cur_start = pts[-1][0]
    win_start = cur_start - timedelta(days=7)
    total = weight = 0.0
    for (t, p), (t_next, _) in zip(pts, pts[1:]):
        w = (min(t_next, cur_start) - max(t, win_start)).total_seconds()
        if w > 0:
            total += p * w
            weight += w
    return {
        "tracked_days": round((now - pts[0][0]).total_seconds() / 86400, 1),
        "min30": min(in30), "max30": max(in30),
        "avg7_prev": round(total / weight, 2) if weight >= 6 * 3600 else None,
        "price_since": prices[-1][0],
    }


def back_off(blocked, key, now):
    """Engelleyen kaynağı atla: ilk engelde BLOCK_BACKOFF_MIN, her tekrarında iki katı."""
    prev = blocked.get(key)
    wait = min(BLOCK_BACKOFF_MAX_MIN, prev["wait"] * 2 if prev else BLOCK_BACKOFF_MIN)
    blocked[key] = {"wait": wait, "until": (now + timedelta(minutes=wait)).isoformat(timespec="minutes")}


def scan_site(site, quick):
    """Bir sitenin sayfalarını sırayla indirir. -> ([(kategori, ürünler)], hatalar, engellendi_mi)"""
    parse = PARSERS[site]
    out, errors = [], []
    for category, pages in CATEGORIES[site]:
        for url in pages[:1] if quick else pages:
            try:
                out.append((category, parse(fetch(url))))
            except Blocked as e:
                errors.append(f"{url}: engellendi ({e})")
                return out, errors, True  # engelleyen siteye istek atmaya devam etme
            except Exception as e:  # ayrıştırıcı hatası diğer sayfaları durdurmasın
                errors.append(f"{url}: {type(e).__name__}: {e}")
            time.sleep(REQUEST_DELAY)
    return out, errors, False


def main(quick):
    now = datetime.now(timezone.utc)
    stamp = now.isoformat(timespec="minutes")
    cutoff = (now - timedelta(days=HISTORY_DAYS)).isoformat(timespec="minutes")
    show_after = (now - timedelta(minutes=SHOW_SEEN_WITHIN_MIN)).isoformat(timespec="minutes")
    history = load_json(HISTORY_FILE, {})
    blocked = load_json(BLOCK_FILE, {})
    status = {}
    log(f"--- {'hızlı' if quick else 'tam'} tur başladı")

    # Siteler aynı anda (her biri kendi iş parçacığında) taranır; site içindeki
    # sayfalar sırayla ve aralarında beklemeyle istenir. Geçmiş sadece ana iş
    # parçacığında güncellenir.
    active = {}
    for site in CATEGORIES:
        b = blocked.get(site)
        if b and b["until"] > stamp:
            status[site] = {"urun": 0, "hatalar": [f"engel nedeniyle {b['until'][11:16]} UTC'ye kadar atlanıyor"]}
            log(f"{site}: atlandı (engel, {b['until'][11:16]} UTC'ye kadar)")
        else:
            active[site] = b
    with ThreadPoolExecutor(max_workers=max(1, len(active))) as pool:
        results = dict(zip(active, pool.map(lambda s: scan_site(s, quick), active)))

    for site, (pages_products, errors, site_blocked) in results.items():
        found = set()  # sayfalarda tekrar eden vitrin ürünleri bir kez sayılsın
        for category, products in pages_products:
            for p in products:
                if not p["price"]:
                    continue
                h = history.setdefault(p["id"], {"prices": []})
                h.update(site=site, category=category, name=p["name"], url=p["url"],
                         old_price=p["old_price"], site_low30=p.get("low30"), last_seen=stamp)
                prices = h["prices"]
                if not prices or prices[-1][1] != p["price"]:
                    prices.append([stamp, p["price"]])
                found.add(p["id"])

        if site_blocked:
            back_off(blocked, site, now)
        else:
            blocked.pop(site, None)
        status[site] = {"urun": len(found), "hatalar": errors}
        log(f"{site}: {len(found)} ürün" + (f", {len(errors)} hata" if errors else ""))
        for e in errors:
            log(f"    {e}")

    # Eski kayıtları temizle
    for pid in list(history):
        h = history[pid]
        h["prices"] = [x for x in h["prices"] if x[0] >= cutoff] or h["prices"][-1:]
        if h["last_seen"] < cutoff:
            del history[pid]

    deals = []
    for pid, h in history.items():
        if h["last_seen"] < show_after:
            continue  # uzun süredir görülmeyen ürün: stokta olmayabilir
        seen = [x[1] for x in h["prices"]]
        deals.append({
            "id": pid, "site": h["site"], "category": h["category"], "name": h["name"],
            "url": h["url"], "price": seen[-1], "old_price": h.get("old_price"),
            "site_low30": h.get("site_low30"),
            "max_seen": max(seen), "min_seen": min(seen),
            "first_seen": h["prices"][0][0], "last_seen": h["last_seen"],
            **price_stats(h["prices"], now),
        })
    # Aynı ürün başka sitede daha ucuz mu? (kendi verimiz, ek istek yok)
    compare_across_sites(deals)

    out ={"updated": stamp, "mode": "hızlı" if quick else "tam", "status": status, "items": deals}
    save_json(HISTORY_FILE, history)
    save_json(DEALS_FILE, out)
    DEALS_JS.write_text("window.DEALS=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";",
                        encoding="utf-8")
    save_json(BLOCK_FILE, blocked)
    log(f"Toplam {len(deals)} ürün yazıldı")


def test(site, html_file):
    html = Path(html_file).read_text(encoding="utf-8", errors="replace")
    items = PARSERS[site](html)
    print(f"{len(items)} ürün")
    for p in items[:8]:
        print(f"  {p['price']!s:>10} | eski={p['old_price']!s:>10} | {p['name'][:60]} | {p['url'][:60]}")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--test":
        test(sys.argv[2], sys.argv[3])
        sys.exit()
    if "--publish-only" in sys.argv:
        from .publish import publish
        publish(DEALS_FILE, LOCAL_DIR, interactive=True)
        log("GitHub'a gönderildi")
        sys.exit()
    if not acquire_lock():
        log("Başka bir tur hâlâ çalışıyor, bu tur atlandı")
        sys.exit()
    try:
        main(quick="--quick" in sys.argv)
        if "--publish" in sys.argv:
            try:
                from .publish import publish
                publish(DEALS_FILE, LOCAL_DIR)
                log("GitHub'a gönderildi")
            except Exception as e:  # internet/GitHub sorunu taramayı bozmasın
                log(f"GitHub'a gönderilemedi: {e}")
    except Exception as e:
        log(f"HATA: {type(e).__name__}: {e}")
        raise
    finally:
        LOCK_FILE.unlink(missing_ok=True)
