"""User-entered purchase dates; these are estimates, not billing API data."""

import datetime as dt


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
