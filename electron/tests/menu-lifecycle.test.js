const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const { buildApplicationMenuTemplate, shouldQuitOnWindowAllClosed } = require("../src/menu");

test("buildApplicationMenuTemplate includes desktop app menus and shortcuts", () => {
  const labels = buildApplicationMenuTemplate({
    isMac: true,
    isDev: true,
    actions: {},
  }).map((item) => item.label || item.role);

  assert.deepEqual(labels, ["Codex Account Manager", "File", "Edit", "View", "Go", "Window", "Help"]);
});

test("application menu exposes refresh settings notification and sidebar actions", () => {
  const template = buildApplicationMenuTemplate({ isMac: false, isDev: false, actions: {} });
  const allLabels = template.flatMap((item) => (item.submenu || []).map((entry) => entry.label || entry.role));

  assert.ok(allLabels.includes("Refresh Table"));
  assert.ok(allLabels.includes("Profiles"));
  assert.ok(allLabels.includes("Auto Switch"));
  assert.ok(allLabels.includes("Settings"));
  assert.ok(allLabels.includes("Test Notification"));
  assert.ok(allLabels.includes("Toggle Sidebar"));
  assert.ok(allLabels.includes("Next Section"));
  assert.ok(allLabels.includes("Quit + Stop Core"));
});

test("shouldQuitOnWindowAllClosed keeps tray app alive until explicit quit", () => {
  assert.equal(shouldQuitOnWindowAllClosed({ hasTray: true, isQuitting: false }), false);
  assert.equal(shouldQuitOnWindowAllClosed({ hasTray: false, isQuitting: false }), true);
  assert.equal(shouldQuitOnWindowAllClosed({ hasTray: true, isQuitting: true }), true);
});

test("bootstrap creates the tray before waiting for runtime startup", () => {
  const mainSource = fs.readFileSync(path.join(__dirname, "../src/main.js"), "utf8");
  const bootstrapStart = mainSource.indexOf("async function bootstrap()");
  assert.notEqual(bootstrapStart, -1);

  const bootstrapSource = mainSource.slice(bootstrapStart, mainSource.indexOf("app.whenReady()", bootstrapStart));
  const createWindowIndex = bootstrapSource.indexOf("createMainWindow();");
  const syncTrayIndex = bootstrapSource.indexOf("syncDesktopTray(");
  const checkRuntimeIndex = bootstrapSource.indexOf("await checkRuntime({ activateBackend: true });");

  assert.notEqual(createWindowIndex, -1);
  assert.notEqual(syncTrayIndex, -1);
  assert.notEqual(checkRuntimeIndex, -1);
  assert.ok(createWindowIndex < syncTrayIndex);
  assert.ok(syncTrayIndex < checkRuntimeIndex);
});
