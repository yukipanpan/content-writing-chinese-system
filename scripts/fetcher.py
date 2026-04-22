"""
fetcher.py — Detects URL type and extracts content before passing to Claude.

Supported sources:
  - YouTube (youtube.com, youtu.be)  → transcript via youtube-transcript-api
                                       CI note: GitHub Actions runners are IP-blocked
                                       by YouTube — local use only.
  - Twitter / X (twitter.com, x.com) → full post via ADHX API (no key required)
                                        CI note: GitHub Actions DNS cannot resolve
                                        api.adhx.com — local use only.
  - Everything else                  → webpage body via requests + BeautifulSoup
                                       Works in all environments including CI.
"""

import re
import sys
import requests
from typing import NamedTuple


class FetchResult(NamedTuple):
    url: str
    source_type: str   # "youtube" | "twitter" | "web"
    title: str
    content: str
    error: str | None  # None if successful


# ── URL type detection ──────────────────────────────────────────────────────

def detect_type(url: str) -> str:
    if re.search(r"(youtube\.com/watch|youtu\.be/)", url):
        return "youtube"
    if re.search(r"(twitter\.com|x\.com)/\w+/status/", url):
        return "twitter"
    return "web"


def extract_video_id(url: str) -> str | None:
    patterns = [
        r"youtube\.com/watch\?v=([^&]+)",
        r"youtu\.be/([^?]+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


# ── YouTube ─────────────────────────────────────────────────────────────────

def fetch_youtube(url: str) -> FetchResult:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
    except ImportError:
        return FetchResult(url, "youtube", "", "",
                           "youtube-transcript-api not installed. Run: pip install youtube-transcript-api")

    video_id = extract_video_id(url)
    if not video_id:
        return FetchResult(url, "youtube", "", "", f"Could not extract video ID from: {url}")

    try:
        text = _youtube_get_text(YouTubeTranscriptApi, NoTranscriptFound, video_id)
        title = f"YouTube video {video_id}"
        content = (
            f"[YouTube Transcript]\n"
            f"Video ID: {video_id}\n"
            f"URL: {url}\n\n"
            f"{text}"
        )
        return FetchResult(url, "youtube", title, content, None)
    except Exception as e:
        return FetchResult(url, "youtube", "", "", f"Transcript fetch failed: {e}")


def _youtube_get_text(Api, NoTranscriptFound, video_id: str) -> str:
    """
    Fetch transcript text, handling all known youtube-transcript-api versions:
      < 0.7  — class methods: Api.get_transcript(), Api.list_transcripts()
      0.7.x  — instance methods: Api().fetch(), Api().list()
      1.x    — instance methods: Api().get_transcript(), Api().list_transcripts()
    """
    def _segments_to_text(segments) -> str:
        return " ".join(
            s["text"] if isinstance(s, dict) else s.text
            for s in segments
        )

    api = Api()

    # Ordered preference: en → zh variants → any available
    lang_attempts = [["en"], ["zh", "zh-Hans", "zh-Hant"]]

    # Try instance method "fetch" (0.7.x)
    if hasattr(api, "fetch"):
        for langs in lang_attempts:
            try:
                return _segments_to_text(api.fetch(video_id, languages=langs))
            except NoTranscriptFound:
                continue
        # Fall back to any available
        tl = api.list(video_id) if hasattr(api, "list") else Api.list_transcripts(video_id)
        return _segments_to_text(next(iter(tl)).fetch())

    # Try instance method "get_transcript" (1.x)
    if hasattr(api, "get_transcript"):
        for langs in lang_attempts:
            try:
                return _segments_to_text(api.get_transcript(video_id, languages=langs))
            except NoTranscriptFound:
                continue
        tl_method = getattr(api, "list_transcripts", None) or getattr(api, "list", None)
        tl = tl_method(video_id)
        return _segments_to_text(next(iter(tl)).fetch())

    # Legacy class method (< 0.7)
    for langs in lang_attempts:
        try:
            return _segments_to_text(Api.get_transcript(video_id, languages=langs))
        except NoTranscriptFound:
            continue
    tl = Api.list_transcripts(video_id)
    return _segments_to_text(next(iter(tl)).fetch())


# ── Twitter / X via ADHX API ────────────────────────────────────────────────

def fetch_twitter(url: str) -> FetchResult:
    """
    ADHX API converts any x.com/twitter.com URL into structured JSON.
    Docs: https://adhx.com
    """
    api_url = "https://api.adhx.com/v1/tweet"
    try:
        resp = requests.get(api_url, params={"url": url}, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        author   = data.get("author", {}).get("name", "Unknown")
        handle   = data.get("author", {}).get("username", "")
        date     = data.get("created_at", "")
        text     = data.get("full_text") or data.get("text", "")
        thread   = data.get("thread", [])
        article  = data.get("article_content", "")  # long-form content if available

        body_parts = [f"@{handle} ({author}) — {date}\n\n{text}"]
        if thread:
            for i, reply in enumerate(thread, 1):
                body_parts.append(f"[Thread {i}] {reply.get('text', '')}")
        if article:
            body_parts.append(f"[Full article content]\n{article}")

        content = (
            f"[Twitter/X Post]\n"
            f"URL: {url}\n\n"
            + "\n\n".join(body_parts)
        )
        return FetchResult(url, "twitter", f"@{handle}: {text[:60]}…", content, None)

    except requests.HTTPError as e:
        return FetchResult(url, "twitter", "", "", f"ADHX API error {e.response.status_code}: {e}")
    except Exception as e:
        return FetchResult(url, "twitter", "", "", f"Twitter fetch failed: {e}")


# ── Generic webpage ──────────────────────────────────────────────────────────

def fetch_web(url: str) -> FetchResult:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return FetchResult(url, "web", "", "",
                           "beautifulsoup4 not installed. Run: pip install beautifulsoup4 requests")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "aside",
                          "header", "form", "iframe", "noscript"]):
            tag.decompose()

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else url

        # Prefer article / main content if available
        main = (
            soup.find("article")
            or soup.find("main")
            or soup.find(id=re.compile(r"content|article|post", re.I))
            or soup.find(class_=re.compile(r"content|article|post|body", re.I))
            or soup.body
        )
        text = main.get_text(separator="\n", strip=True) if main else soup.get_text(separator="\n", strip=True)

        # Collapse excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Cap at ~10k chars to avoid context overflow on large pages
        if len(text) > 10_000:
            text = text[:10_000] + "\n\n[… content truncated at 10,000 chars …]"

        content = f"[Web Page: {title}]\nURL: {url}\n\n{text}"
        return FetchResult(url, "web", title, content, None)

    except requests.HTTPError as e:
        return FetchResult(url, "web", "", "", f"HTTP {e.response.status_code} for {url}")
    except Exception as e:
        return FetchResult(url, "web", "", "", f"Fetch failed: {e}")


# ── Public interface ─────────────────────────────────────────────────────────

def fetch_all(urls: list[str]) -> tuple[str, list[str]]:
    """
    Fetch all URLs. Returns:
      - combined_content: single string ready to pass to Claude
      - warnings: list of error messages for failed fetches
    """
    results = []
    warnings = []

    for url in urls:
        url = url.strip()
        if not url:
            continue

        source_type = detect_type(url)
        print(f"  fetching [{source_type}] {url}", file=sys.stderr)

        if source_type == "youtube":
            r = fetch_youtube(url)
        elif source_type == "twitter":
            r = fetch_twitter(url)
        else:
            r = fetch_web(url)

        if r.error:
            warnings.append(f"⚠ {url}: {r.error}")
            results.append(f"--- Source ({source_type}): {url} ---\n[FETCH FAILED: {r.error}]\n")
        else:
            results.append(f"--- Source ({source_type}): {url} ---\n{r.content}\n")

    combined = "\n\n".join(results)
    return combined, warnings
