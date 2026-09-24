# MouseLife Tracker — Antigravity Master Build Instruction

You are the lead developer for this project.

Two authoritative project documents are available in the workspace:

* `SRS.md`
* `IMPLEMENTATION.md`

Your job is to analyze these documents and then build the complete MouseLife Tracker application.

## STEP 1 — READ THE DOCUMENTS

Before writing code:

1. Read `SRS.md` completely.
2. Read `IMPLEMENTATION.md` completely.
3. Understand every functional and technical requirement.
4. Compare both documents.
5. Identify contradictions, missing details, or technically risky decisions.
6. Resolve minor implementation decisions using good engineering judgment.
7. Do not blindly follow a technically incorrect approach if a safer implementation is required.

Do not begin by creating a fake UI.

The real mouse tracking functionality is the core requirement.

---

# STEP 2 — CREATE AN IMPLEMENTATION PLAN

Before implementation, determine:

* complete architecture
* folder structure
* dependencies
* agent design
* local persistence strategy
* synchronization strategy
* MongoDB schema
* API design
* React architecture
* Windows startup approach
* packaging approach
* testing strategy

Then implement the project phase by phase.

---

# STEP 3 — BUILD THE REAL MOUSE TRACKER FIRST

The most important requirement is real global Windows mouse tracking.

The agent must detect:

* left click
* right click
* middle click

The clicks must be detected while the user is using:

* Chrome
* VS Code
* File Explorer
* Desktop
* other Windows applications

The tracker application itself does NOT need to be focused.

For example:

```text
Open Chrome
↓
Click 100 times
↓
Tracker records 100 clicks
```

Then:

```text
Open VS Code
↓
Click 50 times
↓
Tracker records another 50 clicks
```

This must be real functionality, not simulated data.

---

# STEP 4 — BUILD RELIABLE LOCAL STORAGE

The agent must continue counting even when:

* backend is down
* MongoDB is down
* internet is unavailable

Use local persistent storage for unsynchronized click data.

Never silently discard clicks.

---

# STEP 5 — BUILD BACKEND

Implement the Express backend according to `IMPLEMENTATION.md`.

Use:

* Node.js
* Express
* Mongoose
* MongoDB Atlas

Implement validation and proper error handling.

---

# STEP 6 — BUILD SAFE SYNCHRONIZATION

Do NOT send a request to the backend for every click.

Use:

```text
Mouse click
↓
Local counter
↓
Persistent local state
↓
Periodic batch
↓
Express
↓
MongoDB
```

If synchronization fails:

```text
Keep pending data
↓
Retry later
```

Prevent duplicate synchronization from double-counting clicks.

---

# STEP 7 — BUILD MONGODB

Implement:

* Mouse
* ClickSession
* DailyStatistic

Use appropriate indexes and atomic operations.

Verify that daily statistics are updated correctly.

---

# STEP 8 — BUILD REACT DASHBOARD

Build a professional dashboard.

It should show:

### Total

```text
150,420 clicks
```

### Button breakdown

```text
Left      110,200
Right      40,180
Middle          40
```

### Lifespan

```text
Rated:       3,000,000
Used:          150,420
Remaining:   2,849,580
Life Used:        5.01%
```

### Charts

* Daily clicks
* Weekly clicks
* Monthly clicks
* Click distribution

### Sessions

Show recent tracking sessions.

### Status

Show whether the tracker is active.

---

# STEP 9 — SYSTEM TRAY

Create a system-tray experience.

It should allow:

```text
Tracking status
Total clicks
Open dashboard
Pause
Resume
Exit
```

The tracker should normally run silently in the background.

---

# STEP 10 — WINDOWS STARTUP

Configure automatic startup.

Expected behavior:

```text
User starts Windows
↓
MouseLife Tracker starts
↓
Tracker runs in background
↓
User uses mouse normally
↓
Clicks are counted
```

The user should not need to manually launch a terminal or Python script every day.

---

# STEP 11 — TEST EVERYTHING

Do not assume the code works after generation.

Run the application.

Test:

### Real clicks

Click in multiple applications.

### Persistence

Restart the tracker.

Verify totals remain correct.

### Offline mode

Stop backend.

Generate clicks.

Verify they remain locally stored.

Restart backend.

Verify pending clicks synchronize.

### Duplicate synchronization

Repeat the same synchronization request.

Verify clicks are not double-counted.

### Dashboard

Verify dashboard values match MongoDB.

### Windows startup

Restart Windows and verify the tracker starts.

---

# STEP 12 — FIX PROBLEMS

If you encounter errors:

1. Diagnose the root cause.
2. Fix the implementation.
3. Re-run the affected test.
4. Continue only after verification.

Do not hide errors or simply mark a feature as complete.

---

# STEP 13 — PACKAGE THE APPLICATION

Create a practical Windows executable/package for the agent.

The final user experience should eventually be close to:

```text
Install MouseLife Tracker
↓
Start Windows
↓
Tracker automatically runs
↓
Use mouse normally
↓
Clicks automatically tracked
```

---

# STEP 14 — DOCUMENTATION

Update:

* README.md
* setup instructions
* MongoDB configuration
* environment variables
* development commands
* Windows startup setup
* packaging instructions
* troubleshooting
* architecture documentation
* API documentation

---

# IMPORTANT PRIVACY RULE

The tracker must ONLY monitor mouse button events required for click counting.

Never implement:

* keylogging
* screenshot capture
* clipboard monitoring
* browser history tracking
* URL collection
* password collection
* typed text collection
* application-content monitoring

---

# IMPORTANT PRODUCT LIMITATION

The tracker measures clicks from the point tracking begins.

It cannot determine clicks that occurred before tracking started unless the physical mouse exposes its own internal lifetime click counter.

The manufacturer's 3,000,000-click specification must be treated as a rated lifespan, not an exact guaranteed failure point.

---

# FINAL REQUIREMENT

Do not stop at creating source files.

The goal is a functioning application.

Before declaring completion, verify this complete flow:

```text
REAL MOUSE
    ↓
WINDOWS
    ↓
PYTHON GLOBAL CLICK AGENT
    ↓
LOCAL PERSISTENCE
    ↓
BATCH SYNCHRONIZATION
    ↓
EXPRESS API
    ↓
MONGODB ATLAS
    ↓
REACT DASHBOARD
```

The final application must actually count real mouse clicks and display accurate persistent statistics.
