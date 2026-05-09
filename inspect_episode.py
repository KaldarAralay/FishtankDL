"""
Opens an episode page in a persistent-profile Chromium window so you can log in
once (via Google or email), then captures every network request so we can
identify how the video is actually served (direct MP4, HLS manifest, etc.).

Run: python inspect_episode.py <episode_url>
The first run: a browser window opens. Log in, play the video briefly, then
close the window. A report of media/video-ish URLs is written to captured.txt.
Subsequent runs reuse the same login (stored in ./browser_profile).
"""

import sys
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE_DIR = Path(__file__).parent / "browser_profile"
OUTPUT_FILE = Path(__file__).parent / "captured.txt"

# URL substrings / extensions that are likely video-related
MEDIA_HINTS = re.compile(
    r"\.(mp4|m3u8|ts|mpd|m4s|webm|mov)(\?|$)|video|stream|playlist|media|cdn",
    re.IGNORECASE,
)


def main():
    if len(sys.argv) < 2:
        print("Usage: python inspect_episode.py <episode_url>")
        sys.exit(1)

    url = sys.argv[1]
    PROFILE_DIR.mkdir(exist_ok=True)
    captured: list[tuple[str, str, dict]] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1400, "height": 900},
            accept_downloads=True,
        )

        def on_request(req):
            if MEDIA_HINTS.search(req.url):
                captured.append(
                    (
                        req.method,
                        req.url,
                        {
                            k: v
                            for k, v in req.headers.items()
                            if k.lower()
                            in {"range", "referer", "origin", "cookie", "authorization"}
                        },
                    )
                )

        def on_response(resp):
            ct = resp.headers.get("content-type", "")
            if (
                "video" in ct
                or "mpegurl" in ct
                or "dash" in ct
                or MEDIA_HINTS.search(resp.url)
            ):
                captured.append(("RESP " + str(resp.status), resp.url, {"content-type": ct}))

        page = ctx.new_page()
        page.on("request", on_request)
        page.on("response", on_response)

        print(f"Opening {url}")
        print("Log in if needed, click play on the video, then close the browser.")
        page.goto(url, wait_until="domcontentloaded")

        # Block until the browser is closed manually.
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass

        ctx.close()

    # Deduplicate by URL, keep first occurrence
    seen: set[str] = set()
    unique: list[tuple[str, str, dict]] = []
    for m, u, h in captured:
        if u in seen:
            continue
        seen.add(u)
        unique.append((m, u, h))

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for m, u, h in unique:
            f.write(f"{m}  {u}\n")
            for k, v in h.items():
                f.write(f"    {k}: {v}\n")
            f.write("\n")

    print(f"\nCaptured {len(unique)} media-ish requests -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
