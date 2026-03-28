# How to Download YouTube Videos

## Recommended Tool: yt-dlp

`yt-dlp` is the most reliable and actively maintained tool for downloading YouTube videos.

### Step 1: Install yt-dlp

**macOS (using Homebrew):**
```bash
brew install yt-dlp
```

**Python/pip:**
```bash
pip install yt-dlp
```

### Step 2: Download a Video

**Basic download:**
```bash
yt-dlp "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Download best quality (video + audio merged):**
```bash
yt-dlp -f best "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Download specific format (1080p with audio):**
```bash
yt-dlp -f "bestvideo[height<=1080]+bestaudio" "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Download as MP4 (most compatible):**
```bash
yt-dlp -f mp4 "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Download only audio (MP3):**
```bash
yt-dlp -x --audio-format mp3 "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Step 3: Useful Options

| Option | Description |
|--------|-------------|
| `-o filename` | Custom output filename |
| `--playlist` | Download entire playlist |
| `-c` | Resume partial downloads |
| `--subtitles` | Download subtitles (cc) |
| `-v` | Verbose output for debugging |

**Example with custom filename:**
```bash
yt-dlp -o "%(title)s.%(ext)s" "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Download playlist to folder:**
```bash
yt-dlp -o "%(playlist)s/%(title)s.%(ext)s" "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

### Notes
- Downloads save to your current directory by default
- Requires FFmpeg for merging video/audio (install via `brew install ffmpeg`)
- Respect YouTube's Terms of Service and copyright laws
