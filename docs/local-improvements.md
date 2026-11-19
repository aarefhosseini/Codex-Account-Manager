# Local improvements

This checkout adds purchase tracking, explicit action feedback, and verified desktop switching.

## Run this checkout

From `electron/`, run `npm ci`, then `npm run dev`. Python 3.11+ and a desktop-capable Electron runtime are required. The development launcher uses this checkout's Python backend. `npm run build` builds the renderer; it does not replace an installed application. Use `npm run dist:mac` for a packaged macOS build.

## Purchase dates

Open an account's row menu → **Purchase date / Plus period**, or open account details → **Edit purchase date**. Enter the actual purchase date. The Plus period column shows the purchase date, estimated end date, and remaining days. Dates are displayed in the Persian calendar; the stored value is an ISO calendar date. The end date is exactly 30 days after purchase.

Existing accounts remain **Purchase date not set** until edited. Adding an account does not establish its purchase date. This local estimate does not query OpenAI billing. Re-login, rename, and profile archive export/import preserve the metadata.

## Switching and continuation

The desktop Switch button now waits for one complete operation:

1. Find the desktop application and capture the current owner's last locally recorded chat interaction.
2. Check whether the previous chat can be resumed when **Continue unfinished work** is enabled.
3. Quit the application, wait for its process tree, and terminate surviving helpers if necessary. An inspection or shutdown failure stops the switch before credentials change.
4. Preserve the outgoing account's refreshed credentials, write a private backup, replace auth atomically, and verify the selected identity.
5. Reopen the desktop application with the previous local chat's [documented deep link](https://learn.chatgpt.com/docs/reference/commands#chats).
6. Use [`codex queue --resume`](https://learn.chatgpt.com/docs/developer-commands#codex-queue) to send one continuation message to that exact chat. It asks the agent to inspect current progress, continue unfinished work, and preserve existing approval requirements.

The bundled Codex CLI is checked before the system CLI. Missing chat history and older CLIs without `queue --resume` produce a separate warning after a successful switch. Turn off **Continue unfinished work** to switch and reopen without sending a message. This preference is saved locally. Opening the link or accepting the queued message does not prove a new model turn has finished; an unavailable daemon or failed resume is reported explicitly. An ambiguous delivery timeout is never retried automatically.

On macOS, discovery checks the `com.openai.codex` bundle identity, including installations named `ChatGPT.app`. The unrelated ChatGPT client and Codex Account Manager are not matched by name. For a custom installation, set `codex.app_path_macos`, `codex.app_path_windows`, or `codex.app_path_linux` in the project `config.json`.

If writing or verifying credentials fails, the previous auth state is restored and the target profile remains available to retry. If reopening fails after verification, the error states that the account already changed. The switch stays locked through relaunch and continuation delivery.

## Feedback and checks

Async buttons show a busy state and prevent repeated clicks. Success feedback is visible, errors remain until dismissed, and optional update/debug/chain failures do not prevent profile controls from loading. Missing quota data is shown as unavailable rather than 0% remaining.

Validation commands:

```sh
python3 -m unittest discover -s tests
cd electron
npm test
npm run build
```

`scripts/qa-renderer.py` tests the built renderer with Python Playwright and a fake preload bridge. It exercises purchase-date editing, switch feedback, duplicate prevention, optional-service failures, and error recovery. `tests/test_subscription_api.py` runs an isolated local backend with fake credentials and checks date persistence, validation, and POST authentication.

The real macOS application identity and process discovery were inspected read-only. No live account switch, application shutdown, or continuation message was sent during development. Those actions would close the active Codex session. Windows and Linux lifecycle handling have not been tested on those operating systems.
