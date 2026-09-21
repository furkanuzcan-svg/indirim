"""Her site için sayfayı indirip ürün listesine çeviren ayrıştırıcılar.

Her ayrıştırıcı şu alanlara sahip sözlükler döndürür:
    id, site, name, url, price, old_price (yoksa None)
    low30 (isteğe bağlı): sitenin kendi bildirdiği son 30 günün en düşük fiyatı
"""
import json
import re
import time

from bs4 import BeautifulSoup
# curl_cffi, Chrome'un TLS parmak izini taklit eder; düz `requests`
# Teknosa tarafından bot olarak tanınıp engelleniyor.
from curl_cffi import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}


class Blocked(Exception):
    """Site isteği engelledi (403/503 veya boş sayfa)."""


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, impersonate="chrome", timeout=30,
                             headers={"Accept-Language": HEADERS["Accept-Language"]})
            if r.status_code == 200 and len(r.text) > 5000:
                return r.text
            last = f"HTTP {r.status_code}, {len(r.text)} bayt"
        except Exception as e:  # curl_cffi bağlantı/zaman aşımı hataları
            last = str(e)
        time.sleep(5 * (i + 1))
    raise Blocked(last)


def tl_to_float(text):
    """'53.900,00 TL' -> 53900.0 ; '14.049' -> 14049.0"""
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return float(text)
    s = re.sub(r"[^\d,\.]", "", str(text))
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _json_str(s):
    """JSON içinden yakalanmış kaçışlı metni çözer."""
    try:
        return json.loads(f'"{s}"')
    except json.JSONDecodeError:
        return s


# ---------------------------------------------------------------- Trendyol
def parse_trendyol(html):
    # Ürün nesnesi: ..."contentId":N,..."name":"...","price":{..."originalPrice":X,..."discountedPrice":Y,...}
    items = []
    seen = set()
    pat = re.compile(
        r'"name":"((?:[^"\\]|\\.){5,400})","price":\{[^}]*?"originalPrice":([\d.]+)[^}]*?"discountedPrice":([\d.]+)'
    )
    for m in pat.finditer(html):
        before = html[max(0, m.start() - 4000):m.start()]
        ids = re.findall(r'"contentId":(\d+)', before)
        if not ids or ids[-1] in seen:
            continue
        pid = ids[-1]
        seen.add(pid)
        after = html[m.end():m.end() + 4000]
        url = None
        for u in re.findall(r'"url":"((?:[^"\\]|\\.)*?)"', before + after):
            u = _json_str(u)
            if f"-p-{pid}" in u:
                url = u
                break
        if not url:
            url = f"/x/x-p-{pid}"
        items.append({
            "id": f"trendyol:{pid}",
            "name": _json_str(m.group(1)),
            "url": url if url.startswith("http") else "https://www.trendyol.com" + url,
            "price": float(m.group(3)),
            "old_price": float(m.group(2)),
        })
    return items


# ---------------------------------------------------------------- n11
def parse_n11(html):
    # Kart: <a class="product-item" href="/urun/...-ID">
    #   div.old-price (üstü çizili), div.price (sepet öncesi), h3.price-currency (son fiyat)
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for card in soup.select("a.product-item[href]"):
        final = card.select_one("h3.price-currency")
        if not final:
            continue
        price = tl_to_float(final.get_text())
        olds = [tl_to_float(el.get_text()) for el in card.select("div.old-price, div.price")]
        olds = [o for o in olds if o and price and o > price]
        titled = card.find(attrs={"title": True})
        img = card.find("img", alt=True)
        name = (titled and titled["title"]) or (img and img["alt"]) or card["href"].rsplit("/", 1)[-1]
        href = card["href"]
        pid = re.search(r"-(\d+)(?:\?|$)", href)
        items.append({
            "id": f"n11:{pid.group(1) if pid else href}",
            "name": name,
            "url": "https://www.n11.com" + href if href.startswith("/") else href,
            "price": price,
            "old_price": max(olds) if olds else None,
        })
    return items


