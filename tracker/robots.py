"""robots.txt denetimi: taradığımız adresler sitelerin kurallarına uygun mu?

Çalıştırma:  python -m tracker.robots

Kural: sadece "User-agent: *" bloğuna bakılır (bizim gibi genel bir istemci için geçerli olan).
Bir adres Disallow kalıbına uyuyorsa ve daha belirgin bir Allow yoksa taranmaz.
Yeni site/kategori eklerken bu denetim çalıştırılmalı.
"""
import re
import sys
import time
from urllib.parse import urlparse

from curl_cffi import requests

from .config import CATEGORIES

HEADERS = {"Accept-Language": "tr-TR,tr;q=0.9"}


def fetch_rules(netloc):
    """-> [(disallow|allow, kalıp)] ; sadece User-agent: * bloğu"""
    text = requests.get(f"https://{netloc}/robots.txt", impersonate="chrome",
                        timeout=20, headers=HEADERS).text
    rules, in_star = [], False
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            in_star = value == "*"
        elif in_star and key in ("disallow", "allow") and value:
            rules.append((key, value))
    return rules


def _matches(pattern, target):
    return re.match("^" + re.escape(pattern).replace(r"\*", ".*").replace(r"\$", "$") + ".*", target) is not None


def disallowed(rules, url):
    """Adres yasaklıysa eşleşen Disallow kalıplarını döndürür, değilse boş liste."""
    p = urlparse(url)
    target = p.path + ("?" + p.query if p.query else "")
    dis = [v for k, v in rules if k == "disallow" and _matches(v, target)]
    allow = [v for k, v in rules if k == "allow" and _matches(v, target)]
    return [] if allow else dis


def main():
    cache, problems = {}, 0
    for site, cats in CATEGORIES.items():
        urls = [u for _, pages in cats for u in pages]
        netloc = urlparse(urls[0]).netloc
        if netloc not in cache:
            cache[netloc] = fetch_rules(netloc)
            time.sleep(1)
        bad = [(u, d) for u in urls if (d := disallowed(cache[netloc], u))]
        problems += len(bad)
        print(f"{site:12} {len(urls):3} adres | yasak: {len(bad)}")
        for u, d in bad[:3]:
            print(f"    {d} <- {u}")
    print("\nSONUÇ:", "tüm adresler izinli" if not problems else f"{problems} adres yasaklı - config.py düzeltilmeli")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
