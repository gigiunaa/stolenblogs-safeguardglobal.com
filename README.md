# Safeguard Global Blog Scraper (Render)

A tiny Flask service that scrapes **only** `safeguardglobal.com` blog pages and returns cleaned HTML + image URLs.

## Deploy to Render

### Option A: One‑click via `render.yaml`
1. Create a **New Web Service** on [Render](https://dashboard.render.com/).
2. Connect your repo (or upload this folder) containing `render.yaml`.
3. Render auto-detects and builds; it will run:
   ```bash
   pip install -r requirements.txt
   gunicorn blog_scraper_clean:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

### Option B: Without `render.yaml`
- Create a **Web Service** (Environment = *Python*).
- Set **Build Command**: `pip install -r requirements.txt`
- Set **Start Command**: `gunicorn blog_scraper_clean:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
- Add `PORT` env var if Render doesn’t inject it automatically.

## Endpoints

- `GET /` — health check
  ```json
  {"status":"ok","service":"safeguardglobal-blog-scraper"}
  ```

- `POST /scrape-blog` — scrape a Safeguard Global blog post
  - Request JSON:
    ```json
    {
      "url": "https://www.safeguardglobal.com/resources/blog/peo-vs-payroll-services/"
    }
    ```
  - Response JSON:
    ```json
    {
      "title": "PEO vs. payroll services ...",
      "content_html": "<div>...cleaned html...</div>",
      "images": ["https://..."],
      "image_names": ["image1.png", "image2.png"]
    }
    ```

> ⚠️ The service rejects non‑SafeguardGlobal URLs with HTTP 403.
