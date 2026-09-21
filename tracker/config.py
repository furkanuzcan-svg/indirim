"""Hangi sayfaların takip edileceği. Yeni kategori eklemek için listeye ekle.

OnuAl gibi: en uç pahalı ürünler yerine insanların gerçekten aldığı fiyat
aralığındaki popüler ürünler. Her kategoride sitenin kendi fiyat filtresiyle
PRICE_MIN-PRICE_MAX aralığı, içinde "çok satanlar" (yoksa sitenin varsayılan)
sıralaması; ilk birkaç sayfa taranır. Fiyat filtreleri 2026-09-16'da her sitede
en düşük/en yüksek fiyat kontrol edilerek doğrulandı.
"""

# Taranan fiyat aralığı (TL). Sitenin kendi fiyat filtresi ancak robots.txt izin veriyorsa
# adreste kullanılır (Trendyol, n11, Vatan); diğerlerinde filtresiz sayfa taranıp aralık
# kendi tarafımızda uygulanır (bkz. run.py). Aralık dışı ürünler kaydedilmez.
PRICE_MIN = 5000
PRICE_MAX = 150000

PAGES_PER_CATEGORY = 3
# Hızlı tur (5 dk) kategori başına kaç sayfa tarasın (tam tur hepsini tarar).
# 2 sayfa ~3 dk sürüyor; 5 dakikalık aralığa sığmalı.
QUICK_PAGES = 2


def _pages(url_fmt, first_page):
    return [url_fmt.format(p=first_page + i, lo=PRICE_MIN, hi=PRICE_MAX) for i in range(PAGES_PER_CATEGORY)]


def _site(url_fmt, first_page, categories):
    # Her kategori: (etiket, [sayfa1, sayfa2, ...]); hızlı tur sadece ilk sayfayı tarar.
    return [(label, _pages(url_fmt.replace("{path}", path), first_page))
            for label, path in categories]


CATEGORIES = {
    # sst=BEST_SELLER, prc=min-max, sayfa pi=1'den
    "trendyol": _site("https://www.trendyol.com/{path}?sst=BEST_SELLER&prc={lo}-{hi}&pi={p}", 1, [
        ("Elektronik", "laptop-x-c103108"),
        ("Elektronik", "oyuncu-dizustu-bilgisayari-x-c106084"),
        ("Elektronik", "cep-telefonu-x-c103498"),
        ("Elektronik", "televizyon-x-c104024"),
        ("Elektronik", "akilli-saat-x-c1240"),
        ("Elektronik", "bluetooth-kulaklik-x-c108626"),
        ("Oyun", "playstation-5-x-c144046"),
        ("Beyaz Eşya", "buzdolabi-x-c103623"),
        ("Beyaz Eşya", "camasir-makinesi-x-c103625"),
    ]),
    # varsayılan sıralama, minp/maxp, sayfa pg=1'den
    "n11": _site("https://www.n11.com/{path}?minp={lo}&maxp={hi}&pg={p}", 1, [
        ("Elektronik", "bilgisayar/dizustu-bilgisayar"),
        ("Elektronik", "telefon-ve-aksesuarlari/cep-telefonu"),
        ("Elektronik", "televizyon-ve-ses-sistemleri"),
        ("Elektronik", "fotograf-ve-kamera"),
        ("Oyun", "video-oyun-konsol/playstation-5"),
        ("Beyaz Eşya", "beyaz-esya"),
    ]),
    # Not: Teknosa robots.txt "*s=*" adreslerini botlara kapatmış -> filtresiz sayfa kullanılıyor
    "teknosa": _site("https://www.teknosa.com/{path}?page={p}", 0, [
        ("Elektronik", "laptop-notebook-c-116004"),
        ("Elektronik", "televizyonlar-c-101001"),
        ("Elektronik", "tablet-c-116012"),
        ("Elektronik", "akilli-saat-c-100004001"),
        ("Ev Aletleri", "dikey-supurge-c-117005001"),
        ("Ev Aletleri", "klima-c-117007002"),
    ]),
    # Not: Hepsiburada robots.txt "?filtreler=..." adreslerini kapatmış -> filtresiz sayfa
    "hepsiburada": _site("https://www.hepsiburada.com/{path}?sayfa={p}", 1, [
        ("Elektronik", "laptop-notebook-dizustu-bilgisayarlar-c-98"),
        ("Elektronik", "oyuncu-laptoplari-c-95583"),
        ("Elektronik", "cep-telefonlari-c-371965"),
        ("Elektronik", "led-tv-televizyonlar-c-163192"),
        ("Elektronik", "tablet-c-3008012"),
        ("Elektronik", "monitorler-c-57"),
        ("Elektronik", "akilli-saatler-c-60003676"),
        ("Elektronik", "bluetooth-kulakliklar-c-16218"),
        ("Oyun", "playstation-5-konsol-c-80757006"),
        ("Beyaz Eşya", "camasir-makineleri-c-155121"),
        ("Beyaz Eşya", "bulasik-makineleri-c-22156"),
        ("Ev Aletleri", "supurgeler-c-155123"),
        ("Ev Aletleri", "klimalar-c-17453"),
    ]),
    # Not: MediaMarkt robots.txt "?filter=" ve "*sort=" adreslerini kapatmış -> filtresiz sayfa
    "mediamarkt": _site("https://www.mediamarkt.com.tr/tr/category/{path}.html?page={p}", 1, [
        ("Elektronik", "laptop-504926"),
        ("Elektronik", "cep-telefonlari-504171"),
        ("Elektronik", "akilli-saatler-862018"),
        ("Elektronik", "bluetooth-kulakliklar-795539"),
        ("Elektronik", "fotograf-makineleri-811020"),
        ("Beyaz Eşya", "buzdolabi-465709"),
        ("Beyaz Eşya", "camasir-makineleri-809009"),
        ("Beyaz Eşya", "bulasik-makineleri-712509"),
        ("Ev Aletleri", "dikey-supurge-465743"),
        ("Ev Aletleri", "kahve-makinesi-806537"),
    ]),
    # varsayılan sıralama = çok satanlar, min/max, page=N (1'den); 24 ürün/sayfa
    "vatan": _site("https://www.vatanbilgisayar.com/{path}/?min={lo}&max={hi}&page={p}", 1, [
        ("Elektronik", "notebook"),
        ("Elektronik", "cep-telefonu-modelleri"),
        ("Elektronik", "televizyon"),
        ("Elektronik", "tabletler"),
        ("Elektronik", "bilgisayar-monitorleri"),
        ("Elektronik", "akilli-saatler"),
        ("Oyun", "playstation"),
        ("Ev Aletleri", "elektrikli-supurgeler"),
        ("Ev Aletleri", "robot-supurgeler"),
        ("Ev Aletleri", "kahve-makinesi"),
        ("Ev Aletleri", "klima"),
    ]),
    # Not: İdefix robots.txt "*?siralama" adreslerini kapatmış -> filtresiz sayfa (varyantlar ayrı ürün)
    "idefix": _site("https://www.idefix.com/{path}?sayfa={p}", 1, [
        ("Elektronik", "cep-telefonu-c-2313571270"),
        ("Elektronik", "bilgisayar-ve-tablet-c-2302"),
        ("Elektronik", "televizyon-c-2314109670"),
        ("Elektronik", "akilli-saatler-smartwatch-c-230993929"),
        ("Elektronik", "kulakici-bluetooth-kulakliklar-c-231466333"),
        ("Oyun", "playstation-5-konsollari-c-230874691"),
        ("Beyaz Eşya", "camasir-makineleri-c-230156015"),
        ("Beyaz Eşya", "bulasik-makineleri-c-230123063"),
        ("Ev Aletleri", "supurgeler-c-2311351740"),
        ("Ev Aletleri", "kahve-makineleri-c-2311628240"),
    ]),
    # Kural: sadece otomatik okumayı engellemeyen siteler. Bir site sürekli engellerse
    # atlatmaya çalışılmaz, listeden çıkarılır (Amazon 2026-09-16'da bu yüzden çıkarıldı).
}

