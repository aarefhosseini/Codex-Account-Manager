"""Resume one exact local thread through the shared Codex daemon."""

import os
import subprocess
from pathlib import Path

try:
    from .desktop import THREAD_ID
except ImportError:
    from desktop import THREAD_ID

CONTINUE_MESSAGE = (
    "The account was switched by Codex Account Manager. Continue the unfinished work "
    "in this chat from where it stopped. First check the current files and any running "
    "operations so completed steps are not repeated. Preserve the user's existing scope "
    "and approval requirements. If the task is already complete, do not start new work."
)


def find_resume_cli(apps, fallback: str, home: Path, run=subprocess.run) -> str:
    candidates = []
    for app in apps:
        if app.bundle:
            resources = Path(app.bundle) / "Contents/Resources"
            candidates.extend([resources / "codex-cli/bin/codex", resources / "codex"])
    if fallback:
        candidates.append(Path(fallback))
    env = {**os.environ, "CODEX_HOME": str(home)}
    for candidate in dict.fromkeys(candidates):
        if not candidate.is_file():
            continue
        try:
            result = run([str(candidate), "queue", "--help"], capture_output=True, text=True, timeout=4, env=env)
            if result.returncode == 0 and "--resume" in result.stdout:
                return str(candidate)
        except (OSError, subprocess.TimeoutExpired):
            continue
    raise RuntimeError("Automatic continuation requires a Codex CLI with 'queue --resume'. Update Codex or turn off Continue unfinished work, then retry. Account was not changed.")


def continue_thread(cli_path: str, thread_id: str, home: Path, run=subprocess.run) -> None:
    if not THREAD_ID.fullmatch(thread_id):
        raise RuntimeError("Cannot continue: invalid local chat ID.")
    try:
        result = run([cli_path, "queue", "--thread", thread_id, "--message", CONTINUE_MESSAGE, "--resume"],
                     capture_output=True, text=True, timeout=15,
                     env={**os.environ, "CODEX_HOME": str(home)})
    except subprocess.TimeoutExpired:
        # Delivery might have succeeded. Never retry a possibly delivered message.
        raise RuntimeError("Continuation delivery timed out and its result is unknown. Check the previous chat before sending another message.") from None
    if result.returncode:
        raise RuntimeError("Could not queue the continuation message. Open the previous chat and continue it, or check the Codex local daemon.")
    if "could not resume" in (result.stderr or "").lower():
        raise RuntimeError("The continuation message was queued, but Codex could not resume the chat. Open the previous chat; do not send the message again.")
    if "queued message" not in (result.stdout or "").lower():
        raise RuntimeError("Codex did not confirm continuation delivery. Check the previous chat before retrying.")
