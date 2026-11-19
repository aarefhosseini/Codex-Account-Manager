# Release Notes

This file tracks user-visible changes by version.

## Unreleased

## 0.1.3

- Fixed a race that could cancel an account switch before Codex returned the sign-in verification result.

## 0.1.2

- Recover from a failed sign-in by restoring the previous state and keeping saved profiles available for another attempt.
- Switch from a signed-out Codex session even when there is no chat to resume. Report continuation issues separately after a successful switch.
- Show available Plus renewal or scheduled end dates in the desktop app, with a manual 30-day estimate when billing data is unavailable.
- Open the desktop app in a smaller window with readable account rows and a visible Switch button. Show more details in wider windows and account cards in narrow ones.
- Fit refresh rules, notifications, and switch controls into compact layouts. Keep reference topics expandable and give log messages more room on narrow screens.

## 0.1.0

- Check that Codex and its helpers exit before replacing account credentials. Back up and verify the active credentials, reopen Codex, and queue a continuation message when enabled.
- Recognize macOS installations named ChatGPT.app using the Codex bundle identity.
- Record the Plus purchase date and show the estimated end date and remaining days for a 30-day period.
- Search and filter accounts, see the active account at a glance, and use a card layout in narrow windows. Improve keyboard navigation and dialog focus.
- Prevent duplicate actions, keep failures visible, and show unavailable quota without treating it as zero.
- Package the desktop app with the Python core for Apple Silicon and Windows x64.

## 0.0.21

### Auto-Switch Notification Control

- Added a stop control in the desktop auto-switch notification flow so users can halt a pending switch from the warning surface.
- Added focused pending-switch dialog behavior with explicit actions to continue switching or stop the flow.
- Updated notification click handling to focus the desktop app and route into the in-app confirmation flow.

### Settings and Test Flow

- Moved the notification test action to Settings under `Notifications`.
- Renamed the action to `Test auto switch notif` and aligned its styling with standard settings actions.
- Wired the test path through the real auto-switch pending-notification behavior so stop/continue flow can be validated end-to-end.

## 0.0.12

### Update Flow Fixes

- Fixed the web-panel update flow so the dialog can be closed while an update continues in the background.
- Added a progress bar, step text, and short updater output inside the update dialog.
- Fixed post-update reload timing so the panel waits for the UI service to actually cycle before reloading into the new build.

## 0.0.11

### Profiles, Alarms, and Update Flow

- Replaced the old Export / Import settings card with a full-width `Profiles` panel that uses dedicated `Import` and `Export` actions.
- Added a richer export dialog with profile checkboxes, `Select All` / `Unselect All`, and optional custom archive naming before downloading a `.camzip` migration archive.
- Added 20 built-in alarm presets, a dedicated alarm picker dialog, per-preset preview buttons, and an inline `Test Alarm` action for warning sound checks.
- Moved the app version next to the `Codex Account Manager` title and added in-app update availability checks with a release-notes review dialog before running `pipx upgrade codex-account-manager`.

### Guidance, Tooltips, and Stability

- Refreshed in-app `Guide & Help` content so it matches the current Profiles, Alarm, and Update experiences.
- Expanded tooltip coverage on newer controls and modal actions so every visible section has clearer inline guidance.
- Fixed a boot-breaking inline JavaScript escape issue in the new update flow that could prevent the accounts table from loading after restart.
- Improved loading behavior so the accounts table can show placeholder rows sooner while slow usage refresh requests complete.

## 0.0.10

### UI and Workflow Refresh

- Merged Add Account into a single dialog that captures the profile name, explains login modes, and keeps device-login URL/code actions in one place.
- Split panel refresh behavior into `Current Account Auto Refresh` and `Auto Refresh All`, with the all-accounts path sweeping accounts one by one instead of batch-refreshing everything every tick.
- Added a toolbar `Restart` action in the panel, kept `Refresh` as the manual full-sync action, and refined button color semantics for refresh/restart/remove flows in both dark and light themes.
- Improved in-panel spacing and density for refresh controls, alarm thresholds, and switch thresholds to better use available card space.

### Table, Row Actions, and Guidance

- Added broader tooltip coverage across panel controls, account actions, headers, and dialogs to explain visible UI behavior without opening docs.
- Updated destructive row actions and account-toolbar destructive buttons to render with clearer red warning semantics.
- Improved light-theme status-dot visibility and inactive-dot styling for the `STS` column.
- Refreshed in-app `Guide & Help` content so it matches the current controls, refresh model, login flow, and auth-handling behavior.

### Current Account and Auth Reliability

- Fixed current-account detection so the active Codex account is resolved correctly even when live tokens rotate and the saved profile snapshot is not byte-identical.
- Fixed current-row usage fetching to read from the live active auth session instead of a stale saved profile snapshot.
- Added automatic sync from the live active auth back into the matching saved profile snapshot after a healthy current-account usage refresh, reducing stale-token drift for future refreshes.
- Replaced misleading `0% / unknown` failure states for broken auth rows with clearer auth-error signaling such as `auth expired`.

## 0.0.8

### UI and Workflow Improvements

- Improved light-theme toggle switch colors for better visibility/contrast.
- Replaced the header Debug button icon with a clearer terminal-style glyph.
- Increased the header Settings button size for better click/tap usability.
- Increased inner size of Debug/Settings header icons while keeping equal button container sizes.
- Improved manual `Refresh` button responsiveness so a single click triggers immediate visible refresh state.
- Updated `Kill All` confirmation modal to use a red confirm action for clearer destructive intent.
- Scoped `Kill All` shutdown to Codex Account Manager processes only (no Codex desktop/app shutdown side effects).
- Reworked switch-row feedback so the entire row blinks slowly while a switch is in progress.
- Added a post-switch drag/drop-style animation that moves the newly selected current row to the top after refresh completes.

### Accounts and Metadata

- Added `plan_type` and `is_paid` fields to `usage-local --json` profile rows.
- Added `Plan` and `Paid` columns in the Accounts table.
- Kept `Plan` and `Paid` hidden by default in column preferences (users can enable from `Columns`).

### Auto-Switch and Selection Fixes

- Fixed auto-arrange chain ranking so exhausted accounts are pushed to the end instead of appearing as next preferred switch targets.
- Fixed candidate selection to skip accounts with `0%` remaining quota when auto-switch chooses the next account.
- Fixed balanced-mode chain generation so stale manual-chain ordering no longer leaks into auto-arranged previews.
- Fixed red switch-state rendering so accounts with `0%` on either `5H` or `Weekly` show the blocked visual state consistently.

### macOS Switch Reliability

- Restored the macOS switch flow to close and relaunch Codex instead of using the close-only path.
- Improved macOS app relaunch reliability by preserving the detected app target and retrying launch when the app is still shutting down.

### Guide and Help

- Rewrote in-app `Guide & Help` content to reflect current visible panel controls and workflows.
- Added in-app release-notes sync from GitHub Releases with local fallback to this file.
- Added manual in-guide release-note refresh and status states (`Synced`, `Fallback`, `Failed`).

### Stability and Platform Improvements

- Improved Windows-focused reliability in current iteration (login/service and runtime behavior hardening).
- Continued general UI reliability and diagnostics improvements in active development.

## 0.0.7

- Packaged baseline cross-platform CLI + local web UI release.
- Core profile management (`save`, `add`, `list`, `switch`, `remove`).
- Live usage monitoring and local UI service controls.
- Auto-switch controls and local event/diagnostics surfaces.
