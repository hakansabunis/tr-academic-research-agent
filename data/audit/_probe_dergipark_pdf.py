"""Probe DergiPark article landing pages: find PDF download links."""
import requests, re, sys

URLS = [
    'https://dergipark.org.tr/en/pub/gazimmfd/article/1745517',
    'https://dergipark.org.tr/en/pub/ejovoc/article/73192',
    'https://dergipark.org.tr/en/pub/akusosbil/article/1079030',
]

HEADERS = {'User-Agent': 'audit-probe'}

for url in URLS:
    print(f'\n=== {url} ===')
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except Exception as e:
        print(f'  FAIL: {e}')
        continue
    print(f'  status={r.status_code}  len={len(r.text):,}')

    patterns = [
        ('article-file', r'href="(/[a-z]{2}/download/article-file/\d+)"'),
        ('article-file alt', r'href="(/download/article-file/\d+)"'),
        ('pdf direct', r'href="([^"]+\.pdf)"'),
        ('citation_pdf_url meta', r'<meta\s+name="citation_pdf_url"\s+content="([^"]+)"'),
    ]
    for name, p in patterns:
        found = re.findall(p, r.text)
        if found:
            print(f'  HIT [{name}]: {found[0]}')
            break
    else:
        print(f'  no PDF link pattern matched')
