const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");

const {
  buildPyInstallerArgs,
  coreExecutableName,
  verifyPythonCoreLayout,
} = require("../scripts/build-python-core");

test("buildPyInstallerArgs uses onedir output with private _internal support files", () => {
  const args = buildPyInstallerArgs({
    rootDir: "/repo/electron",
    projectRoot: "/repo",
    platform: "darwin",
  });

  assert.ok(args.includes("--onedir"));
  assert.ok(args.includes("--contents-directory"));
  assert.equal(args[args.indexOf("--contents-directory") + 1], "_internal");
  assert.ok(args.includes("--collect-data"));
  assert.ok(args.includes("codex_account_manager"));
  assert.equal(args.at(-1), path.join("/repo", "bin", "codex-account"));
});

test("coreExecutableName is platform-specific", () => {
  assert.equal(coreExecutableName("darwin"), "codex-account");
  assert.equal(coreExecutableName("linux"), "codex-account");
  assert.equal(coreExecutableName("win32"), "codex-account.exe");
});

test("verifyPythonCoreLayout rejects missing executable or _internal directory", () => {
  assert.throws(
    () => verifyPythonCoreLayout({
      coreDir: "/tmp/core",
      platform: "darwin",
      fsImpl: { existsSync: () => false },
    }),
    /missing frozen core executable/i,
  );

  assert.throws(
    () => verifyPythonCoreLayout({
      coreDir: "/tmp/core",
      platform: "darwin",
      fsImpl: {
        existsSync: (target) => target.endsWith("codex-account"),
        statSync: () => ({ isDirectory: () => false }),
      },
    }),
    /missing PyInstaller support directory/i,
  );
});
