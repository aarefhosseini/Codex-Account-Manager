// Browser-only fixture. Never reads or switches real credentials.
(() => {
  const clone = (value) => JSON.parse(JSON.stringify(value));
  const rows = ["work", "backup"].map((name, index) => ({
    name, email: `${name}@example.test`, account_id: `${name}-test`,
    account_hint: `${name}@example.test`, saved_at: "2026-11-01T10:00:00",
    is_current: index === 0, plan_type: "plus", is_paid: true, error: null,
    usage_5h: { remaining_percent: index ? 85 : 35, resets_at: 1794710000 },
    usage_weekly: { remaining_percent: index ? 90 : 45, resets_at: 1794900000 },
    subscription: { purchased_at: null, expires_at: null, days_remaining: null, status: "unknown" },
  }));
  const state = {
    current: { profile_name: "work", account_hint: "work@example.test" },
    list: { profiles: clone(rows) }, usage: { current_profile: "work", profiles: clone(rows) },
    config: { ui: { theme: "dark", current_auto_refresh_enabled: false, all_auto_refresh_enabled: false }, auto_switch: { enabled: false } },
    autoSwitch: {},
  };
  window.fixture = { state, switchCalls: [], failSwitch: false, failOptional: false };
  const runtime = { phase: "ready", python: { supported: true }, core: { installed: true }, uiService: { running: true } };
  const desktop = {
    platform: "darwin", shell: "electron",
    getRuntimeStatus: async () => runtime,
    getState: async () => clone(state),
    getBackendState: async () => ({ baseUrl: "http://127.0.0.1:4673", version: "test" }),
    getUpdateStatus: async () => {
      if (window.fixture.failOptional) throw new Error("Release server unavailable");
      return { current_version: "0.0.21", update_available: false };
    },
    refresh: async () => clone(state),
    switchProfile: async (name, options) => {
      window.fixture.switchCalls.push({ name, options });
      await new Promise((resolve) => setTimeout(resolve, 500));
      if (window.fixture.failSwitch) throw new Error("Codex is still running. Close its windows and retry. Account was not changed.");
      state.current.profile_name = name;
      state.usage.current_profile = name;
      [state.list, state.usage].forEach((source) => source.profiles.forEach((row) => { row.is_current = row.name === name; }));
      return clone(state);
    },
    request: async (path, options = {}) => {
      const route = path.split("?")[0];
      if (route === "/api/ui-config" && options.method === "POST") {
        const patch = JSON.parse(options.body);
        state.config = { ...state.config, ...patch, ui: { ...state.config.ui, ...patch.ui } };
        return clone(state.config);
      }
      if (route === "/api/local/subscription") {
        const body = JSON.parse(options.body);
        const end = body.purchased_at ? new Date(`${body.purchased_at}T12:00:00Z`) : null;
        if (end) end.setUTCDate(end.getUTCDate() + 30);
        const subscription = { purchased_at: body.purchased_at, expires_at: end?.toISOString().slice(0, 10) || null, days_remaining: 10, status: end ? "active" : "unknown" };
        [state.list, state.usage].forEach((source) => source.profiles.forEach((row) => { if (row.name === body.name) row.subscription = subscription; }));
        return { name: body.name, subscription };
      }
      if (route.startsWith("/api/usage-local")) return clone(state.usage);
      if (route === "/api/list") return clone(state.list);
      if (route === "/api/current") return clone(state.current);
      if (route === "/api/auto-switch/state") return {};
      if (route === "/api/auto-switch/chain") {
        if (window.fixture.failOptional) throw new Error("Usage service unavailable");
        return { chain: ["work", "backup"], items: [] };
      }
      if (route === "/api/debug/logs") return { logs: [] };
      if (route === "/api/release-notes") return {};
      return {};
    },
    openExternal: async () => {},
    testNotification: async () => ({ ok: true }),
  };
  ["onNavigate", "onToggleSidebar", "onCycleView", "onRefreshRequested", "onRuntimeStatus", "onRuntimeProgress", "onUpdateProgress", "onAutoSwitchStopped", "onAutoSwitchPending"].forEach((name) => { desktop[name] = () => () => {}; });
  window.codexAccountDesktop = desktop;
})();
