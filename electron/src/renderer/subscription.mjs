export function formatSubscriptionDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value || "")) return "Not set";
  const date = new Date(`${value}T12:00:00`);
  return Number.isFinite(date.getTime()) ? date.toLocaleDateString("fa-IR") : "Not set";
}

export function subscriptionSummary(subscription) {
  if (!subscription?.expires_at) return "Purchase date not set";
  const end = formatSubscriptionDate(subscription.expires_at);
  return subscription.status === "expired"
    ? `${end} · Period ended`
    : `${end} · ${subscription.days_remaining} days left`;
}
