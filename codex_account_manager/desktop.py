"""Desktop lifecycle only. Never launch the CLI as a desktop fallback."""

import json
import os
import plistlib
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DesktopApp:
    executable: str
    bundle: str = ""


def discover_macos_apps(configured: Path | None = None) -> list[DesktopApp]:
    candidates = [configured] if configured else []
    for root in (Path("/Applications"), Path.home() / "Applications"):
        candidates.extend(root / name for name in ("Codex.app", "ChatGPT.app"))
    apps = []
    for candidate in candidates:
        if not candidate:
            continue
        bundle = candidate
        if bundle.suffix != ".app":
            bundle = next((p for p in candidate.parents if p.suffix == ".app"), candidate)
        try:
            info = plistlib.loads((bundle / "Contents/Info.plist").read_bytes())
            # The old ChatGPT chat client has a different bundle identifier.
            if info.get("CFBundleIdentifier") != "com.openai.codex":
                continue
            executable = bundle / "Contents/MacOS" / info["CFBundleExecutable"]
            if executable.is_file():
                app = DesktopApp(str(executable), str(bundle))
                if app not in apps:
                    apps.append(app)
        except (OSError, ValueError, KeyError, plistlib.InvalidFileException):
            continue
    return apps


def process_snapshot(run=subprocess.run, platform=None) -> list[dict]:
    try:
        return _read_process_snapshot(run, platform)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError) as error:
        raise RuntimeError("Cannot inspect Codex processes. Check system permissions and retry; account was not changed.") from error


def _read_process_snapshot(run, platform=None) -> list[dict]:
    platform = platform or sys.platform
    if platform.startswith("win"):
        result = run([
            "powershell", "-NoProfile", "-Command",
            "$ErrorActionPreference='Stop'; Get-CimInstance Win32_Process | "
            "Select-Object ProcessId,ParentProcessId,ExecutablePath | ConvertTo-Json -Compress",
        ], capture_output=True, text=True, timeout=5)
        if result.returncode:
            raise RuntimeError("Cannot inspect Codex processes. Check PowerShell permissions and retry.")
        rows = json.loads(result.stdout or "[]")
        if isinstance(rows, dict):
            rows = [rows]
        return [{"pid": int(r["ProcessId"]), "ppid": int(r["ParentProcessId"]),
                 "executable": r.get("ExecutablePath") or ""} for r in rows]
    result = run(["ps", "-axo", "pid=,ppid=,comm="], capture_output=True, text=True, timeout=5)
    if result.returncode:
        raise RuntimeError("Cannot inspect Codex processes. Check system permissions and retry.")
    rows = []
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            rows.append({"pid": int(parts[0]), "ppid": int(parts[1]), "executable": parts[2]})
    return rows


def desktop_processes(rows: list[dict], apps: list[DesktopApp], platform=None) -> list[dict]:
    platform = platform or sys.platform
    def matches(row):
        executable = row["executable"]
        key = executable.lower() if platform.startswith("win") else executable
        for app in apps:
            target = app.executable.lower() if platform.startswith("win") else app.executable
            if key == target or (app.bundle and executable.startswith(app.bundle + "/Contents/")):
                return True
        return False
    selected = {r["pid"] for r in rows if matches(r)}
    while True:
        children = {r["pid"] for r in rows if r["ppid"] in selected}
        if children <= selected:
            break
        selected |= children
    return [r for r in rows if r["pid"] in selected and r["pid"] != os.getpid()]


def discover_apps(configured: Path | None = None, run=subprocess.run, platform=None) -> list[DesktopApp]:
    platform = platform or sys.platform
    if platform == "darwin":
        return discover_macos_apps(configured)
    if configured and configured.is_file():
        return [DesktopApp(str(configured.resolve()))]
    if platform.startswith("win"):
        apps = []
        for row in process_snapshot(run, platform):
            path = row["executable"]
            normalized = path.replace("\\", "/").lower()
            # Exclude the npm CLI, bundled app-server, and Account Manager itself.
            if normalized.endswith("/codex.exe") and not any(
                part in normalized for part in ("/resources/", "/node_modules/", "/vendor/", "/bin/")
            ):
                apps.append(DesktopApp(path))
        if not apps:
            result = run(["powershell", "-NoProfile", "-Command",
                          "$ErrorActionPreference='Stop'; Get-AppxPackage '*Codex*' | "
                          "Select-Object -ExpandProperty InstallLocation"],
                         capture_output=True, text=True, timeout=5)
            for line in (result.stdout or "").splitlines():
                for relative in ("app/Codex.exe", "Codex.exe"):
                    candidate = Path(line.strip()) / relative
                    if candidate.is_file():
                        apps.append(DesktopApp(str(candidate)))
        return list(dict.fromkeys(apps))
    for candidate in (Path("/opt/Codex/codex"), Path("/opt/codex/codex"), Path("/usr/share/codex/codex")):
        if candidate.is_file():
            return [DesktopApp(str(candidate))]
    return []


