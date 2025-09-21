# blog_scraper_clean.py
# -*- coding: utf-8 -*-
import os
import re
import json
import logging
import requests
from urllib.parse import urlparse
from flask import Flask, request, Response
from flask_cors import CORS
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
CORS(app)


def extract_images(container):
    image_urls = set()

    for img in container.find_all("img"):
        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-lazy-src")
            or img.get("data-original")
            or img.get("data-background")
        )
        if not src and img.get("srcset"):
            src = img["srcset"].split(",")[0].split()[0]

        if src:
            if src.startswith("//"):
                src = "https:" + src
            if src.startswith(("http://", "https://")):
                image_urls.add(src)

    for source in container.find_all("source"):
        srcset = source.get("srcset")
        if srcset:
            first = srcset.split(",")[0].split()[0]
            if first.startswith("//"):
                first = "https:" + first
            if first.startswith(("http://", "https://")):
                image_urls.add(first)

    for tag in container.find_all(style=True):
        style = tag["style"]
        for match in re.findall(r"url\((.*?)\)", style):
            url = match.strip("\"' ")
            if url.startswith("//"):
                url = "https:" + url
            if url.startswith(("http://", "https://")):
                image_urls.add(url)

    return list(image_urls)


def clean_html(container):
    for tag in container(["script", "style", "svg", "noscript"]):
        tag.decompose()

    for tag in container.find_all(True):
        if tag.name not in [
            "p", "h1", "h2", "h3", "ul", "ol", "li", "img",
            "strong", "em", "b", "i", "a"
        ]:
            tag.unwrap()
            continue

        if tag.name == "img":
            src = tag.get("src")
            if not src and tag.get("srcset"):
                src = tag["srcset"].split(",")[0].split()[0]
            if src and src.startswith("//"):
                src = "https:" + src

            if src:
                alt = tag.get("alt", "").strip() or "Image"
                tag.attrs = {"src": src, "alt": alt}
            else:
                tag.decompose()

        elif tag.name == "a":
            href = tag.get("href", "").strip()
            tag.attrs = {"href": href} if href else {}

        else:
            tag.attrs = {}

    return container


@app.post("/scrape-blog")
def scrape_blog():
    try:
        data = request.get_json(force=True)
        url = data.get("url")
        if not url:
            return Response("Missing 'url' field", status=400)

        parsed = urlparse(url)
        if "safeguardglobal.com" not in parsed.netloc:
            return Response("This scraper only works for safeguardglobal.com", status=403)

        resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # ✅ სათაური
        h1_tag = soup.find("h1", class_="text-brand-purple-black")
        title = h1_tag.get_text(strip=True) if h1_tag else ""

        # ✅ სტატია
        article = soup.find(
            "div",
            class_=lambda c: c and "lg:w-2/3" in c and "flex" in c and "gap-10" in c,
        )
        if not article:
            return Response("Could not extract blog content", status=422)

        clean_article = clean_html(article)

        # ✅ სურათები
        images = extract_images(clean_article)
        image_names = [f"image{i+1}.png" for i in range(len(images))]

        # ✅ content_html = <h1> + <article>
        content_html = f"<h1>{title}</h1><article>{str(clean_article).strip()}</article>"

        result = {
            "title": title,
            "content_html": content_html,
            "images": images,
            "image_names": image_names,
        }

        return Response(json.dumps(result, ensure_ascii=False), mimetype="application/json")
    except Exception as e:
        logging.exception("Error scraping blog")
        return Response(json.dumps({"error": str(e)}), status=500, mimetype="application/json")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
