#!/usr/bin/env bash
set -euo pipefail

REMOVE_APP=0
REMOVE_ALL_DATA=0
REMOVE_DEV_DATA=0
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: scripts/remove-all-required-for-installation-test.sh [options]

Removes local Codex Account Manager install/runtime state before manual installer tests.

Options:
  --remove-app       Remove /Applications/Codex Account Manager.app.
  --all-data         Also remove profiles, profile homes, backups, and ~/.codex/auth.json.
  --dev-data         Also remove Electron dev-shell userData/preferences.
  --dry-run          Print what would be removed without deleting anything.
  -h, --help         Show this help.

Default keeps account profiles and profile homes.
For a true zero-state packaged app test, use: --remove-app --all-data
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --remove-app) REMOVE_APP=1 ;;
    --all-data) REMOVE_ALL_DATA=1 ;;
    --dev-data) REMOVE_DEV_DATA=1 ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

echo "Removing Codex Account Manager local install/runtime state for installation testing..."
if [ "$DRY_RUN" -eq 1 ]; then
  echo "Dry run only; no files will be removed."
fi

HOME_DIR="${HOME}"
LOCAL_BIN="${HOME_DIR}/.local/bin"
LOCAL_PIPX="${HOME_DIR}/.local/pipx"
CODEX_DIR="${HOME_DIR}/.codex"
UI_SERVICE_DIR="${CODEX_DIR}/ui-service"
ACCOUNT_MANAGER_DIR="${CODEX_DIR}/account-manager"
ELECTRON_APP_SUPPORT="${HOME_DIR}/Library/Application Support/Codex Account Manager"
ELECTRON_DEV_APP_SUPPORT="${HOME_DIR}/Library/Application Support/Codex Account Manager Dev"
APP_BUNDLE="/Applications/Codex Account Manager.app"

remove_path() {
  local target="$1"
  if [ -e "$target" ] || [ -L "$target" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then
      echo "Would remove: $target"
    else
      rm -rf "$target"
      echo "Removed: $target"
    fi
  else
    echo "Not present: $target"
  fi
}

run_if_present() {
  local cmd="$1"
  shift
  if [ "$DRY_RUN" -eq 1 ]; then
    if command -v "$cmd" >/dev/null 2>&1; then
      echo "Would run: $cmd $*"
    else
      echo "Command not found, skipped: $cmd"
    fi
    return 0
  fi
  if command -v "$cmd" >/dev/null 2>&1; then
    "$cmd" "$@" >/dev/null 2>&1 || true
    echo "Ran: $cmd $*"
  else
    echo "Command not found, skipped: $cmd"
  fi
}

quit_packaged_app() {
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "Would quit packaged app and related Electron processes."
    return 0
  fi
  osascript -e 'tell application "Codex Account Manager" to quit' >/dev/null 2>&1 || true
  pkill -f "/Applications/Codex Account Manager.app/Contents/MacOS/" >/dev/null 2>&1 || true
  echo "Requested packaged app quit."
}

quit_packaged_app
run_if_present codex-account ui-service stop
run_if_present pipx uninstall codex-account-manager

remove_path "${LOCAL_BIN}/codex-account"
remove_path "${LOCAL_PIPX}/venvs/codex-account-manager"
remove_path "${LOCAL_PIPX}/shared"
remove_path "${LOCAL_PIPX}/logs"
remove_path "${UI_SERVICE_DIR}/service.json"
remove_path "${ACCOUNT_MANAGER_DIR}/runtime-state.json"
remove_path "${ELECTRON_APP_SUPPORT}"
remove_path "${HOME_DIR}/Library/Preferences/com.codexaccountmanager.desktop.plist"
remove_path "${HOME_DIR}/Library/Logs/com.codex.account.manager"
remove_path "${HOME_DIR}/Library/Saved Application State/com.codexaccountmanager.desktop.savedState"
remove_path "${HOME_DIR}/Library/Caches/com.codexaccountmanager.desktop"
remove_path "${HOME_DIR}/Library/HTTPStorages/com.codexaccountmanager.desktop"
remove_path "${HOME_DIR}/Library/HTTPStorages/com.codexaccountmanager.desktop.binarycookies"

if [ "$REMOVE_APP" -eq 1 ]; then
  remove_path "${APP_BUNDLE}"
else
  echo "Kept installed app bundle. Pass --remove-app to remove: ${APP_BUNDLE}"
fi

if [ "$REMOVE_DEV_DATA" -eq 1 ]; then
  remove_path "${ELECTRON_DEV_APP_SUPPORT}"
  remove_path "${HOME_DIR}/Library/Preferences/com.codexaccountmanager.desktop.dev.plist"
else
  echo "Kept Electron dev-shell data. Pass --dev-data to remove it."
fi

if [ "$REMOVE_ALL_DATA" -eq 1 ]; then
  remove_path "${CODEX_DIR}/account-profiles"
  remove_path "${CODEX_DIR}/profile-homes"
  remove_path "${CODEX_DIR}/account-backups"
  remove_path "${CODEX_DIR}/auth.json"
else
  echo
  echo "Kept intentionally:"
  echo "  ${CODEX_DIR}/account-profiles"
  echo "  ${CODEX_DIR}/profile-homes"
  echo "  ${CODEX_DIR}/account-backups"
  echo "  ${CODEX_DIR}/auth.json"
fi

echo
echo "Cleanup complete. The packaged app should use its bundled core on next launch."
