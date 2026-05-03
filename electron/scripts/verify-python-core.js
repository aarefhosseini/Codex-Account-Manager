"use strict";

const path = require("node:path");

const { verifyPythonCoreLayout } = require("./build-python-core");

const root = path.resolve(__dirname, "..");

try {
  const layout = verifyPythonCoreLayout({
    coreDir: path.join(root, "build", "python-core", "core"),
  });
  console.log(`Verified embedded Python core: ${layout.executable}`);
} catch (error) {
  console.error(error?.message || String(error));
  console.error("Run `npm run build:python-core` before packaging the Electron app.");
  process.exit(1);
}
