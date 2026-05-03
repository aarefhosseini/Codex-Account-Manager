"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const projectRoot = path.resolve(root, "..");
const PYINSTALLER_TIMEOUT_MS = 10 * 60 * 1000;

function coreExecutableName(platform = process.platform) {
  return platform === "win32" ? "codex-account.exe" : "codex-account";
}

function dataArg(source, destination, platform = process.platform) {
  return `${source}${platform === "win32" ? ";" : ":"}${destination}`;
}

function buildPyInstallerArgs({
  rootDir = root,
  projectRoot: repoRoot = projectRoot,
  platform = process.platform,
} = {}) {
  const buildRoot = path.join(rootDir, "build", "python-core");
  return [
    "-m",
    "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onedir",
    "--name",
    "codex-account",
    "--distpath",
    path.join(buildRoot, "dist"),
    "--workpath",
    path.join(buildRoot, "work"),
    "--specpath",
    path.join(buildRoot, "spec"),
    "--contents-directory",
    "_internal",
    "--paths",
    repoRoot,
    "--collect-data",
    "codex_account_manager",
    "--add-data",
    dataArg(path.join(repoRoot, "codex_account_manager", "web"), path.join("codex_account_manager", "web"), platform),
    "--add-data",
    dataArg(path.join(repoRoot, "codex_account_manager", "assets"), path.join("codex_account_manager", "assets"), platform),
    path.join(repoRoot, "bin", "codex-account"),
  ];
}

function verifyPythonCoreLayout({ coreDir, platform = process.platform, fsImpl = fs } = {}) {
  const executable = path.join(coreDir, coreExecutableName(platform));
  if (!fsImpl.existsSync(executable)) {
    throw new Error(`missing frozen core executable: ${executable}`);
  }
  const internalDir = path.join(coreDir, "_internal");
  if (!fsImpl.existsSync(internalDir) || !fsImpl.statSync(internalDir).isDirectory()) {
    throw new Error(`missing PyInstaller support directory: ${internalDir}`);
  }
  return { coreDir, executable, internalDir };
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || root,
    env: options.env || process.env,
    encoding: "utf8",
    stdio: options.stdio || "pipe",
    timeout: options.timeoutMs || PYINSTALLER_TIMEOUT_MS,
  });
  if (result.status !== 0) {
    const output = [result.stdout, result.stderr, result.error?.message].filter(Boolean).join("\n").trim();
    throw new Error(`${command} ${args.join(" ")} failed${output ? `\n${output}` : ""}`);
  }
  return result;
}

function resolvePythonCommand(env = process.env) {
  return String(env.CAM_ELECTRON_PYTHON || env.PYTHON || "python3").trim();
}

function buildPythonCore({
  rootDir = root,
  repoRoot = projectRoot,
  platform = process.platform,
  env = process.env,
  fsImpl = fs,
  runImpl = run,
} = {}) {
  const buildRoot = path.join(rootDir, "build", "python-core");
  const distAppDir = path.join(buildRoot, "dist", "codex-account");
  const coreDir = path.join(buildRoot, "core");
  const python = resolvePythonCommand(env);

  fsImpl.rmSync(buildRoot, { recursive: true, force: true });
  fsImpl.mkdirSync(buildRoot, { recursive: true });

  try {
    runImpl(python, ["-m", "PyInstaller", "--version"], { cwd: repoRoot, env, timeoutMs: 30000 });
  } catch (error) {
    throw new Error(
      `PyInstaller is required to build the embedded Python core. Install it with: ${python} -m pip install -r electron/requirements-python-core.txt\n${error.message}`,
    );
  }

  runImpl(python, buildPyInstallerArgs({ rootDir, projectRoot: repoRoot, platform }), {
    cwd: repoRoot,
    env,
    stdio: "inherit",
  });

  fsImpl.renameSync(distAppDir, coreDir);
  const layout = verifyPythonCoreLayout({ coreDir, platform, fsImpl });
  runImpl(layout.executable, ["doctor", "--json"], { cwd: repoRoot, env, timeoutMs: 30000 });
  return layout;
}

if (require.main === module) {
  try {
    const layout = buildPythonCore();
    console.log(`Built embedded Python core: ${layout.executable}`);
  } catch (error) {
    console.error(error?.message || String(error));
    process.exit(1);
  }
}

module.exports = {
  buildPyInstallerArgs,
  buildPythonCore,
  coreExecutableName,
  dataArg,
  resolvePythonCommand,
  verifyPythonCoreLayout,
};
