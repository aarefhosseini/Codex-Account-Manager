"""Read-only banked reset balances for saved Codex accounts."""

import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPException
from pathlib import Path

try:
    from .subscriptions import _NoRedirect
except ImportError:
    from subscriptions import _NoRedirect


def parse_reset_balance(payload):
    if not isinstance(payload, dict):
        return None
    available = payload.get("available_count")
    if type(available) is not int or available < 0:
        return None
    earned = payload.get("total_earned_count")
    return {
        "available": available,
        "earned": earned if type(earned) is int and earned >= 0 else None,
    }


def _lookup(profile: Path):
    try:
        auth_path = profile / "auth.json"
        auth = auth_path.read_bytes()
        tokens = json.loads(auth)["tokens"]
        token, account_id = tokens["access_token"], tokens["account_id"]
        if not all(isinstance(value, str) and value for value in (token, account_id)):
            return None
        request = urllib.request.Request(
            "https://chatgpt.com/backend-api/wham/rate-limit-reset-credits",
            headers={"Authorization": f"Bearer {token}", "ChatGPT-Account-Id": account_id,
                     "Accept": "application/json", "User-Agent": "Mozilla/5.0 codex-account-manager"},
        )
        with urllib.request.build_opener(_NoRedirect).open(request, timeout=5) as response:
            raw = response.read(262145)
        if len(raw) > 262144 or auth_path.read_bytes() != auth:
            return None
        balance = parse_reset_balance(json.loads(raw))
        return {"name": profile.name, "account_id": account_id, **balance} if balance is not None else None
    except (OSError, HTTPException, ValueError, KeyError, TypeError):
        return None


def lookup_reset_balances(profiles: list[Path]) -> list[dict]:
    with ThreadPoolExecutor(max_workers=6) as pool:
        return [row for row in pool.map(_lookup, profiles) if row is not None]
