#!/usr/bin/env python3
"""
clone_static.py
Clone a static webpage: download HTML + linked CSS/JS/images and rewrite local links.
Limitations: won't run JS; only downloads assets referenced in HTML.
"""
import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse, urldefrag

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; simple-cloner/1.0)"}

def safe_filename(url):
    # create a filesystem-friendly filename from a URL path+query
    parsed = urlparse(url)
    path = parsed.path
    if path.endswith("/"):
        path += "index.html"
    name = (path + ("?" + parsed.query if parsed.query else "")).lstrip("/")
    name = re.sub(r'[^A-Za-z0-9._-]', '_', name)
    return name

def make_dirs_for_file(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def download_file(session, url, outpath):
    try:
        r = session.get(url, headers=HEADERS, timeout=20, stream=True)
        r.raise_for_status()
    except Exception as e:
        print(f"[WARN] Failed to download {url}: {e}")
        return False
    make_dirs_for_file(outpath)
    with open(outpath, "wb") as f:
        for chunk in r.iter_content(8192):
            if chunk:
                f.write(chunk)
    print(f"[OK] {url} -> {outpath}")
    return True

def gather_asset_urls(soup, base_url):
    urls = set()
    # CSS files (link rel=stylesheet)
    for tag in soup.find_all("link", href=True):
        rel = (tag.get("rel") or [])
        if "stylesheet" in rel or tag.get("type") == "text/css" or tag.get("href").endswith(".css"):
            urls.add(urljoin(base_url, tag["href"]))
    # script src
    for tag in soup.find_all("script", src=True):
        urls.add(urljoin(base_url, tag["src"]))
    # images
    for tag in soup.find_all("img", src=True):
        urls.add(urljoin(base_url, tag["src"]))
    # other common assets (source, video poster, etc.)
    for tag in soup.find_all(src=True):
        # include any remaining src attributes (audio, video, source)
        urls.add(urljoin(base_url, tag["src"]))
    # CSS @import in style tags or style attributes - simple regex search for url(...)
    for style_tag in soup.find_all("style"):
        txt = style_tag.string or ""
        for m in re.findall(r'url\(([^)]+)\)', txt):
            u = m.strip(' \'"')
            urls.add(urljoin(base_url, u))
    # inline styles on tags
    for tag in soup.find_all(style=True):
        txt = tag["style"]
        for m in re.findall(r'url\(([^)]+)\)', txt):
            u = m.strip(' \'"')
            urls.add(urljoin(base_url, u))
    return {urldefrag(u)[0] for u in urls if u and not u.startswith("data:")}

def rewrite_links_to_local(soup, base_url, url_to_local):
    # link[href]
    for tag in soup.find_all(href=True):
        new = url_to_local.get(urljoin(base_url, tag["href"]))
        if new:
            tag["href"] = new
    # script[src]
    for tag in soup.find_all(src=True):
        new = url_to_local.get(urljoin(base_url, tag["src"]))
        if new:
            tag["src"] = new
    # style tag contents: naive replacement of url(...)
    for style_tag in soup.find_all("style"):
        txt = style_tag.string or ""
        def repl(m):
            raw = m.group(1).strip(' \'"')
            new = url_to_local.get(urljoin(base_url, raw))
            return f"url('{new}')" if new else m.group(0)
        new_txt = re.sub(r'url\(([^)]+)\)', repl, txt)
        style_tag.string = new_txt
    # inline style attributes
    for tag in soup.find_all(style=True):
        txt = tag["style"]
        def repl2(m):
            raw = m.group(1).strip(' \'"')
            new = url_to_local.get(urljoin(base_url, raw))
            return f"url('{new}')" if new else m.group(0)
        tag["style"] = re.sub(r'url\(([^)]+)\)', repl2, txt)
    return soup

def clone_page(url, out_dir="cloned_site"):
    session = requests.Session()
    os.makedirs(out_dir, exist_ok=True)
    r = session.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    # Gather asset URLs
    assets = gather_asset_urls(soup, url)

    # Map remote -> local relative paths
    url_to_local = {}
    for a in assets:
        local_path = safe_filename(a)
        local_rel = local_path  # stored relative to out_dir
        url_to_local[a] = local_rel

    # Download assets
    for a, local_rel in url_to_local.items():
        outpath = os.path.join(out_dir, local_rel)
        try:
            download_file(session, a, outpath)
        except Exception as e:
            print(f"[WARN] cannot save {a}: {e}")

    # rewrite links in HTML to local files
    soup = rewrite_links_to_local(soup, url, url_to_local)

    # Save modified HTML
    # Determine filename for the main html
    parsed = urlparse(url)
    html_name = "index.html"
    if parsed.path and parsed.path not in ("/", ""):
        html_name = safe_filename(url)
    html_out = os.path.join(out_dir, html_name)
    make_dirs_for_file(html_out)
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(str(soup))
    print(f"[DONE] Saved page to {html_out}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python clone_static.py <url> [output_dir]")
        sys.exit(1)
    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "cloned_site"
    clone_page(url, out)
