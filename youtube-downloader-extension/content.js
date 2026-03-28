// content.js - Injected into YouTube pages to extract video information

(function() {
  'use strict';

  // Detect when page is a YouTube video page
  function isYouTubeVideoPage() {
    return window.location.href.includes('youtube.com/watch?v=') || 
           window.location.href.includes('youtu.be/');
  }

  // Extract video ID from URL
  function getVideoId() {
    const match = window.location.href.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)/);
    return match ? match[1] : null;
  }

  // Extract video title
  function getVideoTitle() {
    // Try multiple methods to get the title
    
    // Method 1: From page title
    let title = document.title;
    if (title) {
      // Remove common YouTube title suffixes
      title = title.replace(/\s*-\s*YouTube$/i, '').trim();
      return title;
    }

    // Method 2: From meta tags
    const metaTitle = document.querySelector('meta[property="og:title"]');
    if (metaTitle) {
      return metaTitle.getAttribute('content');
    }

    // Method 3: From structured data
    const script = document.querySelector('script[type="application/ld+json"]');
    if (script) {
      try {
        const data = JSON.parse(script.textContent);
        if (data && data.name) {
          return data.name;
        }
      } catch (e) {
        // Ignore JSON parse errors
      }
    }

    return 'YouTube Video';
  }

  // Extract video metadata
  function getVideoMetadata() {
    const videoId = getVideoId();
    const title = getVideoTitle();
    const url = window.location.href;

    // Try to extract player response data
    let playerResponse = null;
    const playerDataScript = document.querySelector('script#player-response');
    if (playerDataScript) {
      try {
        playerResponse = JSON.parse(playerDataScript.textContent);
      } catch (e) {
        // Ignore parse errors
      }
    }

    // Extract available formats if available
    const formats = [];
    if (playerResponse && playerResponse.streamingData) {
      const streamingData = playerResponse.streamingData;
      
      if (streamingData.formats) {
        streamingData.formats.forEach(format => {
          formats.push({
            itag: format.itag,
            mimeType: format.mimeType,
            quality: format.quality,
            url: format.url || null
          });
        });
      }

      if (streamingData.adaptiveFormats) {
        streamingData.adaptiveFormats.forEach(format => {
          formats.push({
            itag: format.itag,
            mimeType: format.mimeType,
            quality: format.quality,
            bitrate: format.bitrate,
            url: format.url || null
          });
        });
      }
    }

    return {
      videoId: videoId,
      title: title,
      url: url,
      formats: formats,
      hasFormats: formats.length > 0
    };
  }

  // Check for video element
  function getVideoElement() {
    return document.querySelector('video');
  }

  // Listen for messages from popup/background
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getVideoInfo') {
      if (!isYouTubeVideoPage()) {
        sendResponse({ success: false, error: 'Not a YouTube video page' });
        return;
      }

      const metadata = getVideoMetadata();
      const videoElement = getVideoElement();

      sendResponse({
        success: true,
        ...metadata,
        isPlaying: videoElement ? !videoElement.paused : false,
        currentTime: videoElement ? videoElement.currentTime : 0,
        duration: videoElement ? videoElement.duration : 0
      });
    }

    if (request.action === 'getVideoUrl') {
      const videoElement = getVideoElement();
      if (videoElement && videoElement.src) {
        sendResponse({
          success: true,
          src: videoElement.src
        });
      } else {
        sendResponse({
          success: false,
          error: 'Could not get video source'
        });
      }
    }

    if (request.action === 'captureFrame') {
      const videoElement = getVideoElement();
      if (videoElement) {
        const canvas = document.createElement('canvas');
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob((blob) => {
          sendResponse({
            success: true,
            blobUrl: URL.createObjectURL(blob)
          });
        }, 'image/jpeg', 0.8);
      } else {
        sendResponse({
          success: false,
          error: 'No video element found'
        });
      }
    }

    return true; // Keep channel open for async responses
  });

  // Expose function for popup to call directly
  window.__youtubeDownloader = {
    getVideoInfo: getVideoMetadata,
    isYouTubeVideoPage: isYouTubeVideoPage,
    getVideoId: getVideoId,
    getVideoTitle: getVideoTitle
  };

  console.log('YouTube Downloader content script loaded');
})();
