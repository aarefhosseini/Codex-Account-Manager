import React from "react";
import { profileIsReady, profileNeedsAttention } from "../profile-filters.mjs";
import ProgressBar from "./ProgressBar.jsx";

export default function ProfilesOverview({ profiles, onOpenDetails }) {
  const active = profiles.find((row) => row.is_current);
  const ready = profiles.filter(profileIsReady).length;
  const attention = profiles.filter(profileNeedsAttention).length;
  return (
    <section className="profiles-overview" aria-label="Account overview">
      <div className="active-account-summary">
        <div className="overview-eyebrow"><span className="status-dot active" /> Active account</div>
        {active ? <>
          <button className="active-account-name" onClick={() => onOpenDetails(active)} title="Open active account details">{active.name}</button>
          <p className="active-account-email" title={active.email_display}>{active.email_display}</p>
        </> : <><strong>No account selected</strong><p className="active-account-email">Add an account to get started.</p></>}
      </div>
      <div className="overview-usage" aria-label="Active account quota">
        <div><span>5-hour remaining</span><ProgressBar value={active?.error ? null : active?.usage_5h?.remaining_percent} /></div>
        <div><span>Weekly remaining</span><ProgressBar value={active?.error ? null : active?.usage_weekly?.remaining_percent} /></div>
      </div>
      <dl className="overview-counts">
        <div><dt>Saved</dt><dd>{profiles.length}</dd></div>
        <div><dt>Quota available</dt><dd>{ready}</dd></div>
        <div className={attention ? "needs-attention" : ""}><dt>Needs attention</dt><dd>{attention}</dd></div>
      </dl>
    </section>
  );
}
