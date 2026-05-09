"""
Download a fishtank.live episode as MP4.

Episodes are served via Bunny Stream HLS. The segments are readable with just
the correct Referer header — no per-request token — so yt-dlp can fetch the
master playlist directly and mux into MP4 via ffmpeg.

Usage:
    python download_episode.py <episode_url_or_uuid> [-o OUTPUT] [-q QUALITY]

Examples:
    python download_episode.py https://www.fishtank.live/episodes/f25a76ee-...
    python download_episode.py f25a76ee-befb-440e-9cee-d06abcd5b204 -o ep6.mp4
    python download_episode.py <url> -q 720p
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

CDN_HOST = "vz-a2fe5bfa-400.b-cdn.net"
REFERER = "https://player.mediadelivery.net/"
UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


def extract_uuid(arg: str) -> str:
    m = UUID_RE.search(arg)
    if not m:
        sys.exit(f"Could not find an episode UUID in: {arg}")
    return m.group(0).lower()


def build_playlist_url(uuid: str, quality: str | None) -> str:
    if quality:
        return f"https://{CDN_HOST}/{uuid}/{quality}/video.m3u8"
    return f"https://{CDN_HOST}/{uuid}/playlist.m3u8"


def main():
    ap = argparse.ArgumentParser(description="Download a fishtank.live episode.")
    ap.add_argument("episode", help="Episode URL or UUID")
    ap.add_argument(
        "-o", "--output",
        help="Output file path (default: <uuid>.mp4 in current dir)",
    )
    ap.add_argument(
        "-q", "--quality",
        help="Force a specific quality ladder (e.g. 1080p, 720p, 480p, 240p). "
             "Default: let yt-dlp pick the best from the master playlist.",
    )
    args = ap.parse_args()

    uuid = extract_uuid(args.episode)
    url = build_playlist_url(uuid, args.quality)
    output = args.output or f"{uuid}.mp4"

    print(f"Episode UUID : {uuid}")
    print(f"Playlist URL : {url}")
    print(f"Output       : {output}")
    print()

    cmd = [
        "yt-dlp",
        "--referer", REFERER,
        "--no-part",
        "--concurrent-fragments", "8",
        "--merge-output-format", "mp4",
        "-o", output,
        url,
    ]
    # If user didn't force a quality, tell yt-dlp to pick the best video+audio.
    if not args.quality:
        cmd[1:1] = ["-f", "bestvideo*+bestaudio/best"]

    print("Running:", " ".join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(f"yt-dlp exited with code {r.returncode}")

    final = Path(output)
    if final.exists():
        mb = final.stat().st_size / (1024 * 1024)
        print(f"\nDone: {final}  ({mb:.1f} MB)")


if __name__ == "__main__":
    main()
