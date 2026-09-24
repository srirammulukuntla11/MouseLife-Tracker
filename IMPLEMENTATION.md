# MouseLife Tracker — Implementation Specification

## 1. Technology Stack

### Windows Agent

Use:

* Python 3.x
* pynput
* requests/httpx
* local persistence mechanism
* system tray library such as pystray
* packaging using PyInstaller or an equivalent Windows packaging solution

### Backend

Use:

* Node.js
* Express
* Mongoose
* MongoDB Atlas

Recommended additional packages:

* dotenv
* cors
* zod or Joi for validation
* helmet
* morgan or equivalent logging library

### Frontend

Use:

* React
* Vite
* Recharts
* Axios or fetch
* Modern CSS / Tailwind if appropriate

---

# 2. Repository Structure

Create:

```text
MouseLife-Tracker/

├── agent/
│   ├── src/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── tracker.py
│   │   ├── persistence.py
│   │   ├── sync.py
│   │   ├── tray.py
│   │   └── logger.py
│   │
│   ├── data/
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── backend/
│   ├── src/
│   │   ├── config/
│   │   ├── models/
│   │   ├── controllers/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── middleware/
│   │   └── server.js
│   │
│   ├── .env.example
│   ├── package.json
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── utils/
│   │   └── App.jsx
│   │
│   ├── .env.example
│   ├── package.json
│   └── README.md
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── SETUP.md
│
├── SRS.md
├── IMPLEMENTATION.md
└── README.md
```

Adjust the structure if a more professional architecture is required.

---

# 3. Agent Architecture

The Python agent should contain independent modules for:

### Mouse Listener

Responsible only for receiving mouse events.

### Counter

Responsible for incrementing:

```text
leftClicks
rightClicks
middleClicks
totalClicks
```

### Persistence

Responsible for saving local state.

### Synchronization

Responsible for sending batches to the backend.

### Tray

Responsible for:

* status
* pause
* resume
* dashboard
* exit

### Configuration

Read configuration from environment/config files.

---

# 4. Local Persistence

The agent must maintain a local source of unsynchronized click data.

Recommended design:

```text
Local persistent state

mouseId
total unsynced clicks
left unsynced clicks
right unsynced clicks
middle unsynced clicks
last successful synchronization
```

Use a reliable local format/database.

Do not rely solely on memory.

---

# 5. Synchronization

The agent should accumulate clicks locally.

Example:

```text
Left: 100
Right: 40
Middle: 2
Total: 142
```

Then send a batch:

```http
POST /api/clicks/sync
```

Example payload:

```json
{
  "mouseId": "...",
  "leftClicks": 100,
  "rightClicks": 40,
  "middleClicks": 2,
  "totalClicks": 142,
  "clientSessionId": "..."
}
```

The backend should acknowledge successful processing.

Only after successful acknowledgement should the corresponding local pending data be cleared.

---

# 6. Duplicate Protection

Synchronization must be designed to avoid double counting.

Use a unique synchronization/session identifier.

The backend should be able to recognize an already-processed synchronization request.

MongoDB transactions or atomic update operations may be used where appropriate.

---

# 7. MongoDB Models

## Mouse

Fields:

```text
name
manufacturer
model
ratedClicks
totalClicks
leftClicks
rightClicks
middleClicks
trackingStartedAt
createdAt
updatedAt
```

## ClickSession

Fields:

```text
mouseId
startedAt
endedAt
duration
leftClicks
rightClicks
middleClicks
totalClicks
createdAt
```

## DailyStatistic

Fields:

```text
mouseId
date
leftClicks
rightClicks
middleClicks
totalClicks
createdAt
updatedAt
```

Create a unique index for:

```text
mouseId + date
```

---

# 8. Backend APIs

Implement:

```text
GET    /api/health

POST   /api/mice
GET    /api/mice
GET    /api/mice/:id

POST   /api/clicks/sync

GET    /api/mice/:id/statistics/daily
GET    /api/mice/:id/statistics/weekly
GET    /api/mice/:id/statistics/monthly

GET    /api/mice/:id/sessions

POST   /api/sessions/start
POST   /api/sessions/end
```

