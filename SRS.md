# MouseLife Tracker — Software Requirements Specification

## 1. Project Overview

**MouseLife Tracker** is a Windows-based mouse click tracking application that automatically counts mouse clicks made by a user's mouse and stores the statistics persistently.

The initial target mouse is a **Portronics mouse rated for approximately 3,000,000 clicks**.

The application should run in the background while the user uses Windows normally.

The user should NOT need to interact with the tracker application to count clicks.

Example:

```text
Connect mouse
      ↓
Windows detects mouse
      ↓
MouseLife Tracker runs in background
      ↓
User uses laptop normally
      ↓
Every mouse click is detected
      ↓
Click statistics are stored
```

---

# 2. Main Objective

The system must answer:

> "How many clicks has my mouse made since I started tracking it, and how much of its rated click lifespan have I used?"

Example:

```text
Rated lifespan:    3,000,000 clicks
Tracked clicks:      150,420 clicks
Remaining:         2,849,580 clicks
Life used:              5.01%
```

---

# 3. Target Platform

Primary platform:

* Windows 10
* Windows 11

The first version does not need macOS or Linux support.

---

# 4. System Components

The system consists of three primary components.

## 4.1 Windows Mouse Agent

The agent is responsible for:

* Detecting global mouse clicks
* Counting left clicks
* Counting right clicks
* Counting middle clicks
* Maintaining local statistics
* Persisting unsynchronized data
* Synchronizing data with the backend
* Running in the background
* Supporting Windows startup
* Providing system-tray controls

Recommended technology:

* Python
* pynput or equivalent Windows-compatible mouse event library

---

# 5. Backend

Technology:

* Node.js
* Express
* Mongoose

Responsibilities:

* Receive click synchronization data
* Validate requests
* Store click statistics
* Maintain mouse information
* Maintain daily statistics
* Maintain tracking sessions
* Provide APIs for the dashboard

---

# 6. Database

Database:

**MongoDB Atlas**

The database must store persistent mouse statistics.

Recommended collections:

* mice
* click_sessions
* daily_statistics

---

# 7. Frontend

Technology:

* React
* Vite
* Recharts

The frontend is a web dashboard for visualizing mouse usage.

It should provide:

* Total clicks
* Left clicks
* Right clicks
* Middle clicks
* Rated lifespan
* Remaining clicks
* Percentage of lifespan used
* Daily statistics
* Weekly statistics
* Monthly statistics
* Session history
* Tracker status

---

# 8. Functional Requirements

## FR-01 Global Click Detection

The Windows agent shall detect mouse button events globally.

Clicks must be detected regardless of which application has focus.

Examples:

* Chrome
* VS Code
* File Explorer
* Desktop
* Other Windows applications

The tracker dashboard does NOT need to be focused.

---

## FR-02 Left Click

Every detected left mouse click shall increment:

```text
leftClicks += 1
totalClicks += 1
```

---

## FR-03 Right Click

Every detected right mouse click shall increment:

```text
rightClicks += 1
totalClicks += 1
```

---

## FR-04 Middle Click

Every detected middle mouse click shall increment:

```text
middleClicks += 1
totalClicks += 1
```

---

## FR-05 Persistent Storage

Click data must survive:

* Tracker restart
* Backend restart
* Dashboard restart
* Windows restart

The agent must not depend entirely on MongoDB for real-time counting.

---

## FR-06 Offline Support

If:

* Internet is unavailable
* Backend is unavailable
* MongoDB is temporarily unavailable

the agent must continue counting clicks.

Unsynchronized click data must remain stored locally.

When connectivity returns, the agent should synchronize the pending data.

---

## FR-07 Batch Synchronization

The system must NOT send an HTTP request for every mouse click.

Instead:

```text
Mouse click
    ↓
Local counter
    ↓
Local persistence
    ↓
Periodic batch synchronization
    ↓
Backend
    ↓
MongoDB
```

The synchronization interval should be configurable.

---

## FR-08 Daily Statistics

Maintain statistics by date.

Each daily record should contain:

* Date
* Left clicks
* Right clicks
* Middle clicks
* Total clicks

---

## FR-09 Tracking Sessions

Maintain tracking sessions.

Each session should contain:

* Mouse ID
* Start time
* End time
* Duration
* Left clicks
* Right clicks
* Middle clicks
* Total clicks

---

## FR-10 Mouse Information

Store:

