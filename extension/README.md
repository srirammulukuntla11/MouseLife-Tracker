# 🖱️ MouseLife Tracker — Chrome Extension (V1)

A lightweight, read-only status viewer for your personal **MouseLife Tracker** system. It displays your current switch wear, remaining click budget, and button distributions directly inside Google Chrome without needing to open the full React dashboard.

---

## 📌 What This Extension Does
- **Instant Status Readout:** Shows your mouse switch lifespan percentage and remaining clicks at a glance.
- **Button Breakdown:** Displays left, right, and middle click counts with exact percentages.
- **Live Connection State:** Indicates whether the local tracking backend is active (`🟢 Tracker Active`) or offline (`🔴 Backend Offline`).
- **On-Demand Refresh:** Fetches the freshest click counts directly from your local Node.js/Express API.
- **Quick Dashboard Launcher:** Provides a one-click button to open the full React dashboard at `http://localhost:5173/`.

---

## 🚫 What This Extension DOES NOT Do
- ❌ **Does NOT count mouse clicks:** The Windows `MouseLifeTracker.exe` background agent is the sole component that intercepts and records physical mouse clicks via low-level OS hooks.
- ❌ **Does NOT monitor web pages:** Contains **zero** content scripts, DOM listeners, or website scrapers.
- ❌ **Does NOT collect keyboard input or passwords:** Has no access to typing, form inputs, or keystrokes.
- ❌ **Does NOT track browsing history:** Does not inspect visited tabs, bookmarks, or URLs.
- ❌ **Does NOT send external telemetry:** Only communicates locally with `http://localhost:5000/`.

---

## 🏛️ Architecture & Data Flow

```text
Physical Mouse Click
        ↓
MouseLifeTracker.exe (Windows Low-Level Hook)
        ↓
SQLite Local Buffer (mouselife_local.db)
        ↓ (Batch sync every 5s)
Node.js / Express Backend (http://localhost:5000)
        ↓
MongoDB Persistence
        ↓
Chrome Extension Popup (GET /api/mice/portronics-default-01)
```

The extension is strictly a **client-side consumer** of the local REST API. It never writes to databases, never alters click counters, and never sends increment payloads.

---

## 📥 How to Install in Google Chrome

1. Open **Google Chrome**.
2. Navigate to:
   ```text
   chrome://extensions/
   ```
3. In the top-right corner, toggle **Developer mode** to **ON**.
4. Click the **Load unpacked** button in the top-left toolbar.
5. In the file picker, select the `extension/` directory inside this repository:
   ```text
   <path-to-project>\MouseClick Tracker\extension
   ```
6. Click **Select Folder**.
7. Click the **Extensions** icon (puzzle piece) in the Chrome toolbar and click the **Pin** icon next to **MouseLife Tracker**.
8. Click the MouseLife Tracker icon to view your live stats!

---

## 🔄 How to Update the Extension

When you make changes to files inside `extension/`:
1. Go to `chrome://extensions/`.
2. Locate **MouseLife Tracker**.
3. Click the **Refresh** (circular arrow) icon on the extension card.
4. Re-open the popup to view your updates.

---

## 🔐 Required Permissions

In accordance with Chrome Manifest V3 least-privilege standards:
- **`host_permissions`:**
  - `http://localhost:5000/*`
  - `http://127.0.0.1:5000/*`
- **Other Permissions:** **None.** (No `tabs`, no `history`, no `cookies`, no `webNavigation`, no `scripting`).

---

## 🛠️ Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| **🔴 Backend Offline** | The Node.js API server is not running on port 5000 | Run `python setup_backend_startup.py --start` or `cd backend && npm start` |
| **🟡 Idle / Ready** | No mouse clicks have synced in the last 15 minutes | Click your mouse a few times; clicks will sync within 5 seconds |
| **Dashboard fails to open** | React frontend is not started | Start the dashboard with `cd frontend && npm run dev` |
| **Numbers not updating** | Offline buffer syncing | Click the **Refresh** button in the popup |

---

## 📊 Opening the Full Dashboard

Click the **Open Full Dashboard** button at the bottom of the popup or navigate directly to:
```text
http://localhost:5173/
```
*(Make sure the frontend is running via `cd frontend && npm run dev`)*
