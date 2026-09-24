# MouseLife Tracker — Setup & Operations Guide

## 1. System Requirements

- **Operating System**: Windows 10 or Windows 11
- **Python**: 3.10+ (tested on Python 3.13)
- **Node.js**: 18+ (tested on Node v24.11)
- **Database**: MongoDB (Local MongoDB Server or MongoDB Atlas)

---

## 2. Quick Start (All Components)

### Step 1: Clone & Install Agent
```powershell
cd agent
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

### Step 2: Install & Start Backend
```powershell
cd ..\backend
npm install
npm run dev
```
Backend will start on `http://127.0.0.1:5000` and automatically connect to `mongodb://127.0.0.1:27017/mouselife` (or `MONGODB_URI` from `.env`).

### Step 3: Install & Start Frontend Dashboard
```powershell
cd ..\frontend
npm install
npm run dev
```
Open your browser at `http://127.0.0.1:5173/`.

### Step 4: Run Windows Mouse Agent
```powershell
cd ..\agent
.\venv\Scripts\python src\main.py
```
A system tray icon with a mouse silhouette will appear near your Windows clock.
Mouse clicks across all applications (Chrome, VS Code, Explorer, Desktop, games) will immediately be counted and synced to your dashboard!

---

## 3. Windows Automatic Startup

To configure MouseLife Tracker to start silently whenever your computer boots up:

```powershell
.\venv\Scripts\python src\main.py --install-startup
```
This generates a silent `.vbs` script in `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\MouseLifeTracker.vbs`.

To disable automatic startup:
```powershell
.\venv\Scripts\python src\main.py --uninstall-startup
```

To verify status:
```powershell
.\venv\Scripts\python src\main.py --status
```

---

## 4. Building Standalone Windows Executable

To compile the agent into a single, standalone Windows `.exe` that does not require Python:

```powershell
cd agent
.\venv\Scripts\python build_exe.py
```
The compiled binary will be placed at `agent\dist\MouseLifeTracker.exe`.

---

## 5. Offline & Recovery Behavior

If your network goes offline or the Express backend is stopped:
1. The Windows Agent continues counting clicks locally in its transactional SQLite database (`agent/data/mouselife_local.db`).
2. The Dashboard displays a warning banner stating that tracking continues offline.
3. Once connectivity returns, the agent automatically flushes all pending batches.
4. Zero clicks are lost!
