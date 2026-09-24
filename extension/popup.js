/**
 * MouseLife Tracker — Chrome Extension Popup Logic
 * 
 * Read-only status viewer that communicates with the local Express API:
 *   GET http://localhost:5000/api/mice/portronics-default-01
 * 
 * Strictly READ-ONLY: Never registers click listeners, never logs clicks,
 * never modifies database values, never requests external telemetry.
 */

const API_PRIMARY = "http://localhost:5000/api/mice/portronics-default-01";
const API_FALLBACK = "http://127.0.0.1:5000/api/mice/portronics-default-01";
const DASHBOARD_URL = "http://localhost:5173/";
const RATED_CLICKS_DEFAULT = 3000000;

// DOM Elements
const elStatusBadge = document.getElementById("statusBadge");
const elStatusDot = document.getElementById("statusDot");
const elStatusText = document.getElementById("statusText");

const elErrorBanner = document.getElementById("errorBanner");
const elErrorTitle = document.getElementById("errorTitle");
const elErrorMsg = document.getElementById("errorMsg");
const elRetryBtn = document.getElementById("retryBtn");

const elDeviceName = document.getElementById("deviceName");
const elRemainingClicks = document.getElementById("remainingClicks");
const elLifeRemainingPct = document.getElementById("lifeRemainingPercentage");
const elProgressBar = document.getElementById("progressBar");

const elTotalClicks = document.getElementById("totalClicks");
const elLeftClicks = document.getElementById("leftClicks");
const elRightClicks = document.getElementById("rightClicks");
const elMiddleClicks = document.getElementById("middleClicks");

const elLeftPct = document.getElementById("leftPct");
const elRightPct = document.getElementById("rightPct");
const elMiddlePct = document.getElementById("middlePct");

const elRatedClicks = document.getElementById("ratedClicks");
const elLifeUsed = document.getElementById("lifeUsed");
const elLastUpdated = document.getElementById("lastUpdated");

const elRefreshBtn = document.getElementById("refreshBtn");
const elRefreshIcon = document.getElementById("refreshIcon");
const elOpenDashboardBtn = document.getElementById("openDashboardBtn");

let lastFetchedData = null;

// Helpers
function formatNumber(num) {
  if (typeof num !== "number" || isNaN(num)) return "--";
  return new Intl.NumberFormat("en-US").format(num);
}

function formatRelativeTime(dateString) {
  if (!dateString) return "Never";
  try {
    const diffMs = Date.now() - new Date(dateString).getTime();
    if (diffMs < 0) return "Just now";
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 10) return "Just now";
    if (diffSec < 60) return `${diffSec}s ago`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHrs = Math.floor(diffMin / 60);
    if (diffHrs < 24) return `${diffHrs}h ago`;
    return new Date(dateString).toLocaleDateString();
  } catch {
    return dateString;
  }
}

/**
 * Updates UI with mouse statistics.
 */
