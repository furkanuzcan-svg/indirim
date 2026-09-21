# İndirim projesi

## Çalışma ortamı: iki laptop, Google Drive senkronu
Bu klasör Google Drive ile senkronlanıyor ve iki farklı laptopta (ev + okul) kullanılıyor.
Kurallar:

- **Mutlak yol yok.** Kodda `G:\Drive'ım\...` gibi yollar kullanma; okuldaki laptopta Drive
  harfi/yolu farklı olabilir. Her zaman proje köküne göre göreli yol kullan.
- **Bağımlılıklar Drive'a girmesin.** `node_modules/`, `.venv/`, `__pycache__/`, build/dist
  çıktıları binlerce küçük dosyadır; Drive senkronunu kilitler ve makineye özeldir.
  Sanal ortamı/bağımlılıkları her makinede ayrı kur (`npm install` / `pip install -r requirements.txt`).
  Python venv gerekiyorsa Drive dışında oluştur (örn. `%USERPROFILE%\.venvs\indirim`).
- **Bağımlılık listesi dosyada tutulsun** (`package.json` / `requirements.txt`), böylece
  diğer makinede tek komutla kurulabilir.
- **Gizli bilgiler** `.env` dosyasında; `.env.example` ile hangi değişkenlerin gerektiği belgelenir.
- **Aynı anda iki makinede düzenleme yapma.** Birinde kapatmadan önce Drive senkronunun
  bitmesini bekle, yoksa "(1)" kopyası çakışma dosyaları oluşur.