Use controllers/services instead of placing all logic inside route files.

---

# 9. Environment Variables

Backend:

```env
PORT=5000
MONGODB_URI=
CORS_ORIGIN=
```

Agent:

```env
API_BASE_URL=http://localhost:5000
MOUSE_ID=
SYNC_INTERVAL_SECONDS=10
```

Frontend:

```env
VITE_API_URL=http://localhost:5000
```

Never commit real credentials.

---

# 10. Dashboard Pages

Initial application can use one main dashboard.

Components:

```text
Dashboard
├── Header
├── TrackerStatus
├── TotalClicksCard
├── ClickTypeCards
├── LifespanCard
├── LifespanProgress
├── DailyClickChart
├── ClickDistributionChart
├── RecentSessions
└── MouseInformation
```

---

# 11. UI States

Implement:

### Loading

Show a proper loading state.

### Empty

If no clicks have been recorded:

```text
No click data yet.
Start using your mouse to begin tracking.
```

### Offline

Show:

```text
Backend unavailable
Local tracking continues.
```

### Tracker inactive

Show:

```text
Tracker offline
```

### Tracking

Show:

```text
● Tracking
```

---

# 12. Calculations

Use:

```text
lifeUsed =
(totalClicks / ratedClicks) * 100
```

Use:

```text
remainingClicks =
max(ratedClicks - totalClicks, 0)
```

Do calculations carefully and avoid floating-point display problems.

---

# 13. Agent System Tray

Tray menu:

```text
MouseLife Tracker
-----------------
Status: Tracking
Total: 150,420
-----------------
Open Dashboard
Pause Tracking
Resume Tracking
Exit
```

When paused:

```text
Status: Paused
```

No clicks should be recorded while paused.

---

# 14. Windows Startup

Use a reliable Windows startup mechanism.

Possible approaches:

* Startup folder
* Windows registry Run key
* packaged executable
* Windows Task Scheduler if appropriate

Choose the safest and simplest production approach.

Document how it works.

---

# 15. Packaging

Package the Python agent as a Windows executable.

The user should eventually be able to run something similar to:

```text
MouseLifeTracker.exe
```

without needing to manually execute Python commands.

---

# 16. Logging

The agent should maintain useful logs for:

* startup
* tracker status
* synchronization
* synchronization failures
* retry attempts
* errors

Do not log sensitive information.

---

# 17. Testing

Implement tests for:

### Click counter

```text
Left +1
Right +1
Middle +1
Total = sum
```

### Persistence

Restart agent and verify data remains.

### Offline

Disable backend/network.

Generate clicks.

Verify clicks remain locally.

Restore backend.

Verify clicks synchronize.

### Duplicate sync

Send the same synchronization request twice.

Verify clicks are not counted twice.

### Lifespan

Verify:

```text
3,000,000 total
0% used
```

and:

```text
150,000 total
5% used
2,850,000 remaining
```

### API

Test all important endpoints.

---

# 18. Security

Implement:

* environment variables
* CORS configuration
* request validation
* secure MongoDB configuration
* Helmet
* error handling

Never expose:

```text
MONGODB_URI
```

to React.

---

# 19. Privacy

The agent must only capture:

```text
mouse button type
```

It must never capture:

```text
keyboard input
typed text
screenshots
clipboard
URLs
browser history
passwords
application content
```

---

# 20. Development Priority

Implement in this order:

1. Project structure
2. Mouse click detection
3. Local persistence
4. Backend health/API
5. MongoDB
6. Click synchronization
7. Daily statistics
8. React dashboard
9. System tray
10. Windows startup
11. Tests
12. Packaging
13. Documentation

Do not build unnecessary future features before the core functionality works.

---

# 21. Definition of Done

The implementation is complete only when:

* Real mouse clicks are detected globally.
* Left/right/middle clicks work.
* Total clicks are correct.
* Clicks survive restarts.
* Offline tracking works.
* Synchronization works.
* Duplicate synchronization is protected.
* MongoDB stores correct totals.
* Daily statistics work.
* Dashboard displays correct values.
* Charts work.
* System tray works.
* Pause/resume works.
* Windows startup works.
* Windows executable can be built.
* Documentation is complete.