function updateUI(data) {
  const total = Number(data.totalClicks) || 0;
  const left = Number(data.leftClicks) || 0;
  const right = Number(data.rightClicks) || 0;
  const middle = Number(data.middleClicks) || 0;
  const rated = Number(data.ratedClicks) || RATED_CLICKS_DEFAULT;

  const remaining = Math.max(rated - total, 0);
  const usedPct = rated > 0 ? Number(((total / rated) * 100).toFixed(2)) : 0;
  const remainingPct = Number(Math.max(100 - usedPct, 0).toFixed(2));

  // Device & Main Hero
  if (data.name) elDeviceName.textContent = data.name;
  elRemainingClicks.textContent = formatNumber(remaining);
  elLifeRemainingPct.textContent = `${remainingPct}%`;

  // Progress Bar
  elProgressBar.style.width = `${Math.min(Math.max(remainingPct, 0), 100)}%`;
  if (remainingPct < 10) {
    elProgressBar.style.background = "linear-gradient(90deg, #f87171, #ef4444)";
  } else if (remainingPct < 25) {
    elProgressBar.style.background = "linear-gradient(90deg, #fbbf24, #f59e0b)";
  } else {
    elProgressBar.style.background = "linear-gradient(90deg, #06b6d4, #10b981)";
  }

  // Click Totals
  elTotalClicks.textContent = formatNumber(total);
  elLeftClicks.textContent = formatNumber(left);
  elRightClicks.textContent = formatNumber(right);
  elMiddleClicks.textContent = formatNumber(middle);

  // Button Percentages
  if (total > 0) {
    elLeftPct.textContent = `${((left / total) * 100).toFixed(1)}%`;
    elRightPct.textContent = `${((right / total) * 100).toFixed(1)}%`;
    elMiddlePct.textContent = `${((middle / total) * 100).toFixed(1)}%`;
  } else {
    elLeftPct.textContent = "0.0%";
    elRightPct.textContent = "0.0%";
    elMiddlePct.textContent = "0.0%";
  }

  // Meta info
  elRatedClicks.textContent = formatNumber(rated);
  elLifeUsed.textContent = `${usedPct}%`;

  // Last Synced Time
  const syncTime = data.lastSyncedAt || data.updatedAt;
  elLastUpdated.textContent = formatRelativeTime(syncTime);
  elLastUpdated.title = syncTime ? new Date(syncTime).toLocaleString() : "";

  // Tracker Status: Active if synced recently (within 15 minutes)
  const isRecent = syncTime && (Date.now() - new Date(syncTime).getTime() <= 15 * 60 * 1000);
  if (isRecent) {
    setStatus("active", "Tracker Active");
  } else {
    setStatus("unavailable", "Idle / Ready");
  }

  // Hide error banner
  elErrorBanner.classList.add("hidden");
}

function setStatus(type, label) {
  elStatusBadge.className = `status-badge ${type}`;
  elStatusText.textContent = label;
}

function showError(title, msg) {
  setStatus("offline", "Backend Offline");
  elErrorTitle.textContent = title;
  elErrorMsg.textContent = msg;
  elErrorBanner.classList.remove("hidden");
  elLastUpdated.textContent = "Unavailable";
}

/**
 * Fetches latest mouse statistics from local API.
 */
async function fetchStatistics() {
  elRefreshIcon.classList.add("spinning");
  elRefreshBtn.disabled = true;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 4000);

  let responseData = null;

  try {
    // Try primary URL first (localhost:5000)
    let res;
    try {
      res = await fetch(API_PRIMARY, {
        signal: controller.signal,
        headers: { "Accept": "application/json" }
      });
    } catch (primaryErr) {
      // Try fallback (127.0.0.1:5000)
      res = await fetch(API_FALLBACK, {
        signal: controller.signal,
        headers: { "Accept": "application/json" }
      });
    }

    clearTimeout(timeoutId);

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }

    const json = await res.json();
    if (!json.success || !json.data) {
      throw new Error("Invalid API payload format");
    }

    lastFetchedData = json.data;
    updateUI(lastFetchedData);
  } catch (err) {
    clearTimeout(timeoutId);
    console.warn("[MouseLife Extension] API Fetch Failed:", err);
    showError("Backend Offline", "Ensure backend service is running on port 5000");
  } finally {
    elRefreshIcon.classList.remove("spinning");
    elRefreshBtn.disabled = false;
  }
}

// ----------------------------------------------------------------------------
// Event Listeners
// ----------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  fetchStatistics();
});

elRefreshBtn.addEventListener("click", () => {
  fetchStatistics();
});

elRetryBtn.addEventListener("click", () => {
  fetchStatistics();
});

elOpenDashboardBtn.addEventListener("click", () => {
  if (typeof chrome !== "undefined" && chrome.tabs && chrome.tabs.create) {
    chrome.tabs.create({ url: DASHBOARD_URL });
  } else {
    window.open(DASHBOARD_URL, "_blank");
  }
});