def stop_apps(apps: list[DesktopApp], run=subprocess.run, platform=None) -> None:
    platform = platform or sys.platform
    remaining = desktop_processes(process_snapshot(run, platform), apps, platform)
    tracked = {row["pid"] for row in remaining}
    if not remaining:
        return
    if platform == "darwin":
        for app in apps:
            if app.bundle:
                script = f'tell application (POSIX file {json.dumps(app.bundle)} as alias) to quit'
                try:
                    run(["osascript", "-e", script], capture_output=True, text=True, timeout=4)
                except subprocess.TimeoutExpired:
                    pass
    elif platform.startswith("win"):
        pids = ",".join(str(pid) for pid in tracked)
        run(["powershell", "-NoProfile", "-Command",
             f"Get-Process -Id {pids} -ErrorAction SilentlyContinue | ForEach-Object {{ [void]$_.CloseMainWindow() }}"],
            capture_output=True, text=True, timeout=4)
    else:
        for row in remaining:
            try:
                os.kill(row["pid"], signal.SIGTERM)
            except ProcessLookupError:
                pass
    def alive():
        rows = process_snapshot(run, platform)
        selected = desktop_processes(rows, apps, platform)
        tracked.update(row["pid"] for row in selected)
        # Include children reparented when their main window exited.
        return [row for row in rows if row["pid"] in tracked]
    for _ in range(30):
        if not alive():
            return
        time.sleep(0.2)
    for row in alive():
        try:
            if platform.startswith("win"):
                run(["taskkill", "/F", "/T", "/PID", str(row["pid"])],
                    capture_output=True, text=True, timeout=4)
            else:
                os.kill(row["pid"], signal.SIGKILL)
        except ProcessLookupError:
            pass
    for _ in range(15):
        if not alive():
            return
        time.sleep(0.2)
    raise RuntimeError("Codex is still running. Close its windows and background processes, then retry. Account was not changed.")


def start_app(app: DesktopApp, run=subprocess.run, resume_url="", platform=None) -> None:
    platform = platform or sys.platform
    if platform == "darwin":
        command = ["open", "-a", app.bundle]
        if resume_url:
            command.append(resume_url)
        result = run(command, capture_output=True, text=True, timeout=5)
        if result.returncode:
            raise RuntimeError("Codex could not be reopened. Open the desktop app manually.")
    else:
        subprocess.Popen([app.executable, *([resume_url] if resume_url else [])],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         **({"creationflags": getattr(subprocess, "DETACHED_PROCESS", 0)}
                            if platform.startswith("win") else {"start_new_session": True}))
    for _ in range(50):
        rows = process_snapshot(run, platform)
        if any(r["executable"].lower() == app.executable.lower() for r in rows):
            return
        time.sleep(0.2)
    raise RuntimeError("Codex launch was requested, but its process did not appear. Open the desktop app manually.")


THREAD_ID = re.compile(r"(?:local:)?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", re.I)


def local_thread_id(value) -> str:
    text = str(value or "")
    # Current desktop builds key activity by JSON-encoded [host, threadId].
    if text.startswith("["):
        try:
            identity = json.loads(text)
            if not isinstance(identity, list) or len(identity) != 2 or identity[0] != "local":
                return ""
            text = str(identity[1])
        except ValueError:
            return ""
    match = THREAD_ID.fullmatch(text)
    return match[1] if match else ""


def last_thread_url(home: Path) -> str:
    """Best effort, read-only: use the current owner's last user interaction."""
    try:
        state = json.loads((home / ".codex-global-state.json").read_text(encoding="utf-8"))
        owner = state.get("electron-renderer-content-owner")
        atoms = state.get(f"electron-owner-atoms:{owner}", {}) if owner else state.get("electron-persisted-atom-state", {})
        for key in ("selected-thread-id", "last-active-thread-id"):
            value = atoms.get(key) or state.get(key)
            thread_id = local_thread_id(value)
            if thread_id:
                return f"codex://threads/{thread_id}"
        activity = atoms.get("thread-user-activity-times-v1", {})
        candidates = [(float(stamp), local_thread_id(key)) for key, stamp in activity.items()
                      if isinstance(stamp, (int, float)) and local_thread_id(key)]
        if candidates:
            return f"codex://threads/{max(candidates, key=lambda item: item[0])[1]}"
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return ""