# Masaüstündeki zamanlama: hızlı tur 5 dk'da bir (her kategorinin 1. sayfası),
# tam tur saatte bir (tüm sayfalar). Tabloda son bu kadar dakikada görülen ürünler kalır;
# tam tur aralığından uzun olmalı ki sadece 2-3. sayfadaki ürünler kaybolmasın.
SHOW_SEEN_WITHIN_MIN = 150

# Online tablo: masaüstü (--publish ile) deals.json'u bu deponun bu dalına gönderir.
PUBLISH_REPO = "https://github.com/furkanuzcan-svg/indirim.git"
PUBLISH_BRANCH = "data"

# Fiyat hatası avı: normal fiyatı ERROR_MIN_NORMAL_PRICE altında olmayan bir ürünün fiyatı
# ERROR_DROP_PCT kadar düşerse "düşüş" kaydı açılır (data/dips.json). Gerçek fiyat hatası
# kısa sürer: fiyat ERROR_MAX_MIN içinde eski seviyesinin ERROR_RECOVER_PCT'ine dönerse
# "doğrulanmış fiyat hatası" sayılır. Kalıcı düşüşler normal indirimdir, hata sayılmaz.
ERROR_MIN_NORMAL_PRICE = 10000
ERROR_DROP_PCT = 60
ERROR_RECOVER_PCT = 85
ERROR_MAX_MIN = 20
DIP_KEEP_HOURS = 48

# Sürekli döngü (`--loop`): tur biter bitmez yenisi başlar. Fiyat hataları dakikalar içinde
# düzeltildiği için kontrol aralığı ne kadar kısaysa yakalama şansı o kadar yüksek.
LOOP_PAUSE_SEC = 10        # turlar arası nefes payı
LOOP_FULL_MIN = 60         # bu kadar dakikada bir tam tur (tüm sayfalar)
LOOP_PUBLISH_MIN = 5       # GitHub'a en fazla bu sıklıkta gönder

# Geçici engelde (tek seferlik 403/503) siteyi atla: ilk engelde 30 dk, her tekrarında
# iki katı, en fazla 6 saat. Engel kalıcılaşırsa site CATEGORIES'ten çıkarılmalı.
BLOCK_BACKOFF_MIN = 30
BLOCK_BACKOFF_MAX_MIN = 360

# Sitelerin gösterdiği eski fiyat bazen şişirilmiştir. Kendi geçmişimizdeki
# en yüksek fiyatı da kaydediyoruz; tablo ikisini de gösterir.
HISTORY_DAYS = 180

# Her site isteği arasında bekleme (saniye) - siteleri yormamak için.
REQUEST_DELAY = 3
