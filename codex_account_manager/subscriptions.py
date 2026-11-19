"""ChatGPT subscription lookup and local purchase-date estimates."""

import datetime as dt
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPException
from pathlib import Path


_ACCOUNT_CHECK_URL = "https://chatgpt.com/backend-api/accounts/check/v4-2023-04-27"
_MAX_RESPONSE_BYTES = 256 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _billing_timestamp(value) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        timestamp = dt.datetime.fromisoformat(value)
        if timestamp.tzinfo is not None:
            return timestamp.astimezone(dt.timezone.utc)
    except (ValueError, OverflowError):
        pass
    return None


def parse_billing_period(payload, account_id: str, now: dt.datetime | None = None) -> dict | None:
    """Read only the entitlement belonging to the selected account."""
    accounts = payload.get("accounts") if isinstance(payload, dict) else None
    record = accounts.get(account_id) if isinstance(accounts, dict) else None
    if not isinstance(record, dict):
        return None
    account = record.get("account")
    entitlement = record.get("entitlement")
    if not isinstance(account, dict) or account.get("account_id") != account_id:
        return None
    if not isinstance(entitlement, dict) or entitlement.get("subscription_plan") != "chatgptplusplan":
        return None
    now = now or dt.datetime.now(dt.timezone.utc)
    renews_at = _billing_timestamp(entitlement.get("renews_at"))
    if entitlement.get("is_delinquent") is True:
        if renews_at and renews_at <= now:
            return {"status": "renewal_passed"}
        return {"status": "payment_issue"}
    if entitlement.get("has_active_subscription") is not True or entitlement.get("is_delinquent") is not False:
        return None

    last_subscription = record.get("last_active_subscription")
    will_renew = last_subscription.get("will_renew") if isinstance(last_subscription, dict) else None
    if will_renew is False:
        ends_at = _billing_timestamp(entitlement.get("cancels_at"))
        if ends_at and ends_at > now:
            return {"status": "ends", "at": ends_at.isoformat()}
    if will_renew is True and "cancels_at" in entitlement and entitlement["cancels_at"] is None:
        if renews_at and renews_at > now:
            return {"status": "renews", "at": renews_at.isoformat()}
    return None


def _lookup_profile_billing(profile_dir: Path) -> dict | None:
    try:
        auth_path = profile_dir / "auth.json"
        saved_auth = auth_path.read_bytes()
        tokens = json.loads(saved_auth)["tokens"]
        access_token = tokens["access_token"]
        account_id = tokens["account_id"]
        if not all(isinstance(value, str) and value for value in (access_token, account_id)):
            return None
        request = urllib.request.Request(_ACCOUNT_CHECK_URL, headers={
            "Authorization": f"Bearer {access_token}",
            "ChatGPT-Account-Id": account_id,
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 codex-account-manager",
        })
        with urllib.request.build_opener(_NoRedirect).open(request, timeout=4) as response:
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
        if len(raw) > _MAX_RESPONSE_BYTES or auth_path.read_bytes() != saved_auth:
            return None
        billing = parse_billing_period(json.loads(raw), account_id)
        return {"name": profile_dir.name, "account_id": account_id, **billing} if billing else None
    except (OSError, HTTPException, ValueError, KeyError, TypeError):
        return None


def lookup_profile_billing(profile_dirs: list[Path]) -> list[dict]:
    with ThreadPoolExecutor(max_workers=6) as pool:
        return [row for row in pool.map(_lookup_profile_billing, profile_dirs) if row is not None]


def purchase_date(value) -> str | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValueError("Purchase date must use YYYY-MM-DD, or be empty to clear it.")
    try:
        parsed = dt.date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError
        parsed + dt.timedelta(days=30)
    except (ValueError, OverflowError):
        raise ValueError("Enter a valid purchase date in YYYY-MM-DD format.") from None
    return parsed.isoformat()


def subscription_info(value, today: dt.date | None = None) -> dict:
    try:
        purchased = purchase_date(value)
    except ValueError:
        purchased = None
    if not purchased:
        return {"purchased_at": None, "expires_at": None, "days_remaining": None, "status": "unknown"}
    end = dt.date.fromisoformat(purchased) + dt.timedelta(days=30)
    remaining = (end - (today or dt.date.today())).days
    return {"purchased_at": purchased, "expires_at": end.isoformat(),
            "days_remaining": max(0, remaining), "status": "expired" if remaining <= 0 else "active"}