* Mouse name
* Manufacturer
* Model
* Rated click lifespan
* Tracking start date
* Current click totals

Example:

```text
Manufacturer: Portronics
Rated clicks: 3,000,000
```

---

## FR-11 Mouse Lifespan Calculation

Use:

```text
lifeUsedPercentage =
(totalClicks / ratedClicks) × 100
```

Use:

```text
remainingClicks =
max(ratedClicks - totalClicks, 0)
```

The application must never display a negative remaining-click value.

---

## FR-12 Dashboard

The dashboard should display:

### Main Statistics

```text
Total Clicks
Left Clicks
Right Clicks
Middle Clicks
```

### Lifespan

```text
Rated Clicks
Used Clicks
Remaining Clicks
Life Used %
```

### Analytics

```text
Daily Clicks
Weekly Clicks
Monthly Clicks
```

### Sessions

Display recent tracking sessions.

---

# 9. System Tray

The Windows agent should preferably run as a system-tray application.

Tray menu:

```text
MouseLife Tracker

● Tracking

Total Clicks: 150,420

Open Dashboard

Pause Tracking

Resume Tracking

Exit
```

---

# 10. Pause / Resume

The user should be able to pause tracking.

When paused:

* Mouse clicks are NOT counted.

When resumed:

* Mouse clicks are counted again.

---

# 11. Windows Startup

The agent should support automatic Windows startup.

Expected behavior:

```text
Turn on laptop
      ↓
Windows starts
      ↓
MouseLife Tracker starts
      ↓
Agent runs in background
```

The user should not need to manually launch the tracker every day.

---

# 12. Privacy Requirements

The application must ONLY monitor mouse button events required for click counting.

It must NOT:

* Record keyboard input
* Record typed text
* Capture screenshots
* Monitor clipboard contents
* Record browser history
* Record URLs
* Collect passwords
* Monitor application content

Only mouse button events required for counting may be processed.

---

# 13. Dashboard UI

Create a modern, clean dashboard.

Example:

```text
╔══════════════════════════════════════════════╗
║             🖱️ MOUSELIFE TRACKER             ║
╠══════════════════════════════════════════════╣
║                                              ║
║  Status: ● Tracking                          ║
║                                              ║
║  TOTAL CLICKS                                ║
║      150,420                                 ║
║                                              ║
║  LEFT          RIGHT          MIDDLE         ║
║  110,200       40,180         40             ║
║                                              ║
║  MOUSE LIFESPAN                              ║
║                                              ║
║  ████████████░░░░░░░░  5.01%                 ║
║                                              ║
║  Rated:       3,000,000                      ║
║  Used:          150,420                      ║
║  Remaining:   2,849,580                      ║
║                                              ║
║  CLICK ACTIVITY                              ║
║  [Daily chart]                               ║
║                                              ║
║  RECENT SESSIONS                             ║
║  [Session table]                             ║
╚══════════════════════════════════════════════╝
```

---

# 14. Non-Functional Requirements

## Performance

The agent should use minimal CPU and memory.

## Reliability

Temporary connectivity failures must not cause permanent click loss.

## Persistence

Data must survive application and Windows restarts.

## Security

MongoDB credentials must never be exposed to the frontend.

## Maintainability

Use modular, clean architecture.

---

# 15. Important Limitation

The system tracks clicks from the moment tracking begins.

It cannot know how many clicks occurred before tracking started unless the physical mouse itself exposes an internal lifetime click counter.

The 3,000,000-click specification is a manufacturer-rated lifespan and is not a guarantee that the mouse will stop working exactly at 3,000,000 clicks.

---

# 16. Future Features

The architecture should allow future support for:

* Multiple mice
* Mouse identification
* Click heatmaps
* Clicks per minute
* Milestones
* Notifications
* CSV export
* JSON export
* Advanced analytics
* Multiple computers
* Cloud synchronization
* Authentication

These are not required for the first MVP.

---

# 17. Success Criteria

The project is successful when:

1. A real mouse click can be detected globally on Windows.
2. Left/right/middle clicks are counted correctly.
3. Clicks are saved reliably.
4. Data survives restarts.
5. Offline clicks are not lost.
6. Data synchronizes with MongoDB.
7. The React dashboard displays correct statistics.
8. The agent can run in the background.
9. The agent can start automatically with Windows.
10. The user can use the laptop normally without interacting with the tracker.
