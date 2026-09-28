#!/usr/bin/env python3
"""Download Pal portraits from palworld.gg into ./images (run once, on your own computer).

Usage:  python3 download_images.py
Files are saved as images/<slug>.<ext>, e.g. images/azurobe-cryst.webp
"""
import os
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser

BASE = "https://palworld.gg"
HEADERS = {"User-Agent": "Mozilla/5.0 (personal fan project)"}


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=30).read()


class Cards(HTMLParser):
    """Finds the first real portrait <img> inside each /pal/<slug> link."""

    def __init__(self):
        super().__init__()
        self.cur = None
        self.found = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        href = a.get("href") or ""
        if tag == "a" and href.startswith("/pal/"):
            self.cur = href.rstrip("/").split("/")[-1]
        elif tag == "img" and self.cur and self.cur not in self.found:
            src = a.get("data-src") or a.get("src") or ""
            if not src or src.startswith("data:") or "/icons/" in src:
                return
            self.found[self.cur] = src

    def handle_endtag(self, tag):
        if tag == "a":
            self.cur = None


def resolve(src):
    # Next.js image URLs wrap the real path in ?url=...
    if "url=" in src:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(src).query).get("url")
        if q:
            src = q[0]
    return urllib.parse.urljoin(BASE, src)


def main():
    os.makedirs("images", exist_ok=True)
    parser = Cards()
    parser.feed(get(BASE + "/pals").decode("utf-8", "ignore"))
    if not parser.found:
        raise SystemExit("No portraits found on the page. The site layout may have changed.")
    print(f"Found {len(parser.found)} portraits")
    missing = []
    for slug, src in parser.found.items():
        url = resolve(src)
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower() or ".png"
        path = os.path.join("images", slug + ext)
        if os.path.exists(path):
            continue
        try:
            with open(path, "wb") as f:
                f.write(get(url))
            print("saved", path)
            time.sleep(0.15)
        except Exception as err:
            missing.append(slug)
            print("FAILED", slug, err)
    print("Done." + (f" Missing: {', '.join(missing)}" if missing else ""))


if __name__ == "__main__":
    main()