# ---------------------------------------------------------------- Teknosa
def parse_teknosa(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for box in soup.select("div[data-product-id]"):
        last = box.select_one("span.prc-last")
        link = box.find("a", href=True)
        if not last or not link:
            continue
        first = box.select_one("span.prc-first")
        name = box.get("data-product-name") or link.get("title") or link.get_text(" ", strip=True)
        href = link["href"]
        items.append({
            "id": "teknosa:" + box["data-product-id"],
            "name": name,
            "url": href if href.startswith("http") else "https://www.teknosa.com" + href,
            "price": tl_to_float(last.get_text()),
            "old_price": tl_to_float(first.get_text()) if first else None,
        })
    return items


# ---------------------------------------------------------------- Hepsiburada
def _cls_prefix(prefix):
    # CSS modül sınıflarının sonu derlemeye göre değişir (price-module_finalPrice__oALDy)
    return lambda c: bool(c) and c.startswith(prefix)


def parse_hepsiburada(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for card in soup.select('li[class^="productListContent-"]'):
        link = card.find("a", href=re.compile(r"-pm?-HB\w+"))
        final = card.find(class_=_cls_prefix("price-module_finalPrice__"))
        if not link or not final:
            continue
        code = re.search(r"-pm?-(HB\w+)", link["href"]).group(1)
        price = tl_to_float(final.get_text("", strip=True))
        orig = card.find(class_=_cls_prefix("price-module_originalPrice__"))
        old = tl_to_float(orig.get_text("", strip=True)) if orig else None
        # "Premium ile" indirimi sadece Premium üyelere: gerçek fiyat üstü çizili olandır
        if card.find(class_=_cls_prefix("price-module_isPremiumCampaign__")) and old:
            price, old = old, None
        img = card.find("img", alt=True)
        href = link["href"]
        items.append({
            "id": f"hepsiburada:{code}",
            "name": link.get("title") or (img and img["alt"]) or href.rsplit("/", 1)[-1],
            "url": href if href.startswith("http") else "https://www.hepsiburada.com" + href,
            "price": price,
            "old_price": old if old and price and old > price else None,
        })
    return items


# ---------------------------------------------------------------- MediaMarkt
def parse_mediamarkt(html):
    # window.__PRELOADED_STATE__ = {..apolloState..}; içinde JS'e özgü `undefined` değerleri var
    m = re.search(r"window\.__PRELOADED_STATE__\s*=\s*", html)
    if not m:
        return []
    text = re.sub(r":undefined([,}\]])", r":null\1", html[m.end():])
    state, _ = json.JSONDecoder().raw_decode(text)
    apollo = state.get("apolloState") or {}
    items = []
    for key, feat in apollo.items():
        if not key.startswith("CofrPriceFeature:") or not isinstance(feat, dict):
            continue
        pid = str(feat.get("id", "")).rsplit(":", 1)[-1]
        prod = apollo.get(f"GraphqlProduct:Media:tr-TR:{pid}")
        base = (feat.get("price") or {}).get("amount")
        if not prod or not base:
            continue
        promo = (feat.get("promoPrice") or {}).get("amount")
        strike = feat.get("strikePrice") or {}
        price = promo if promo and promo < base else base
        # strikePrice (type LOP) sitenin yasal "önceki en düşük fiyat"ı; yoksa kampanya öncesi fiyat
        old = strike.get("amount") if strike.get("shouldBeStruck") else (base if price < base else None)
        items.append({
            "id": f"mediamarkt:{pid}",
            "name": prod.get("title") or pid,
            "url": "https://www.mediamarkt.com.tr" + (prod.get("url") or ""),
            "price": float(price),
            "old_price": float(old) if old and old > price else None,
        })
    return items


# ---------------------------------------------------------------- İdefix
def parse_idefix(html):
    # __NEXT_DATA__ props.pageProps.categoryData.items[].variants[]: her varyant (renk) ayrı ürün.
    # price = liste fiyatı, discountedSalesPrice = sepette fiyat,
    # thirtyDaysLowPrice = sitenin bildirdiği son 30 günün en düşüğü.
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return []
    data = json.loads(m.group(1))
    groups = (((data.get("props") or {}).get("pageProps") or {}).get("categoryData") or {}).get("items") or []
    items = []
    for g in groups:
        for v in g.get("variants") or []:
            if not v.get("isSalable", True) or not v.get("price") or not v.get("handleUrl"):
                continue
            # İdefix, geçici olarak satılamayan ürünlere 99.000 TL yer tutucusu koyuyor
            if float(v["price"]) == 99000:
                continue
            list_price = float(v["price"])
            sale = float(v.get("discountedSalesPrice") or list_price)
            price = min(sale, list_price)
            items.append({
                "id": f"idefix:{v['id']}",
                "name": v.get("name") or v["handleUrl"],
                "url": "https://www.idefix.com" + v["handleUrl"],
                "price": price,
                "old_price": list_price if list_price > price else None,
                "low30": float(v["thirtyDaysLowPrice"]) if v.get("thirtyDaysLowPrice") else None,
            })
    return items


# ---------------------------------------------------------------- Vatan
def parse_vatan(html):
    # Kart: div.product-list.product-list--list-page; model kodu kartta yazıyor.
    # Liste fiyatı .product-list__price; "Sepette X TL" kampanyası varsa gerçek fiyat odur.
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for card in soup.select("div.product-list.product-list--list-page"):
        link = card.find("a", href=True)
        name_el = card.select_one(".product-list__product-name")
        price_el = card.select_one(".product-list__price")
        if not link or not name_el or not price_el:
            continue
        list_price = tl_to_float(price_el.get_text())
        basket = card.select_one(".price-basket-camp__sepet")
        struck = card.select_one(".product-list__current-price")
        price, old = list_price, None
        if basket and tl_to_float(basket.get_text()):
            price, old = tl_to_float(basket.get_text()), list_price
        elif struck and tl_to_float(struck.get_text()):
            old = tl_to_float(struck.get_text())
        code_el = card.select_one(".product-list__product-code")
        code = code_el.get_text(strip=True) if code_el else ""
        href = link["href"]
        name = name_el.get_text(" ", strip=True)
        items.append({
            "id": "vatan:" + (code or href.rstrip("/").rsplit("/", 1)[-1]),
            # Model kodunu ada ekle: siteler arası eşleştirme (match.py) koda bakıyor
            "name": f"{name} {code}" if code and code not in name else name,
            "url": href if href.startswith("http") else "https://www.vatanbilgisayar.com" + href,
            "price": price,
            "old_price": old if old and price and old > price else None,
        })
    return items


PARSERS = {
    "trendyol": parse_trendyol,
    "n11": parse_n11,
    "teknosa": parse_teknosa,
    "hepsiburada": parse_hepsiburada,
    "mediamarkt": parse_mediamarkt,
    "vatan": parse_vatan,
    "idefix": parse_idefix,
}
