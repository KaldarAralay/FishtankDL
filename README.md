# fishtankDL

`fishtankDL` is a small command-line toolkit for downloading archived episodes from `fishtank.live`.

The main downloader takes either a full episode URL or an episode UUID, builds the Bunny Stream HLS playlist URL, and hands the download to `yt-dlp`. A second helper script can open the episode page in Chromium, let you log in, and capture video-related network requests when you need to inspect how an episode is being served.

Use this only for content you are allowed to access and download.

## Project Files

| Path | Purpose |
| --- | --- |
| `download_episode.py` | Main downloader. Converts an episode URL or UUID into a playlist URL and downloads it as an MP4 with `yt-dlp`. |
| `inspect_episode.py` | Browser/network inspection helper. Opens an episode in Chromium through Playwright and records media-like requests. |
| `captured.txt` | Output from `inspect_episode.py`. Useful for checking playlist, segment, CDN, and referer details. |
| `browser_profile/` | Persistent Chromium profile used by Playwright. Stores login/session data from inspection runs. |

## Requirements

Install these before using the scripts:

- Python 3.10 or newer
- `yt-dlp`
- `ffmpeg`
- Playwright for Python, only needed for `inspect_episode.py`
- Playwright's Chromium browser, only needed for `inspect_episode.py`

Check whether the command-line tools are already available:

```powershell
python --version
yt-dlp --version
ffmpeg -version
```

## Setup

From the project directory:

```powershell
cd C:\Users\sean1\OneDrive\Documents\ProgrammingProjects\fishtankDL
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the Python dependency used by the inspector:

```powershell
pip install playwright
python -m playwright install chromium
```

Install `yt-dlp` if it is not already installed:

```powershell
pip install yt-dlp
```

Install `ffmpeg` separately if your system does not already have it. On Windows, common options are:

```powershell
winget install Gyan.FFmpeg
```

or:

```powershell
winget install ffmpeg
```

After installing `ffmpeg`, open a new terminal and run:

```powershell
ffmpeg -version
```

## Quick Start

Download an episode with the default best available quality:

```powershell
python download_episode.py https://www.fishtank.live/episodes/f25a76ee-befb-440e-9cee-d06abcd5b204
```

The script will print:

- the extracted episode UUID
- the generated playlist URL
- the output file path
- the exact `yt-dlp` command it is running

By default, the output file is named after the UUID:

```text
f25a76ee-befb-440e-9cee-d06abcd5b204.mp4
```

## Downloading Episodes

### Download by URL

```powershell
python download_episode.py https://www.fishtank.live/episodes/<episode-uuid>
```

### Download by UUID

```powershell
python download_episode.py <episode-uuid>
```

Example:

```powershell
python download_episode.py f25a76ee-befb-440e-9cee-d06abcd5b204
```

### Choose an output filename

Use `-o` or `--output`:

```powershell
python download_episode.py f25a76ee-befb-440e-9cee-d06abcd5b204 -o episode-06.mp4
```

You can also write to another folder:

```powershell
python download_episode.py f25a76ee-befb-440e-9cee-d06abcd5b204 -o C:\Videos\fishtank\episode-06.mp4
```

Make sure the destination folder already exists.

### Force a quality

By default, `yt-dlp` selects the best video/audio combination from the master playlist:

```powershell
python download_episode.py <episode-uuid>
```

To force a specific quality ladder, use `-q` or `--quality`:

```powershell
python download_episode.py <episode-uuid> -q 1080p
python download_episode.py <episode-uuid> -q 720p
python download_episode.py <episode-uuid> -q 480p
python download_episode.py <episode-uuid> -q 240p
```

When quality is forced, the script downloads this playlist shape:

```text
https://vz-a2fe5bfa-400.b-cdn.net/<episode-uuid>/<quality>/video.m3u8
```

When quality is not forced, the script downloads this master playlist shape:

```text
https://vz-a2fe5bfa-400.b-cdn.net/<episode-uuid>/playlist.m3u8
```

## What the Downloader Does

`download_episode.py`:

1. Reads the episode URL or UUID from the command line.
2. Extracts the UUID with a regular expression.
3. Builds a Bunny CDN HLS playlist URL.
4. Runs `yt-dlp` with the required referer:

```text
https://player.mediadelivery.net/
```

5. Uses `ffmpeg` through `yt-dlp` to merge the HLS media into an MP4.

The generated `yt-dlp` command includes:

```text
--referer https://player.mediadelivery.net/
--no-part
--concurrent-fragments 8
--merge-output-format mp4
```

If no quality is forced, it also includes:

```text
-f bestvideo*+bestaudio/best
```

## Inspecting an Episode

Use `inspect_episode.py` when:

- the downloader stops working for a new episode
- you want to confirm the playlist URL
- you need to see which CDN host, playlist, quality, or media segments the site is requesting
- you need to log in before an episode page can be viewed

Run:

```powershell
python inspect_episode.py https://www.fishtank.live/episodes/<episode-uuid>
```

A Chromium window opens. In that window:

1. Log in if needed.
2. Navigate through any site prompts.
3. Click play on the episode video.
4. Let it play briefly so playlists and video segments load.
5. Close the browser window.

The script writes a deduplicated list of media-like network requests to:

```text
captured.txt
```

The capture includes request/response URLs and selected headers such as:

- `referer`
- `origin`
- `range`
- `cookie`
- `authorization`
- response `content-type`

## First-Run Login Behavior

`inspect_episode.py` uses a persistent Playwright Chromium profile:

```text
browser_profile/
```

That means:

- the first inspection run may require login
- later runs can reuse the same session
- deleting `browser_profile/` resets the browser state and removes saved login/session data

Because `browser_profile/` can contain session cookies or account data, do not share it publicly.

## Reading `captured.txt`

A useful capture usually contains lines like:

```text
GET  https://vz-a2fe5bfa-400.b-cdn.net/<episode-uuid>/playlist.m3u8
    referer: https://player.mediadelivery.net/

