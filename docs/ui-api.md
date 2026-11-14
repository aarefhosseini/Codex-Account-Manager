# UI API

The local UI server is started by `codex-account ui` and serves HTTP on `127.0.0.1:4673` by default.

## Security Model

- GET endpoints are open on localhost service.
- POST endpoints require header: `X-Codex-Token: <session_token>`
- Token is generated per UI service startup and stored in UI state file.

## Response Envelope

Successful responses:

```json
{"ok": true, "data": {...}}
```

Error responses:

```json
{"ok": false, "error": {"code": "...", "message": "...", "details": {...}}}
```

## Core Endpoints

### Health and Status

- `GET /api/health`
- `GET /api/status`
- `GET /api/ping?token=<token>`

### UI and Runtime Config

- `GET /api/ui-config`
- `POST /api/ui-config`

### Profiles and Usage

- `GET /api/list`
- `GET /api/current`
- `GET /api/usage-local?timeout=7&force=false`

### Local Profile Actions

- `POST /api/local/save`
- `POST /api/local/add`
- `POST /api/local/add/start`
- `GET /api/local/add/session?id=<session_id>`
- `POST /api/local/add/cancel`
- `POST /api/local/switch` (also `/api/switch`)
- `POST /api/local/subscription`
- `POST /api/local/remove`
- `POST /api/local/remove-all`
- `POST /api/local/rename`
- `POST /api/local/run`

`/api/local/subscription` accepts `{ "name": "work", "purchased_at": "2026-10-25" }`.
Use `null` to clear the purchase date. It returns `subscription` with `purchased_at`,
`expires_at` (purchase + 30 days), `days_remaining`, and `status`. The same data is
included in profile list and usage rows. Purchase dates are user-entered local
estimates and are never inferred from `saved_at` or treated as billing confirmation.

`/api/local/switch` accepts `{ "name": "work", "no_restart": false, "continue_work": true }`.
The request completes after verified shutdown, atomic auth replacement, desktop
relaunch, and continuation delivery. Both flags shown above are the API defaults.
`continue_work: false` skips message delivery. `close_only: true` closes before
switching but does not relaunch. Explicit `no_restart: true` retains the CLI-style
auth-only operation. Allow up to 90 seconds for a full desktop switch. Failed
steps return actionable errors; errors after auth replacement state that the
account already changed. Do not retry an ambiguous continuation timeout blindly.

### Advanced Wrappers

- `GET /api/adv/status`
- `GET /api/adv/list?debug=1`
- `POST /api/adv/login`
- `POST /api/adv/switch`
- `POST /api/adv/remove`
- `POST /api/adv/import`
- `POST /api/adv/config`
- `POST /api/adv/daemon`
- `POST /api/adv/clean`
- `POST /api/adv/auth`

### Auto-Switch Runtime

- `GET /api/auto-switch/state`
- `GET /api/auto-switch/chain`
- `POST /api/auto-switch/enable`
- `POST /api/auto-switch/stop`
- `POST /api/auto-switch/run-once`
- `POST /api/auto-switch/run-switch`
- `POST /api/auto-switch/test`
- `POST /api/auto-switch/rapid-test`
- `POST /api/auto-switch/account-eligibility`
- `POST /api/auto-switch/chain`
- `POST /api/auto-switch/auto-arrange`

### Events and Logs

- `GET /api/events?since_id=<n>`
- `GET /api/debug/logs?tail=240`
- `GET /api/release-notes?force=true|false`

### Notifications

- `POST /api/notifications/test`
- `POST /api/notifications/native-test`

## UI Static Routes

- `GET /` or `/index.html`: embedded HTML app
- `GET /sw.js`: generated service worker script

## Server Runtime Notes

- Server implementation: `ThreadingHTTPServer`
- Auto-switch evaluation runs in dedicated background thread while server is alive.
- Idle shutdown (optional): controlled by `--idle-timeout` heartbeat watchdog.
- API caching: usage payload has short-lived in-memory cache keyed by config shape.
