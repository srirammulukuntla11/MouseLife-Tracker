# 🖱️ MouseLife Tracker

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?logo=windows)](https://www.microsoft.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Local-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)

**MouseLife Tracker** is a Windows utility and hardware wear monitoring system. It measures real-world mouse usage across all applications, persists click data locally in SQLite, synchronizes in idempotent batches to a Node.js/Express + MongoDB backend, and provides a real-time React dashboard displaying switch health against manufacturer lifespan ratings.

---

## 📋 Table of Contents
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [How It Works](#-how-it-works)
  - [Global Click Tracking](#1-global-click-tracking)
  - [SQLite Local Persistence & Offline Buffering](#2-sqlite-local-persistence--offline-buffering)
  - [Idempotent Backend Synchronization](#3-idempotent-backend-synchronization)
  - [MongoDB Historical Analytics](#4-mongodb-historical-analytics)
  - [React Analytics Dashboard](#5-react-analytics-dashboard)
- [Automatic Windows Startup & Crash Recovery](#-automatic-windows-startup--crash-recovery)
- [Privacy & Security](#-privacy--security)
- [Limitations](#-limitations)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
- [Running the Application](#-running-the-application)
- [Verification & Health Checks](#-verification--health-checks)
- [Automated Tests](#-automated-tests)
- [Release Strategy](#-release-strategy)

---

## 🚀 Key Features

- **Windows Global Mouse Hook**: Uses native Win32 `WH_MOUSE_LL` hooks attached to the active desktop message pump. Captures physical clicks globally across any application (browsers, IDEs, desktop, games, and file managers).
- **Exact Single-Click Counting**: Rigorously counts mouse button **DOWN** events (`WM_LBUTTONDOWN`, `WM_RBUTTONDOWN`, `WM_MBUTTONDOWN`) and ignores UP events. Exactly one physical mouse click produces one counted click.
- **Single-Process & Named Mutex Protection**: Enforces single-instance execution via Windows Named Mutex (`Local\MouseLifeTracker_SingleInstance_Mutex`). Duplicate background processes are completely prevented.
- **ACID Local SQLite Buffer**: Click counts write immediately to local SQLite in WAL mode (`mouselife_local.db`). Survives unexpected power loss, network drops, or system reboots.
- **Idempotent Batch Synchronization**: Local clicks sync to the backend every 5 seconds using cryptographic UUID batch tokens. If a network retry occurs, the backend deduplicates and prevents double-counting.
- **Hardware Lifespan Monitoring**: Computes remaining click budget and wear percentage against manufacturer-rated switch lifespans (default: Portronics 3,000,000 clicks).
- **Silent Windows Startup**: Auto-starts seamlessly on user login via Windows Registry Run keys without flashing terminal windows.
- **Backend Supervision & Crash Recovery**: A background supervisor monitors the Node.js API server and automatically restarts it within 3 seconds if an unexpected exit occurs.
- **On-Demand React Dashboard**: Premium dark-mode glassmorphic dashboard visualizing click totals, left/right/middle ratios, daily/weekly/monthly trends, and session histories. Started manually only when needed.

---

## 🏛️ System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        Windows Interactive Session                     │
│                                                                        │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │               Windows OS Low-Level Mouse Hook                │     │
│   │          (WH_MOUSE_LL -> Left / Right / Middle Down)         │     │
│   └──────────────────────────────┬───────────────────────────────┘     │
│                                  │ Real Clicks                         │
│                                  ▼                                     │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │              MouseLifeTracker (Background Agent)             │     │
│   │  • Named Mutex (Single Instance)   • System Tray Icon        │     │
│   │  • In-Memory Fast Counter          • Pause / Resume Control  │     │
│   └──────────────┬───────────────────────────────▲───────────────┘     │
│                  │ Instant ACID Write            │ Periodic Sync       │
│                  ▼                               │ (Every 5 seconds)   │
│   ┌──────────────────────────────┐               │                     │
│   │   Local SQLite (WAL Mode)    │               │                     │
│   │   • Unsynced click queue     │───────────────┘                     │
│   │   • Lifetime offline cache   │                                     │
│   └──────────────────────────────┘                                     │
│                                                                        │
│                                  │ Idempotent POST /api/clicks/sync    │
│                                  ▼ (UUID Batch Token)                  │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │            Node.js / Express API Service (Port 5000)         │     │
│   │  • Managed by Background Supervisor Daemon                   │     │
│   │  • Auto-Restarts on Crash                                    │     │
│   └──────────────────────────────┬───────────────────────────────┘     │
│                                  │ Mongoose ODM                        │
│                                  ▼                                     │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │               MongoDB (Service / 127.0.0.1:27017)            │     │
│   │  • Mice Metadata        • Daily / Weekly Aggregates          │     │
│   │  • Sync Batches         • Tracking Sessions                  │     │
│   └──────────────────────────────▲───────────────────────────────┘     │
│                                  │ GET /api/mice/:id                   │
│                                  │ (On-demand analytics queries)       │
│   ┌──────────────────────────────┴───────────────────────────────┐     │
│   │             React 18 + Vite Dashboard (Port 5173)            │     │
│   │  • Switch Wear Gauge    • Recharts Activity Trends           │     │
│   │  • Click Ratios         • Manual launch only when needed     │     │
│   └──────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 How It Works

### 1. Global Click Tracking
The agent installs a low-level mouse hook via Win32 `SetWindowsHookExW(WH_MOUSE_LL, ...)`. When a mouse message is intercepted:
- The hook checks if the event is a button-down transition (`WM_LBUTTONDOWN`, `WM_RBUTTONDOWN`, `WM_MBUTTONDOWN`).
- Button-up messages (`WM_LBUTTONUP`, etc.) and mouse movement events (`WM_MOUSEMOVE`) are ignored.
- The hook delegates to an in-memory accumulator and signals the Win32 message pump with `CallNextHookEx` to ensure zero perceptible input latency.

### 2. SQLite Local Persistence & Offline Buffering
Every click batch is recorded to `agent/data/mouselife_local.db` using SQLite in Write-Ahead Logging (WAL) mode:
- **Offline Resilience:** If the Node.js backend or MongoDB is offline, clicks continue accumulating safely in SQLite.
- **Reboot Safe:** Clicks remain preserved across system restarts and crashes.
- **Zero Data Loss:** When the backend comes online, the agent transmits all accumulated offline clicks in chronological order.

### 3. Idempotent Backend Synchronization
Every 5 seconds, the background worker extracts pending clicks from SQLite:
- It assigns a unique UUID (`batchId`) to each payload.
- It sends `POST /api/clicks/sync` to the backend.
- The backend checks MongoDB's `sync_batches` collection. If the `batchId` was already processed (e.g. following a network timeout retry), the duplicate is ignored and the previous response is returned without incrementing totals.

### 4. MongoDB Historical Analytics
The backend stores comprehensive analytics:
- **`mice`**: Cumulative lifetime clicks, button breakdowns, and switch lifespan calculations.
- **`daily_statistics`**: Per-day click counts for historical charting.
- **`click_sessions`**: Session start, end, and duration logs.
- **`sync_batches`**: Processed sync payloads for auditability and idempotency.

### 5. React Analytics Dashboard
The dashboard runs locally on Vite (`http://localhost:5173`):
- **Wear Meter:** Visual progress ring showing percentage of rated lifespan used.
- **Action Breakdown:** Left, right, and middle button counts with relative percentages.
- **Activity Charts:** Daily, weekly, and monthly trend graphs powered by Recharts.
- **Session History:** Log of recent tracking intervals.

---

## ⚡ Automatic Windows Startup & Crash Recovery

MouseLife Tracker includes automated, reliable Windows startup mechanisms configured through dedicated management scripts:

### Agent Automatic Startup
- **Registered In:** `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` -> `MouseLifeTracker`
- **Behavior:** Starts `MouseLifeTracker.exe` silently on user login.
- **Protection:** Win32 Named Mutex `Local\MouseLifeTracker_SingleInstance_Mutex` prevents duplicate processes.
- **Management:**
  ```powershell
  python setup_startup.py --install    # Configure agent auto-start (idempotent)
  python setup_startup.py --uninstall  # Remove agent auto-start
  python setup_startup.py --status     # Check status
  ```

### Backend Automatic Startup & Crash Recovery
- **Registered In:** `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` -> `MouseLifeBackend`
- **Behavior:** Launches `pythonw.exe backend/supervisor.py` without a console window.
- **Supervision:** The supervisor spawns `node.exe src/server.js` with `CREATE_NO_WINDOW`, redirects logs to `backend/logs/backend.log`, and **automatically restarts the server within 3 seconds** if it ever crashes.
- **Management:**
  ```powershell
  python setup_backend_startup.py --install    # Configure backend auto-start (idempotent)
  python setup_backend_startup.py --uninstall  # Remove backend auto-start
  python setup_backend_startup.py --status     # Check status
  python setup_backend_startup.py --health     # Verify http://localhost:5000/api/health
  python setup_backend_startup.py --start      # Start backend now in background
  python setup_backend_startup.py --stop       # Stop backend and supervisor
  ```

> **Note:** The React frontend dashboard is intentionally **NOT** registered for auto-startup. It is started manually only when you want to view analytics.

---

## 🔒 Privacy & Security

MouseLife Tracker is designed with strict privacy boundaries:

- ✅ **What it DOES track:**
  - Mouse button press events: Left Click, Right Click, Middle Click.
  - Timestamps of click batches.
  - Duration of tracking sessions.

- ❌ **What it DOES NOT track (and never collects):**
  - **No keystroke logging** or keyboard input.
  - **No screen capture**, window scraping, or screenshots.
  - **No clipboard access** or contents.
  - **No passwords**, credentials, or tokens.
  - **No browser history**, bookmarks, or visited URLs.
  - **No active window titles**, process names, or document contents.
  - **No mouse cursor coordinates** ($X, Y$ positions are discarded immediately).
  - **No telemetry** sent to any external server or cloud service. All data resides strictly on your local machine (`127.0.0.1`).

---

## ⚠️ Limitations

- **Tracking Scope:** The software counts physical clicks starting strictly from the point tracking is installed and running. It has no hardware interface to query or reconstruct clicks that occurred prior to installation.
- **Switch Wear Estimations:** Switch wear is calculated by comparing total clicks against manufacturer-published ratings (e.g. 3,000,000 clicks for standard switches). Actual mechanical failure rates depend on humidity, dust, click force, and manufacturing variances.
- **Operating System:** Low-level mouse hooks and Named Mutexes are native to Windows 10 and Windows 11 (64-bit).

---

## 📁 Project Structure

```text
MouseLife-Tracker/
├── .env.example                 # Root environment template
├── .gitignore                   # Comprehensive ignore rules
├── README.md                    # Project documentation
├── setup_startup.py             # Agent Windows startup CLI
├── setup_backend_startup.py     # Backend Windows startup & supervisor CLI
│
├── agent/                       # Windows Mouse Tracking Agent (Python)
│   ├── src/
│   │   ├── config.py            # Agent configuration & path resolution
│   │   ├── logger.py            # Rotating file logger
│   │   ├── main.py              # Single-instance entry point & Mutex
│   │   ├── persistence.py       # SQLite WAL persistence layer
│   │   ├── startup.py           # HKCU Registry Run manager
│   │   ├── sync.py              # Batch sync worker (5s interval)
│   │   ├── tracker.py           # Low-level WH_MOUSE_LL Win32 hook
│   │   └── tray.py              # System tray integration (Pystray)
│   ├── tests/                   # 16 Unit & integration tests
│   ├── build_exe.py             # PyInstaller executable compilation script
│   ├── mouselife_agent.spec     # PyInstaller spec configuration
│   └── requirements.txt         # Python dependencies
│
├── backend/                     # API & Persistence Service (Node.js/Express)
│   ├── src/
│   │   ├── config/db.js         # Mongoose MongoDB connection
│   │   ├── controllers/         # REST API route handlers
│   │   ├── middleware/          # Security headers, CORS, error handlers
│   │   ├── models/              # Mongoose schemas (Mouse, SyncBatch, etc.)
│   │   ├── routes/api.js        # Express router
│   │   ├── server.js            # Server entry point
│   │   └── services/            # Business logic
│   ├── tests/                   # Integration tests
│   ├── supervisor.py            # Silent supervisor with crash auto-recovery
│   └── package.json             # Backend dependencies
│
├── frontend/                    # Analytics Dashboard (React + Vite)
│   ├── src/
│   │   ├── components/          # Lifespan gauge, charts, tables
│   │   ├── services/api.js      # REST client for backend
│   │   ├── App.jsx              # Main dashboard view
│   │   └── index.css            # Dark glassmorphic design system
│   ├── package.json             # Frontend dependencies
│   └── vite.config.js           # Vite configuration
│
└── docs/                        # Architectural Specifications
    ├── ARCHITECTURE.md          # Deep technical design
    ├── API.md                   # REST API documentation
    └── SETUP.md                 # Setup & configuration guide
```

---

## 🛠️ Installation & Setup

### Prerequisites
1. **Windows 10 / 11** (64-bit).
2. **Python 3.10+** (ensure `python` is in your PATH).
3. **Node.js 18+** & `npm`.
4. **MongoDB Community Server** installed and running locally as a Windows service on `127.0.0.1:27017`.

### 1. Clone the Repository
```powershell
git clone <repository_url>
cd MouseLife-Tracker
```

### 2. Configure Environment Files
Copy the template files:
```powershell
copy .env.example backend\.env
copy .env.example agent\.env
copy frontend\.env.example frontend\.env
```

### 3. Install Dependencies
```powershell
# Install Backend Dependencies
cd backend
npm install
cd ..

# Install Frontend Dependencies
cd frontend
npm install
cd ..

# Install Agent Dependencies
cd agent
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
cd ..
```

---

## 💻 Running the Application

### Option A: Standard Background Services (Recommended)
Configure the backend and agent to run automatically with Windows:
```powershell
# 1. Enable and start the backend supervisor (silent, with crash recovery)
python setup_backend_startup.py --install
python setup_backend_startup.py --start

# 2. Enable agent auto-startup
python setup_startup.py --install

# 3. Launch the agent
python agent/src/main.py
```

### Option B: Running the React Dashboard (On Demand)
Whenever you want to inspect your mouse health and analytics:
```powershell
cd frontend
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## 🩺 Verification & Health Checks

### Check Backend Health
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/health"
```
*Expected response:*
```json
{
  "status": "ok",
  "service": "MouseLife Tracker API",
  "uptime": 12.4
}
```

### Check Mouse Click Statistics
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/mice/portronics-default-01"
```

### Check Auto-Start Registrations
```powershell
Get-CimInstance Win32_StartupCommand | Where-Object { $_.Name -like "*MouseLife*" } | Format-Table Name, Command -AutoSize
```

---

## 🧪 Automated Tests

### Python Agent Unit Tests
Tests low-level button down filtering, SQLite WAL persistence, Named Mutex enforcement, and batch sync:
```powershell
cd agent
.\venv\Scripts\python -m unittest discover tests/
```
*Expected result: 16 passed.*

### Backend Integration Tests
Tests REST endpoints, Mongoose models, and batch deduplication:
```powershell
cd backend
npm test
```

---

## 📦 Release Strategy

- **Source Code:** Maintained in Git following standard semantic versioning (`v1.0.0`).
- **Binary Distribution:** To keep the Git repository lightweight, compiled Windows binaries (`MouseLifeTracker.exe`) and distribution bundles are excluded from Git history via `.gitignore`.
- **Pre-built Executables:** Download pre-compiled binaries from the **[GitHub Releases](https://github.com/)** page attached to each tagged release.
- **Building From Source:** You can build the standalone executable anytime with:
  ```powershell
  cd agent
  python build_exe.py
  ```
  The single-process executable is generated in `agent/dist/MouseLifeTracker.exe`.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