- Proje notları ve kararlar bu dosyaya yazılır (Claude'un yerel hafızası diğer laptopa taşınmaz).

## Kurulum (her makinede bir kez)
- **Evdeki masaüstü (tarayıcıyı sürekli çalıştıran tek makine):**
  `powershell -ExecutionPolicy Bypass -File kurulum_masaustu.ps1`
  Python 3.12 + venv (`%USERPROFILE%\.venvs\indirim`) kurar, bir hızlı tur dener, iki zamanlanmış görev kaydeder:
  "Indirim Hizli Tur" (5 dk, `--quick`) ve "Indirim Tam Tur" (60 dk). Kaldırmak: aynı komut + `-Kaldir`.
  Log/kilit/engel durumu: `%LOCALAPPDATA%\indirim\` (Drive'a girmez). Uyku modu kapalı olmalı.
- **Laptoplar (sadece geliştirme):** Python 3.12 (`winget install --id Python.Python.3.12 -e --scope user`),
  `py -3.12 -m venv %USERPROFILE%\.venvs\indirim`, `pip install -r requirements.txt`.
  **Laptoplara zamanlanmış görev kurma** ve elle tarama çalıştırıyorsan masaüstündeki görevle çakışabileceğini unutma
  (ikisi aynı `data/history.json`'a yazar; Drive "(1)" kopyası oluşturabilir).
- Tablo: `docs/index.html` dosyasına çift tıkla (veri `docs/deals.js`'ten okunur, sunucu gerekmez).

## Kaldığımız yer
Claude: her anlamlı iş adımından sonra bu bölümü güncelle (ne yapıldı, sırada ne var,
açık sorular). Diğer laptopta yeni oturum açıldığında devam noktası burasıdır.

- **Proje:** OnuAl benzeri kişisel indirim takipçisi (sadece kullanıcı için, WhatsApp/Telegram yok).
  Amazon, MediaMarkt, Hepsiburada, Trendyol, n11, Teknosa vb. sitelerde yüksek fiyatlı
  ürünlerin yüksek yüzdeli indirimlerini takip eder. OnuAl'ın logosu/markası kopyalanmaz.
- **Kararlar (2026-09-12):**
  - Tarayıcı bulutta çalışır: GitHub Actions (ücretsiz, zamanlanmış). Laptoplar kapalıyken de takip sürer.
  - Arayüz: basit liste/tablo (statik HTML, GitHub Pages).
  - Fiyat ve indirim eşikleri arayüzde ayarlanabilir.
  - İndirim yüzdesi mümkünse kendi fiyat geçmişimizle doğrulanır (sitelerin üstü çizili fiyatları şişirilmiş olabilir).
  - Dil: Python.
- **Site erişim testleri (2026-09-12):**
  - Sunucu/bulut IP'sinden (WebFetch): Hepsiburada, Trendyol, n11, Teknosa 403; Amazon 503; sadece MediaMarkt açıldı.
    => GitHub Actions (bulut IP) büyük ihtimalle çoğu sitede engellenir; henüz doğrudan test edilmedi.
  - Ev internetinden (curl / Invoke-WebRequest):
    - Trendyol: kategori sayfası HTML'inde gömülü JSON, `"price":{"originalPrice":..,"discountedPrice":..}`.
    - n11: gömülü JSON, `"priceInfo":{"oldPrice":..,"finalPrice":..}` (+ `discountRate`).
    - Teknosa: HTML, `span.prc-first` (eski) / `span.prc-last` (yeni), `div.prd-discount` (%).
    - Amazon: arama sonucu HTML, `data-component-type="s-search-result"`, `a-price-whole` (yeni),
      `a-text-price > a-offscreen` (eski). Curl bazen 503 aldı, Invoke-WebRequest çalıştı; yeniden deneme gerekli.
    - MediaMarkt: `__PRELOADED_STATE__` / Apollo JSON, `strikePrice` alanları var; ayrıştırma henüz yapılmadı.
    - Hepsiburada: düz istekte 403 veya boş sayfa; gerçek tarayıcıda (Chromium) açılıyor => Playwright gerekli.
- **Karar (test sonrası):** Kullanıcı engelleme riskine rağmen önce bulutu (GitHub Actions) denemek istedi.
  Bulutta çoğu site engellenirse "açık laptopta + Drive" ya da karma modele geçilecek.
- **Kod yapısı:** `tracker/` (site ayrıştırıcıları + fiyat geçmişi), `docs/` (tablo sayfası, GitHub Pages),
  `data/` (fiyat geçmişi JSON), `.github/workflows/scrape.yml` (zamanlanmış çalışma).
- **Durum:** Python 3.12 ve Git kuruldu (ev laptopu). Sanal ortam: `%USERPROFILE%\.venvs\indirim` (Drive dışında).
  Ayrıştırıcılar kayıtlı sayfalarla test edildi: Amazon 58, Trendyol 36, n11 20, Teknosa 19 ürün.
  - n11 listesi HTML'de: `a.product-item`, `h3.price-currency` (son), `div.price` / `div.old-price` (eski).
  - Teknosa: `div[data-product-id]` kutusu, `data-product-name`.
  - Trendyol: `"name":"..","price":{..originalPrice..discountedPrice}`, id = önceki `contentId`.
  - Henüz yok: Hepsiburada (Playwright gerekli), MediaMarkt (strikePrice JSON ayrıştırılmadı).
  - PowerShell 5.1 native komutlara verilen tırnakları siler: Python kodu `@'..'@ | python -` ile ver.
- **İlk canlı tarama (2026-09-12):** Trendyol 107, n11 40, Teknosa 19 ürün (curl_cffi ile).
  Düz `requests` Teknosa/Amazon'da TLS parmak izi yüzünden engelleniyordu -> `curl_cffi` (impersonate="chrome").
  - Amazon: bir günde çok test isteğinden sonra 503 / 202 (JS doğrulama) vermeye başladı. Geçici kısıtlama gibi, tekrar denenmeli.
  - Sonuç: normal kategori sayfalarında büyük indirim neredeyse yok (165 üründen 6'sı %10+, hiçbiri %30+).
    OnuAl tarzı fırsatlar için indirime göre sıralı listeler / fırsat sayfaları kaynak olarak eklenmeli.
  - Tablo: "şüpheli" etiketi ancak 7+ günlük fiyat geçmişi olunca gösterilir.
  - Yerel önizleme: `python -m http.server 8765 --directory docs` -> http://localhost:8765
  - `data/` ve `docs/deals.json` yerelde commit'lenmez (bulutta bot commit'leyecek, çakışma olmasın).
- **Sıralama / sayfalama (2026-09-13):** Hiçbir sitede "indirime göre sırala" yok. Fiyata göre azalan + çok sayfa:
  - Trendyol `?sst=PRICE_BY_DESC&pi=N` (1'den). Her sayfada aynı 20 ürünlük vitrin bloğu tekrar eder, id ile ayıklanır.
  - n11 `?srt=PRICE_HIGH&pg=N` (1'den). Teknosa `?sort=price-desc&page=N` (0'dan).
  - Amazon 13 Eylül'de de 503 verdi (`pct-off` filtreli arama dahil).
- **GitHub:** kullanıcı `furkanuzcan-svg` (Google ile giriş). Depo: `furkanuzcan-svg/indirim`, **herkese açık**
  (ücretsiz hesapta GitHub Pages sadece açık depoda). Remote eklendi; depoyu kullanıcı GitHub'da oluşturacak.
  Pages kaynağı: `main` dalı, `/docs` klasörü.
- **Fiyata göre azalan çok sayfalı tarama (2026-09-13):** Trendyol 3 kategori x 3 sayfa, n11 2x3, Teknosa 1x3.
  448 tekil ürün, 192'si indirimli ama en yüksek indirim %10 (hiçbiri %10'u geçmiyor).
  => Site listelerindeki "eski fiyat" farkları küçük. Büyük fırsatlar için:
     (a) kendi fiyat geçmişimizde ani düşüşleri yakala (OnuAl'ın "son 6 ayın en düşük fiyatı" mantığı),
     (b) kategori sayısını artır (beyaz eşya, küçük ev aletleri, oyun konsolu, kulaklık vb.),
     (c) taramayı sık yap ki geçmiş birikip düşüşler görünsün (bulut zamanlaması bu yüzden önemli).
- **Çalışma yeri kararı (2026-09-13):** Önce bulut (GitHub Actions) denenecek. Bulutta siteler engellenirse
  tarama **evdeki masaüstü PC'de** sürekli açık kalarak çalışacak. Ev laptopu (bu proje burada başladı) ve
  okul laptopu sadece geliştirme için; onlarda sürekli tarama çalıştırılmayacak.
  Masaüstü seçilirse: Python + venv kurulumu, Windows Görev Zamanlayıcı ile 2 saatte bir `python -m tracker.run`,
  sonuçlar Drive'daki `docs/deals.json`'a yazılır (ya da GitHub'a push edilir).
- **Kategoriler genişletildi (2026-09-13):** Trendyol 9, n11 6, Teknosa 6 kategori (beyaz eşya, konsol, kulaklık,
  akıllı saat, klima, süpürge vb.), her biri 3 sayfa. Teknosa'daki yeni kategorilerde en iyi indirim %2-7 idi.
  Genişletilmiş tarama: 1546 ürün (Trendyol 910, n11 360, Teknosa 276), 482 indirimli; %10+ 30, %20+ 13, %30+ 5.
  %30 üstü 5 ürünün hepsi n11'de PS5 paketleri (%34-51). Satıcıların eski fiyatı şişirilmiş olabilir,
  7 günlük geçmiş birikince "şüpheli" kontrolü doğrulayacak.
- **Kontrol aralığı (2026-09-13, kullanıcı isteği):** 2 saat çok uzun, hedef **~5 dakika**.
  Dikkat edilecekler:
  - Tam tarama (~63 sayfa, 3 sn bekleme) şu an ~5 dk sürüyor; aralık tarama süresinden kısa olamaz.
    Öneri: 5 dk'da bir hızlı tur (her kategorinin sadece 1. sayfası + fiyatı düşen ürünler), saatte bir tam tur.
  - Sık istek = engellenme riski artar (Amazon bir günlük testte 503'e düştü). Siteler arasında paralel,
    site içinde sıralı istek; engellenen siteyi bir süre atla (geri çekilme).
  - GitHub Actions cron en az 5 dk ve sık sık 10-20+ dk gecikir; 5 dk'lık düzen için evdeki masaüstü
    (Görev Zamanlayıcı / sürekli çalışan döngü) daha güvenilir. `.github/workflows/scrape.yml` hâlâ 2 saat.
- **Masaüstüne geçiş (2026-09-16):** Kullanıcı buluttan önce evdeki masaüstüne geçmeye karar verdi.
  - `run.py`: `--quick` (her kategorinin 1. sayfası) / tam tur; kilit dosyası (turlar çakışmaz);
    engelleyen site 30 dk atlanır, tekrarında 2 katı (en fazla 6 saat); log `%LOCALAPPDATA%\indirim\tracker.log`.
  - Tablo son 150 dk'da görülen ürünleri gösterir; `deals.js` ile file:// açılır, 5 dk'da bir kendini yeniler.
  - `data/`, `docs/deals.json`, `docs/deals.js` artık .gitignore'da (GitHub Pages'e geçilirse yeniden düşünülmeli).
  - Ev laptopunda test: hızlı tur ~1,5 dk, 691 ürün (Trendyol 424, n11 120, Teknosa 91, **Amazon 56 - yeniden açıldı**).
    Engel mantığı sahte fetch ile test edildi. `kurulum_masaustu.ps1` sadece sözdizimi kontrol edildi, çalıştırılmadı.
  - Masaüstü kuruldu ve çalışıyor (16 Eylül 22:11'de ilk hızlı tur Drive'a geldi).
    Oturum listesi her makinede ayrı; masaüstünde bu sohbet görünmez (normal).
- **Online tablo / GitHub (2026-09-16):**
  - Depo `furkanuzcan-svg/indirim` oluşturuldu (public), `main` push edildi. Commit e-postaları
    `furkanuzcan-svg@users.noreply.github.com` ile değiştirildi (filter-branch; gmail hiçbir yerde yok).
  - `tracker/publish.py`: `--publish` ile her turdan sonra deals.json `data` dalına ebeveynsiz tek commit
    olarak force-push (Pages yeniden yayınlanmaz, saatlik yayın sınırına takılmaz). Yerel kopya `%LOCALAPPDATA%\indirim\yayin`.
    Zamanlanmış görevde `GCM_INTERACTIVE=never`; ilk giriş `--publish-only` ile (kurulum betiği) etkileşimli.
  - `index.html` github.io'da veriyi `api.github.com/.../contents/deals.json?ref=data` (Accept: raw) ile okur,
    başarısızsa raw.githubusercontent.com'a düşer. API CORS `*`, doğrulandı.
  - `.github/workflows/scrape.yml` kaldırıldı (bulutta tarama yok).
  - Ev laptopundan bir kez `--publish-only` ile `data` dalı oluşturuldu ve API'den okundu.
  - **Çalışıyor (16 Eylül 22:40):** Pages açık, masaüstü `data` dalına gönderiyor (fiyat-botu, 19:39 UTC),
    https://furkanuzcan-svg.github.io/indirim/ 748 ürünü gösteriyor. O turda Amazon masaüstünde 0 (engel/geri çekilme).
- **Yeni kaynaklar + doğrulama (2026-09-16 gece):** Kullanıcı sırayla istedi: (1) Hepsiburada+MediaMarkt,
  (2) geçmiş rozetleri, (3) fiyat karşılaştırma sitesi denemesi (sonra kaldırıldı), (4) diğer siteler.
  - Aday site yoklaması (ev IP, curl_cffi): Hepsiburada, MediaMarkt, Pazarama, Vatan, Boyner, İdefix, Koçtaş,
    Çiçeksepeti hepsi 200. İdefix/Koçtaş sayfasında captcha izi.
  - **Hepsiburada artık curl_cffi ile açılıyor (Playwright gerekmez).** Kart `li[class^=productListContent-]`,
    fiyat `price-module_finalPrice__*`, eski `price-module_originalPrice__*`; "Premium ile" indirim sayılmaz.
    `?siralama=azalanfiyat&sayfa=N`, 36 ürün/sayfa.
  - **MediaMarkt:** `window.__PRELOADED_STATE__` (JS `undefined` -> null), apolloState `GraphqlProduct:Media:tr-TR:ID`
    + `CofrPriceFeature` (price/promoPrice/strikePrice type LOP). `?sort=currentprice+desc&page=N`, 12 ürün/sayfa.
  - Siteler paralel (ThreadPoolExecutor): 6 siteli hızlı tur 61 sn, ~1300 ürün.
  - `price_stats`: tracked_days, min30/max30, avg7_prev (zaman ağırlıklı), price_since. Tablo rozetleri:
    ani düşüş (son 2 günde, 7g ort. %10+ altı), 30 günün en düşüğü, sahte indirim (7+ gün geçmiş şartı).
  - Masaüstü yeni kodu Drive'dan aldı (22:57 turunda hepsiburada 467, mediamarkt 120). Amazon masaüstünde
    captcha (HTTP 200, 2 KB) -> geri çekilmede.
- **Diğer siteler (2026-09-16 gece):**
  - **Vatan eklendi:** `div.product-list--list-page`, model kodu `.product-list__product-code` (ada eklenir,
    siteler arası eşleştirme için), "Sepette X TL" = fiyat / liste fiyatı = eski. `?srt=PU&page=N`, 24/sayfa, 11 kategori.
  - **İdefix eklendi:** `__NEXT_DATA__` props.pageProps.categoryData.items[].variants[] (her varyant ayrı ürün):
    price (liste), discountedSalesPrice (sepette), thirtyDaysLowPrice (liste fiyatı üzerinden!).
    `?siralama=desc_price&sayfa=N`, 10 kategori. `low30` -> history `site_low30`; rozet sadece liste fiyatı
    bunun %1 altına inerse (sepette fiyat hep altında olduğundan onunla karşılaştırma anlamsız).
  - İdefix/Koçtaş "captcha" izleri zararsız (gizli recaptcha rozeti / `googleRecaptchaActive = "false"`).
  - **Atlananlar:** Pazarama (fiyatlar `__NUXT__` IIFE değişkenlerinde, fiyat sıralaması yok), Boyner (elektronik
    ucuz aksesuar, indirim bilgisi yok), Koçtaş (yapı market), Karaca (kartlar JS ile çiziliyor, ld+json'da
    sadece fiyat). Gerekirse API'leri araştırılabilir.
  - 8 siteli hızlı tur 67 sn, ~1770 ürün (Amazon hariç; o an 503).
- **OnuAl gibi fiyat aralığı (2026-09-16 gece):** Fiyata göre azalan sıralama en uç pahalı ürünleri (500k+ laptop,
  1M TV) getiriyordu; kapsama ~%1-2 ve yanlış aralık. Artık her kategoride sitenin fiyat filtresiyle
  `PRICE_MIN`-`PRICE_MAX` (5.000-150.000 TL, config.py) + çok satanlar/varsayılan sıralama. Doğrulanmış biçimler:
  Trendyol `sst=BEST_SELLER&prc=lo-hi`, n11 `minp/maxp`, Teknosa `s=%3AbestSellerPoint-desc%3ApriceValue%3Alo-hi`,
  Hepsiburada `filtreler=fiyat:lo-hi` (`fiyat=` çalışmıyor), MediaMarkt `filter=currentprice:lo-hi`, Vatan `min/max`,
  İdefix `siralama=desc_score_best_selling&fiyat=lo-hi`, Amazon `low-price/high-price` (engel yüzünden test edilemedi).
  Hızlı tur 96 sn, 1689 ürün, aralık dışı 0, medyan ~16-28k TL.
- **Siteler arası karşılaştırma (2026-09-16 gece, `tracker/match.py`):** Kullanıcı sordu: "A sitesi fiyatı şişirip
  indiriyor ama B'de zaten ucuz". Kendi verimizde aynı ürün = ortak güçlü model kodu (7+ karakter, 2+ rakam) +
  çelişmeyen özellikler (GB/TB, işlemci, inç, mm) + fiyat farkı 2 katı geçmez. `/rakamlı ek` koda katılır
  (TAC-12CHSD/XA51I). Hariç tutulan kodlar match.NOT_MODEL'de (webOS26, HDR10, 1920X1080, LPDDR5-4800, 8GB-256GB...).
  Test: 1689 üründe 198 eşleşme, rastgele 20'nin ~19'u doğru. Her ürüne `cmp` {site, price, url, name, n, max}.
  Tablo: "X'de Y TL" (başka sitede %3+ ucuz), "N sitenin en ucuzu", "Eski fiyat piyasa üstü" (üstü çizili >
  diğer sitelerin en yükseği ×1.10). **Varsayılan filtre artık "Sahte / başka yerde ucuz olanları gizle"**
  (ownFake, cmpInflated, cheaperElsewhere). Yeni indirim ölçüsü: "Diğer sitelerdeki en ucuz fiyat".
  Örnek: n11 "%33 indirimli" Bosch WGA25203TR 29.095 TL, üstü çizili 43.210; diğer 4 site 29.205-34.999 -> sahte.
- **Fiyat karşılaştırma sitesi ve Amazon KALDIRILDI (2026-09-16 gece, kullanıcı kararı):** Yasallık konuşmasından
  sonra (karşılaştırma sitelerinin veritabanı hakları, kullanım koşulları, engel aşma riski) kullanıcı bir fiyat
  karşılaştırma sitesinden veri alan deneme modülünü tamamen sildirdi ve Amazon'u çıkardı. Model kodu mantığı
  (`NOT_MODEL`, `model_codes`) `match.py`'de.
  **KURAL: Sadece otomatik okumayı engellemeyen mağaza siteleri kullanılır. Captcha/bot kontrolü atlatılmaz;
  bir site kalıcı engellerse listeden çıkarılır. Fiyat karşılaştırma sitelerinden (Akakçe, Cimri, Epey vb.) veri alınmaz.**
  Kalan 7 site: Trendyol, n11, Teknosa, Hepsiburada, MediaMarkt, Vatan, İdefix.
  Online tablo herkese açık ama link paylaşılmadı (kullanıcı bilinçli olarak böyle bıraktı).
  Git geçmişi kullanıcı onayıyla tek commit'e indirildi (2026-09-16), eski commit'ler GitHub'dan force push ile silindi.
- **4 gün sonra kontrol + fiyat hatası avı (2026-09-20):** Masaüstü 4 gündür kesintisiz; 7 sitenin hepsi ürün
  döndürüyor, engel/0 ürün yok. Geçmişte 8.893 ürün, 3.753'ünün fiyatı değişmiş.
  - **Veri gürültüsü bulundu:** İdefix'te 8 üründe ilk kayıt 99.000 TL (yer tutucu); 30 üründe salınım
    (aynı ilanda farklı satıcı/varyant, ör. PS5 Pro 85.999 <-> 45.350); 4 günde 153 kez tek adımda %30+ düşüş.
  - **Çözümler:** (1) `record_price`: bir fiyat ancak arka arkaya iki taramada aynı görülürse geçmişe yazılır
    (tek seferlik aksaklıklar elenir, gerçek değişiklik 5 dk gecikir). (2) `clean_history`: ilk nokta sonrakinin
    1,5 katıysa ve <30 dk sürdüyse atılır (eski 99.000'ler temizlendi). (3) `same_listing`: ilan adı tamamen
    değişirse geçmiş sıfırlanır. (4) `price_stats.volatile`: son 7 günde tekrar eden değerler + 1,5 kat fark.
  - **Fiyat hatası kuralı (kullanıcı isteği):** normal fiyatı >= `ERROR_MIN_NORMAL_PRICE` (10.000 TL) olan ürün,
    tipik fiyatının (avg7_prev, yoksa max30) `ERROR_DROP_PCT` (%60) altına inerse; salınan ilanlar hariç;
    diğer sitede fiyatı varsa onun da %60'ından ucuz olmalı. Tabloda kırmızı "FİYAT HATASI?" rozeti + filtre.
    4 günlük veride %60'ta 0 ürün (doğru: gerçek hata olmamış), %50'de 3, %35'te 6 - o 6'sı da site düzeltmesi,
    gerçek hata değil. Kullanıcı "ürün kaçsın ama yanlış alarm olmasın" dedi -> %60'ta kalındı.
  - **Kapsam 2 katı:** `QUICK_PAGES = 2` (hızlı turda kategori başına 2 sayfa). Ölçüm: 125 sn, 3.143 tekil ürün
    (önce ~1.700). 5 dk sınırına sığıyor.
  - **"Ani düşüş" denetimi (kullanıcı sordu: bundle mı, satıcı şişirdi mi?):** 27 düşüşün 23'ü aynı zamanda
    gördüğümüz en düşük fiyattaydı (şişirme numarası bizi kandırmamış), 2'si "geri dönüş" (önce yükselmiş
    sonra eski seviyesine inmiş; ör. Kärcher SC4 seri 15.569->10.999->15.569->13.019), 1'i paket ilanı.
    Sadece 3'ü başka siteyle doğrulanabildi (çoğunda model kodu yok).
    Düzeltmeler: (a) "Ani düşüş" için ek şart `price <= min30*1.02`, değilse "Eski seviyesine döndü" etiketi;
    aynı şart fiyat hatası kuralına da eklendi. (b) Adında +/set/hediye/paket/2'li geçen ilanlara "Paket"
    etiketi (içerik değişebilir, karşılaştırma güvenilmez) - "465 Litre" yanlış eşleşmesi \b ile düzeltildi.
- **Fiyat hatası kuralı değişti (2026-09-21, kullanıcı isteği):** Eski kural tek bir düşük gözlemi hata sayıyordu
  ve yanlış alarm verdi (İdefix'te 16 Eylül'de 99.000 TL yer tutucusu 4 gün kaldı, 20 Eylül'de gerçek fiyat
  33.660 gelince "%66 hata" göründü). Yeni tanım: **fiyat düşecek ve kısa sürede eski seviyesine dönecek.**
  - `track_dip` (run.py) ham fiyatla çalışır (iki taramalık doğrulamayı beklemez, hatalar 5-20 dk sürüyor).
    Tipik fiyat = son onaylanmış fiyat. Düşüş kaydı `data/dips.json`.
  - `ERROR_RECOVER_PCT` (85) içinde `ERROR_MAX_MIN` (20 dk) dönerse `confirmed=True` (doğrulanmış hata);
    daha geç dönerse confirmed=False; 60 dk'dan uzun sürerse `permanent=True` (kalıcı indirim, hata değil)
    ve aynı seviyede yeniden kayıt açılmaz. Kayıtlar `DIP_KEEP_HOURS` (48) sonra silinir.
  - Tabloda: devam eden düşüş "ŞU AN DÜŞÜK · izleniyor" (skor 20, en üstte), dönmüş olan "FİYAT HATASI ✓ %X · N dk".
    "Fiyat hatası" sekmesi ikisini de gösterir.
  - **İdefix 99.000 TL yer tutucusu** artık ayrıştırıcıda atlanıyor; `clean_history` eski kayıtları da siliyor.
  - Birim testler: 5 dk'da dönen = hata, 25 dk'da dönen = hata değil, 60+ dk düşük kalan = kalıcı indirim.
  - **Not:** Doğrulanmış hata ancak olay bittikten sonra görünür. Yakalamak için "izleniyor" durumu + bildirim gerekir.
  - **Sekmeler (kullanıcı isteği):** İşaret açılır menüsü yerine üstte sekmeler: Fiyat hatası / Ani düşüş /
    30 günün en düşüğü / Gerçek fırsatlar (varsayılan) / Tümü. Her sekmede o an kaç ürün olduğu yazılı;
    "Fiyat hatası" sekmesi doluysa kırmızı yanar. Seçili sekme localStorage'da (`tab`).
    Sayılar diğer süzgeçlerden (fiyat, arama, site) sonra hesaplanır.
  - **Tablo varsayılanları değişti:** sıralama "Geçmiş" puanına göre (fiyat hatası > ani düşüş > 30g en düşük >
    en ucuz), min indirim %30 yerine %0. Sitenin iddia ettiği indirim çoğu gerçek fırsatta %0 olduğu için
    eski varsayılan iyi fırsatları gizliyordu.
- **Bekleme dönemi (2026-09-16'dan itibaren, kullanıcı kararı):** Veri birikmesi bekleniyor, yeni özellik eklenmiyor.
  Beklenen takvim: 2-3 gün "ani düşüş", 7 gün (~23 Eylül) "30 günün en düşüğü"/"sahte indirim", 1 ay gerçek 30g en düşük.
- **Sıradaki adım (~19 Eylül ve ~23 Eylül):** Kullanıcıyla birlikte kontrol: masaüstü log'u
  (`%LOCALAPPDATA%\indirim\tracker.log`, masaüstünde) ve `docs/deals.json` status alanında 0 ürün / engel var mı;
  siteler HTML değiştirdi mi; rozetler (ani düşüş, 30g en düşük, sahte, siteler arası) gerçek veride mantıklı mı,
  yanlış eşleşme var mı. `data/history.json` sadece okunur (laptopta tarama çalıştırma). Açık fikirler: telefon bildirimi (Telegram/ntfy), "ortalamanın %X altında" gösterimi,
  giyim/kozmetik/süpermarket kategorileri (kullanıcı henüz karar vermedi), çoklu alım/birim fiyat.
  Birkaç gün sonra rozetlerin (ani düşüş, 30g en düşük, sahte) gerçek veride mantıklı çalıştığını kontrol et.
  claude.ai/code ile GitHub'dan çalışılırsa değişiklikler Drive'a `git pull` ile gelmeli.
