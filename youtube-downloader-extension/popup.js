// popup.js - Handles the extension popup logic

let currentVideoInfo = null;
let isDownloading = false;

// DOM Elements
const notYoutubeEl = document.getElementById('notYoutube');
const videoInfoEl = document.getElementById('videoInfo');
const videoTitleEl = document.getElementById('videoTitle');
const videoUrlEl = document.getElementById('videoUrl');
const qualityOptionsEl = document.getElementById('qualityOptions');
const qualitySelect = document.getElementById('quality');
const downloadBtn = document.getElementById('downloadBtn');
const refreshBtn = document.getElementById('refreshBtn');
const statusEl = document.getElementById('status');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');

// Initialize popup
async function init() {
  // Get current tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  if (!tab || !tab.url.includes('youtube.com')) {
    showNotYouTube();
    return;
  }

  // Check if it's a video page
  if (!tab.url.includes('watch?v=') && !tab.url.includes('youtu.be/')) {
    showNotYouTube();
    return;
  }

  // Get video info from content script
  try {
    const response = await chrome.tabs.sendMessage(tab.id, { action: 'getVideoInfo' });
    
    if (response && response.success) {
      currentVideoInfo = response;
      showVideoInfo();
    } else {
      showNotYouTube();
    }
  } catch (error) {
    console.log('Could not get video info:', error);
    // Try to get info from tab URL
    const videoId = extractVideoId(tab.url);
    if (videoId) {
      currentVideoInfo = {
        videoId: videoId,
        url: tab.url,
        title: 'YouTube Video'
      };
      showVideoInfo();
    } else {
      showNotYouTube();
    }
  }
}

function showNotYouTube() {
  notYoutubeEl.style.display = 'block';
  videoInfoEl.style.display = 'none';
  qualityOptionsEl.style.display = 'none';
  downloadBtn.style.display = 'none';
  refreshBtn.style.display = 'block';
}

function showVideoInfo() {
  notYoutubeEl.style.display = 'none';
  videoInfoEl.style.display = 'block';
  qualityOptionsEl.style.display = 'block';
  downloadBtn.style.display = 'block';
  refreshBtn.style.display = 'none';

  videoTitleEl.textContent = currentVideoInfo.title || 'YouTube Video';
  videoUrlEl.textContent = currentVideoInfo.url;
  downloadBtn.disabled = false;
}

function extractVideoId(url) {
  const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)/);
  return match ? match[1] : null;
}

function showStatus(message, type = 'info') {
  statusEl.textContent = message;
  statusEl.className = 'status ' + type;
}

function hideStatus() {
  statusEl.className = 'status';
  statusEl.textContent = '';
}

function startProgress() {
  progressContainer.classList.add('active');
  progressFill.style.width = '0%';
  progressText.textContent = 'Preparing download...';
}

function updateProgress(percent, text) {
  progressFill.style.width = percent + '%';
  if (text) progressText.textContent = text;
}

function stopProgress() {
  progressContainer.classList.remove('active');
}

async function downloadVideo() {
  if (!currentVideoInfo || isDownloading) return;
  
  isDownloading = true;
  downloadBtn.disabled = true;
  startProgress();

  try {
    const quality = qualitySelect.value;
    
    updateProgress(10, 'Fetching video information...');
    
    // Send download request to background script
    const response = await chrome.runtime.sendMessage({
      action: 'downloadVideo',
      videoUrl: currentVideoInfo.url,
      quality: quality,
      videoId: currentVideoInfo.videoId,
      title: currentVideoInfo.title
    });

    if (response && response.success) {
      updateProgress(100, 'Download started!');
      showStatus('Download started! Check your downloads folder.', 'success');
      
      // Reset after 3 seconds
      setTimeout(() => {
        stopProgress();
        hideStatus();
      }, 3000);
    } else {
      throw new Error(response?.error || 'Download failed');
    }
  } catch (error) {
    console.error('Download error:', error);
    showStatus('Error: ' + error.message, 'error');
    stopProgress();
  } finally {
    isDownloading = false;
    downloadBtn.disabled = false;
  }
}

// Event Listeners
downloadBtn.addEventListener('click', downloadVideo);

refreshBtn.addEventListener('click', () => {
  init();
});

// Initialize on load
init();
