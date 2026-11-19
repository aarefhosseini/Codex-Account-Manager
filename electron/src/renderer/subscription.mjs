const dateFormatter = new Intl.DateTimeFormat("fa-IR-u-nu-latn");

export function formatSubscriptionDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value || "")) return "Not set";
  const date = new Date(`${value}T12:00:00`);
  return Number.isFinite(date.getTime()) ? dateFormatter.format(date) : "Not set";
}

export function subscriptionDisplay(subscription, billing) {
  if (billing?.status === "renewal_passed") {
    return { label: "Renewal date passed", status: "expired", needsAttention: true };
  }
  if (billing?.status === "payment_issue") {
    return { label: "Renewal date unavailable", status: "unknown" };
  }
  const timestamp = Date.parse(billing?.at);
  const remaining = timestamp - Date.now();
  if (remaining > 0 && ["renews", "ends"].includes(billing.status)) {
    const prefix = billing.status === "renews" ? "Renews" : "Ends";
    const days = Math.ceil(remaining / 86400000);
    return {
      label: `${prefix} ${dateFormatter.format(timestamp)}`,
      detail: `${days} ${days === 1 ? "day" : "days"} left`,
      title: new Date(timestamp).toLocaleString(),
      at: billing.at,
      status: "active",
      needsAttention: billing.status === "ends" && days <= 3,
    };
  }
  if (subscription?.expires_at) {
    return {
      label: `Estimated end ${formatSubscriptionDate(subscription.expires_at)}`,
      detail: subscription.status === "expired" ? "Estimated period ended" : `${subscription.days_remaining} days left`,
      at: subscription.expires_at,
      status: subscription.status,
      needsAttention: subscription.status === "expired"
        || (Number.isFinite(subscription.days_remaining) && subscription.days_remaining <= 3),
    };
  }
  return { label: "Billing date unavailable", status: "unknown" };
}

export function subscriptionSummary(subscription, billing) {
  const { label, detail } = subscriptionDisplay(subscription, billing);
  return detail ? `${label} · ${detail}` : label;
}