GET  https://vz-a2fe5bfa-400.b-cdn.net/<episode-uuid>/1080p/video.m3u8
    referer: https://player.mediadelivery.net/

GET  https://vz-a2fe5bfa-400.b-cdn.net/<episode-uuid>/1080p/video0.ts
    referer: https://player.mediadelivery.net/
```

The important parts are:

- the CDN host, currently `vz-a2fe5bfa-400.b-cdn.net`
- the episode UUID
- the available quality paths, such as `1080p` or `240p`
- the required referer, currently `https://player.mediadelivery.net/`

If the CDN host or referer changes, update the constants near the top of `download_episode.py`:

```python
CDN_HOST = "vz-a2fe5bfa-400.b-cdn.net"
REFERER = "https://player.mediadelivery.net/"
```

## Command Reference

### `download_episode.py`

```text
python download_episode.py <episode_url_or_uuid> [-o OUTPUT] [-q QUALITY]
```

Arguments:

| Argument | Description |
| --- | --- |
| `episode` | Required. A full episode URL or a UUID. |
| `-o`, `--output` | Optional. Output MP4 path. Defaults to `<uuid>.mp4` in the current directory. |
| `-q`, `--quality` | Optional. Force a quality path such as `1080p`, `720p`, `480p`, or `240p`. |

Examples:

```powershell
python download_episode.py https://www.fishtank.live/episodes/f25a76ee-befb-440e-9cee-d06abcd5b204
python download_episode.py f25a76ee-befb-440e-9cee-d06abcd5b204 -o ep6.mp4
python download_episode.py f25a76ee-befb-440e-9cee-d06abcd5b204 -q 720p -o ep6-720p.mp4
```

### `inspect_episode.py`

```text
python inspect_episode.py <episode_url>
```

Arguments:

| Argument | Description |
| --- | --- |
| `episode_url` | Required. Full `fishtank.live` episode page URL to open in Chromium. |

Example:

```powershell
python inspect_episode.py https://www.fishtank.live/episodes/f25a76ee-befb-440e-9cee-d06abcd5b204
```

## Troubleshooting

### `yt-dlp` is not recognized

Install it:

```powershell
pip install yt-dlp
```

Then close and reopen your terminal if needed.

### `ffmpeg` is not found

Install `ffmpeg` and make sure it is on your `PATH`:

```powershell
winget install Gyan.FFmpeg
```

Open a new terminal and verify:

```powershell
ffmpeg -version
```

### Playwright says Chromium is missing

Install the Playwright browser:

```powershell
python -m playwright install chromium
```

### The inspector opens, but nothing useful appears in `captured.txt`

Try this:

1. Make sure you are logged in.
2. Press play on the episode video.
3. Let the video run for at least a few seconds.
4. Scrub forward once to force more media requests.
5. Close the browser window after the video starts loading.

### The downloader returns HTTP 403 or fails immediately

The site may have changed its CDN host, referer requirement, or playlist layout.

Run the inspector:

```powershell
python inspect_episode.py https://www.fishtank.live/episodes/<episode-uuid>
```

Then check `captured.txt` for current `.m3u8` URLs and referer headers. Update `CDN_HOST` or `REFERER` in `download_episode.py` if needed.

### A forced quality fails

The requested quality may not exist for that episode. Try the default mode first:

```powershell
python download_episode.py <episode-uuid>
```

Or inspect the episode and check `captured.txt` for available quality folders.

### The output file is incomplete

Re-run the command. The script uses `--no-part`, so interrupted downloads do not leave normal `.part` resume files. If you need resumable behavior, remove `--no-part` from the `cmd` list in `download_episode.py`.

### Login is stale or broken in the inspector

Close any Playwright Chromium windows, delete `browser_profile/`, and run the inspector again:

```powershell
python inspect_episode.py https://www.fishtank.live/episodes/<episode-uuid>
```

You will need to log in again.

## Notes for Maintainers

- There is no package metadata or requirements file in this project yet.
- `download_episode.py` depends on external command-line tools, especially `yt-dlp` and `ffmpeg`.
- `inspect_episode.py` depends on the Python `playwright` package and an installed Playwright Chromium browser.
- The downloader assumes the current Bunny CDN host and Bunny Stream referer continue to work.
- `browser_profile/` should be treated as local/private runtime data, not source code.

## Typical Workflow

For normal use:

```powershell
python download_episode.py <episode-url-or-uuid> -o episode.mp4
```

When something changes or breaks:

```powershell
python inspect_episode.py <episode-url>
```

Then inspect `captured.txt`, adjust the constants or quality option if needed, and run the downloader again.
