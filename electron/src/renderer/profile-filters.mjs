function remainingQuota(usage) {
  const value = usage?.remaining_percent;
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export function profileNeedsAttention(profile) {
  return Boolean(profile.error)
    || profile.subscription?.status === "expired"
    || (Number.isFinite(profile.subscription?.days_remaining) && profile.subscription.days_remaining <= 3)
    || [profile.usage_5h, profile.usage_weekly].map(remainingQuota).some((value) => value !== null && value <= 0);
}

export function profileIsReady(profile) {
  if (profile.error) return false;
  return [profile.usage_5h, profile.usage_weekly].map(remainingQuota).every((value) => value !== null && value > 0);
}

export function filterProfiles(profiles, query = "", filter = "all") {
  const term = String(query).trim().toLocaleLowerCase();
  return profiles.filter((profile) => {
    if (filter === "ready" && !profileIsReady(profile)) return false;
    if (filter === "attention" && !profileNeedsAttention(profile)) return false;
    return !term || [profile.name, profile.email_display, profile.email, profile.account_id]
      .some((value) => String(value || "").toLocaleLowerCase().includes(term));
  });
}
