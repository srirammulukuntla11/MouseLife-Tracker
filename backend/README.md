# MouseLife Tracker — Backend Service

Express and MongoDB persistence service for MouseLife Tracker.

## Responsibilities
- Receives idempotent click batch synchronization requests (`POST /api/clicks/sync`).
- Atomically updates mouse totals and daily statistics.
- Manages tracking sessions and aggregates daily/weekly/monthly statistics.
- Serves REST APIs for the React dashboard.

## Running
```powershell
npm install
npm run dev
```

## Testing
```powershell
npm test
```
