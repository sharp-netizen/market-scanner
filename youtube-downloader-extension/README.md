# YouTube Video Downloader - Chrome Extension

⚠️ **Important Disclaimer**: This extension is for **educational and personal use only**. Downloading YouTube videos may violate YouTube's Terms of Service and copyright laws. Respect content creators' rights.

## Overview

A Chrome extension that demonstrates video download functionality for YouTube. Due to YouTube's protections, direct downloads are blocked in most cases.

## Files

- **manifest.json** - Chrome Extension Manifest V3 configuration
- **popup.html** - Extension popup UI
- **popup.js** - Popup logic and download handling
- **background.js** - Service worker for downloads
- **content.js** - Content script injected on YouTube pages

## Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top right)
3. Click **Load unpacked**
4. Select the `youtube-downloader-extension` folder
5. The extension will be installed

## Usage

1. Navigate to any YouTube video
2. Click the extension icon in your toolbar
3. The popup will display video information
4. Click "Download Video" to attempt download

## What This Extension Does

- Detects YouTube video pages
- Extracts video metadata (title, URL, formats)
- Attempts to initiate downloads
- Handles YouTube's blob/stream URLs

## Limitations

⚠️ **Important**: YouTube actively blocks direct downloads through browsers. This extension demonstrates the concept but:

1. **Direct downloads are blocked** by YouTube's anti-piracy measures
2. **DRM-protected content** cannot be downloaded
3. **Some formats** are not accessible via browser extensions

## Alternatives

For legitimate video downloading:

1. **youtube-dl** - Command-line tool: `youtube-dl [URL]`
2. **yt-dlp** - Improved fork of youtube-dl
3. **YouTube Premium** - Official offline viewing
4. **Screen recording** - For personal use

## Technical Notes

- Uses Manifest V3 with service workers
- Content script injection on YouTube pages
- Chrome Downloads API integration
- Proper error handling for blocked downloads

## Privacy

- No data is collected
- No external servers involved
- All processing happens locally

## License

For educational purposes only.
