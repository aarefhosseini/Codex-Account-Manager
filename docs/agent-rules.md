# AI Agent Rules & Change Memory

## Project Snapshot
- Keep updates focused on architecture, behavior rules, and high-impact changes only.
- Prefer short, implementation-focused bullets over narrative prose.

## Behavior Rules
- Use `rtk` as the prefix for shell commands in this repository.
- Use jCodeMunch MCP tools for code exploration when they can answer the question.
- Preserve private owner-specific workflow files; do not require them for public repository build, test, or usage.
- Before release completion claims, run fresh verification and report the actual command results.
- Ensure we had script to deleted pre needed things first check it this wokr for current state or not i want to clean every thing and test install app from 0.

## Recent Changes (Last 20)
### 2026-05-03T18:50:05+03:30
- Changed files: `electron/src/renderer/App.jsx`
- Summary: Removed renderer toast notifications by dropping ToastProvider/useToast wiring and the error toast side-effect; keep bottom error snackbar as the single in-app alert surface.
- Behavior impact: Recorded code-level deltas for future AI context.
<!-- fingerprint:3784a91e29a9 -->

### 2026-05-03T18:37:39+03:30
- Changed files: `electron/src/tray.js`, `electron/tests/desktop.test.js`, `electron/tests/identity.test.js`
- Summary: Removed the visible macOS Electron status-bar tray icon by using an empty native image while keeping usage data in the menu bar title, and kept tray asset assertions aligned with the current helper path.
- Behavior impact: Recorded code-level deltas for future AI context.
<!-- fingerprint:67697c2cf2be -->

### 2026-05-02T20:24:53+03:30
- Changed files: `electron/src/main.js`, `electron/tests/menu-lifecycle.test.js`, `electron/tests/runtime.test.js`
- Summary: Fix macOS status bar startup race by creating the Electron tray before runtime/backend startup, and isolate bundled-core runtime test from dev env overrides.
- Behavior impact: Recorded code-level deltas for future AI context.
<!-- fingerprint:c85c27a19f94 -->

### 2026-05-02T20:12:45+03:30
- Changed files: `scripts/remove-all-required-for-installation-test.sh`, `scripts/remove-all-required-for-installation-test.ps1`
- Summary: Updated installation-test cleanup scripts for bundled-core packaged app testing with dry-run, app removal, all-data, and dev-data modes.
- Behavior impact: Added or refreshed 1 behavior rule(s) from user instructions.
<!-- fingerprint:206439ec5e05 -->

### 2026-05-02T20:01:34+03:30
- Changed files: `codex_account_manager/cli.py`, `electron/package.json`, `electron/scripts/build-python-core.js`, `electron/scripts/verify-python-core.js`, `electron/requirements-python-core.txt`, `electron/src/main.js`, `electron/src/renderer/App.jsx`, `electron/src/runtime.js`, +5 more
- Summary: Embed a PyInstaller-built app-private Python core into Electron packaging, prefer bundled runtime in packaged apps, and stop production pipx core sync paths.
- Behavior impact: Recorded code-level deltas for future AI context.
<!-- fingerprint:1087f2d3a70a -->

## Last Updated
- 2026-05-03T18:50:05+03:30
