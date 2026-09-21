"""Aynı ürünü farklı sitelerde bulma (kendi taradığımız veride, ek istek yok).

Sahte indirim örneği: A sitesi fiyatı şişirip "%33 indirim" gösteriyor ama B
sitesinde ürün zaten o fiyata ya da daha ucuza satılıyor. Bunu yakalamak için
her ürünü diğer sitelerdeki aynı ürünle karşılaştırıyoruz.

İki ilan aynı ürün sayılır:
  1. En az bir ortak model kodu var (en az 7 karakter, en az 2 rakam; işlemci,
     ekran kartı, kapasite gibi ortak kodlar hariç - bkz. NOT_MODEL), ve
  2. teknik özellikleri çelişmiyor: bellek/depolama (8GB-16GB), işlemci
     (13420H-13620H), ekran (55"-65"), kasa (40mm-44mm). Bir tarafta bilgi yoksa
     çelişki sayılmaz.
Örnek yanlış eşleşmeler (2026-09-16 testinde): "ANV15-52" Acer Nitro serisi farklı
işlemci/bellekle; "WATCH8" Galaxy Watch8 Small/Large/Classic.
"""
import re
from collections import defaultdict

# Ürüne özgü olmayan, birçok üründe ortak geçen kodlar: işlemci, ekran kartı, bellek,
# kapasite, güç vb. Bunlarla eşleştirmek aynı işlemcili başka bir laptopu bulur.
NOT_MODEL = re.compile(
    r"^(I[3579]\d{4,5}[A-Z]{0,2}|\d{4,5}[A-Z]{1,3}|RTX(PRO|A)?\d{3,5}(TI|ADA)?|GTX\d{3,4}|RX\d{3,4}[A-Z]*"
    r"|R[3579]\d{4}[A-Z]*|RYZEN\d+|ULTRA\d+|M\d(PRO|MAX)?|(LP)?DDR\d+X?|\d+(GB|TB|MB|HZ|MAH|W|BTU|LT|L|KG|CM|MM|INC)"
    r"|WIFI\d+E?|USB\d*C?|PS\d|PCIE\d*|NVME\d*|A\d{2}(PRO|BIONIC)?|SNAPDRAGON\d*|HELIO[A-Z]?\d+|DIMENSITY\d+"
    # yazılım/standart sürümleri: webOS26, HDR10, Android15, iOS18, Windows11, Bluetooth5
    r"|WEBOS\d+|TIZEN\d*|HDR\d+[A-Z]*|ANDROID\d+|IOS\d+|WINDOWS\d+|WIN\d+|BLUETOOTH\d+|BT\d+|DOLBY\w*"
    # çözünürlük (1920X1080), bellek hızı (LPDDR5-4800 -> LPDDR54800)
    r"|\d{3,4}X\d{3,4}|(LP)?DDR\d+X?\d*"
    # birleşik kapasiteler: 8GB-256GB -> 8GB256GB
    r"|(\d+(GB|TB|MB))+)$"
)


def model_codes(name):
    # "/" ayırıcı sayılır (MediaMarkt: "V3607VH-RP049W/Intel Core"), "-" kodun parçası
    tokens = re.findall(r"[A-Z0-9][A-Z0-9\-]{4,}", name.upper().replace("/TR", " ").replace("İ", "I"))
    codes = set()
    for t in tokens:
        c = t.replace("-", "")
        if len(c) >= 6 and re.search(r"\d", c) and re.search(r"[A-Z]", c) and not NOT_MODEL.match(c):
            codes.add(c)
    return codes


def strong_codes(name):
    # "TAC-12CHSD/XA51I", "TAC-12CHSD(080009)/ZG31I": eğik çizgiden sonraki rakamlı ek modelin
    # parçası (TAC-12CHSD sadece seri). Rakamsız ekler ("/TR", "/Intel") ayrı kelime kalır.
    joined = re.sub(r"([A-Za-z0-9\-]{4,})\s*(?:\(\d+\))?\s*/\s*([A-Za-z]*\d[A-Za-z0-9]*)", r"\1\2", name)
    return {c for c in model_codes(joined) if len(c) >= 7 and len(re.findall(r"\d", c)) >= 2}


def specs(name):
    n = name.upper().replace("İ", "I").replace(",", ".")
    return {
        "cap": frozenset(f"{v}{u}" for v, u in re.findall(r"\b(\d{1,4})\s*(GB|TB)\b", n)),
        "cpu": frozenset(re.sub(r"[\s\-]", "", m) for m in re.findall(
            r"\b(I[3579][\s\-]?\d{4,5}[A-Z]{0,2}|\d{4,5}H[XS]?|ULTRA\s?[579]\s?\d{3}[A-Z]{0,2}|RYZEN\s?[3579]\s?\d{3,4}[A-Z]{0,2}|RTX\s?\d{4}(?:\s?TI)?|M[1-5](?:\s?(?:PRO|MAX))?)\b", n)),
        "inch": frozenset(re.findall(r"\b(\d{2,3})(?:[.]\d)?\s*(?:INÇ|INC|IN\b|\"|''|”)", n)),
        "mm": frozenset(re.findall(r"\b(\d{2})\s*MM\b", n)),
    }


def typical(item):
    """Ürünün olağan fiyatı: geçmişteki ortalama/en yüksek varsa o, yoksa anlık fiyat."""
    return item.get("avg7_prev") or item.get("max30") or item["price"]


def compatible(a, b):
    return all(not (a[k] and b[k] and a[k] != b[k]) for k in a)


def compare_across_sites(items):
    """items: tablo ürünleri (site, name, price, url). Her ürüne, başka sitelerde
    eşleşen en ucuz ilanı `cmp` olarak ekler:
    {site, price (en ucuzu), url, name, n (eşleşen site sayısı),
     max (diğer sitelerdeki en yüksek), avg (diğer sitelerdeki ortalama - fiyat hatası doğrulaması bunu kullanır)}."""
    info = {id(it): (strong_codes(it["name"]), specs(it["name"])) for it in items}
    by_code = defaultdict(list)
    for it in items:
        for c in info[id(it)][0]:
            by_code[c].append(it)
    for it in items:
        codes, sp = info[id(it)]
        best, top, sites = None, 0, set()
        seen, others = set(), []
        for c in codes:
            for other in by_code[c]:
                if other is it or other["site"] == it["site"] or id(other) in seen:
                    continue
                seen.add(id(other))
                if not compatible(sp, info[id(other)][1]):
                    continue
                # Aynı ürün büyük mağazalarda yarı fiyatına pek satılmaz; bu kadar fark
                # büyük ihtimalle yanlış eşleşme (ör. ortak bir teknik kod).
                # Karşılaştırma ANLIK fiyatla değil TİPİK fiyatla yapılır: fiyat hatası olan
                # ürün o an piyasanın çok altındadır, yine de aynı üründür.
                lo, hi = sorted((typical(it), typical(other)))
                if lo < hi * 0.5:
                    continue
                sites.add(other["site"])
                top = max(top, other["price"])
                others.append(other["price"])
                if best is None or other["price"] < best["price"]:
                    best = other
        it["cmp"] = ({"site": best["site"], "price": best["price"], "url": best["url"],
                      "name": best["name"], "n": len(sites), "max": top,
                      "avg": round(sum(others) / len(others), 2)} if best else None)
    return items
