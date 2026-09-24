# MouseLife Tracker — API Reference

Base URL: `http://localhost:5000/api`

---

## 1. System Health

### `GET /health`
Returns backend service and database connectivity status.

**Response (200 OK):**
```json
{
  "status": "ok",
  "service": "MouseLife Tracker API",
  "timestamp": "2026-09-24T09:04:14.764Z",
  "uptime": 26.08
}
```

---

## 2. Mouse Hardware Management

### `GET /mice`
Retrieves all registered mice.

### `GET /mice/:id`
Retrieves detailed information and lifespan metrics for a specific mouse.

**Parameters:**
- `id`: Mouse identifier (e.g. `portronics-default-01`)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "mouseId": "portronics-default-01",
    "name": "Portronics Wireless Mouse",
    "manufacturer": "Portronics",
    "model": "Toad 23 / Wireless Optical",
    "ratedClicks": 3000000,
    "totalClicks": 150420,
    "leftClicks": 110200,
    "rightClicks": 40180,
    "middleClicks": 40,
    "remainingClicks": 2849580,
    "lifeUsedPercentage": 5.01,
    "trackingStartedAt": "2026-09-24T08:58:47.664Z",
    "lastSyncedAt": "2026-09-24T09:07:03.678Z"
  }
}
```

### `PATCH /mice/:id`
Updates mouse configuration (e.g. rated clicks or model name).

**Request Body:**
```json
{
  "name": "Portronics Toad 23 Updated",
  "ratedClicks": 3000000
}
```

---

## 3. Click Synchronization

### `POST /clicks/sync`
Receives a batch of accumulated clicks from the Windows Agent. Fully protected against duplicate submissions.

**Request Body:**
```json
{
  "batchId": "79042444-693a-4123-8aa3-35026d28413d",
  "mouseId": "portronics-default-01",
  "clientSessionId": "40f19509-5ebc-42d0-aed5-ea79d31c174e",
  "leftClicks": 15,
  "rightClicks": 5,
  "middleClicks": 2,
  "totalClicks": 22,
  "timestamp": "2026-09-24T09:05:20.120Z"
}
```

**Response (200 OK - Processed):**
```json
{
  "success": true,
  "duplicate": false,
  "batchId": "79042444-693a-4123-8aa3-35026d28413d",
  "mouse": {
    "mouseId": "portronics-default-01",
    "totalClicks": 150420
  }
}
```

**Response (200 OK - Duplicate Acknowledged):**
```json
{
  "success": true,
  "duplicate": true,
  "message": "Batch already processed (idempotent acknowledgement)",
  "batchId": "79042444-693a-4123-8aa3-35026d28413d"
}
```

---

## 4. Analytics & Statistics

### `GET /mice/:id/statistics/daily?days=30`
Returns daily click counts for the specified period.

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "date": "2026-09-24",
      "leftClicks": 110200,
      "rightClicks": 40180,
      "middleClicks": 40,
      "totalClicks": 150420
    }
  ]
}
```

### `GET /mice/:id/statistics/weekly`
Returns click volume aggregated by calendar week.

### `GET /mice/:id/statistics/monthly`
Returns click volume aggregated by month.

---

## 5. Sessions

### `GET /mice/:id/sessions?limit=20`
Returns recent continuous tracking sessions.

### `POST /sessions/start`
Registers a new active session.

### `POST /sessions/end`
Finalizes an active session with calculated duration and clicks.
