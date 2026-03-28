// background.js - Service worker for handling downloads

// Listen for download requests from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'downloadVideo') {
    handleDownload(message)
      .then(response => sendResponse(response))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Keep channel open for async response
  }
});

async function handleDownload(options) {
  const { videoUrl, quality, videoId, title } = options;

  try {
    // Note: YouTube doesn't allow direct downloads due to DRM and Terms of Service
    // This is a simplified implementation that demonstrates the concept
    
    // In a real implementation, you would:
    // 1. Extract the video stream URLs from the YouTube page
    // 2. Use a proxy or backend service to fetch the video
    // 3. Handle the download with proper headers
    
    // For educational purposes, we'll try to initiate a download
    // Note: This may not work for all YouTube videos due to protections
    
    // Generate a filename
    const safeTitle = title.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 50);
    const filename = `${safeTitle}_${quality}.mp4`;
    
    // Try to download - Note: YouTube will likely block this
    // This demonstrates the concept but actual implementation requires
    // a backend service or different approach
    
    // Method 1: Try direct download (likely blocked by YouTube)
    try {
      const downloadId = await chrome.downloads.download({
        url: videoUrl,
        filename: filename,
        saveAs: true
      });
      
      return {
        success: true,
        message: 'Download initiated. Note: YouTube may block direct downloads.',
        downloadId: downloadId
      };
    } catch (downloadError) {
      // YouTube likely blocked the direct download
      return {
        success: false,
        error: 'YouTube blocks direct downloads. This is expected behavior. For educational purposes, consider using youtube-dl or similar tools locally.'
      };
    }
    
  } catch (error) {
    return {
      success: false,
      error: error.message || 'Unknown error occurred'
    };
  }
}

// Alternative approach: Provide information about the video
// This helps users understand what tools they can use locally
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'getDownloadInfo') {
    sendResponse({
      info: 'Direct browser downloads from YouTube are blocked.',
      alternatives: [
        'Use youtube-dl command line tool locally',
        'Use yt-dlp (youtube-dl fork with better support)',
        'Record the video using screen capture',
        'Use a YouTube Premium subscription for offline viewing'
      ],
      note: 'This extension demonstrates the concept but cannot bypass YouTube protections.'
    });
  }
});

// Extension installation handler
chrome.runtime.onInstalled.addListener(() => {
  console.log('YouTube Downloader extension installed');
  
  // Set default options
  chrome.storage.local.set({
    downloadPath: 'default',
    showNotifications: true
  });
});

// Handle download complete
chrome.downloads.onChanged.addListener((downloadDelta) => {
  if (downloadDelta.state && downloadDelta.state.current === 'complete') {
    if (chrome.notifications) {
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icon128.png',
        title: 'Download Complete',
        message: 'Your YouTube video has been downloaded!'
      });
    }
  }
});
