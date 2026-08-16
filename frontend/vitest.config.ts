import { defineConfig, configDefaults } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: true,
    css: false,
    // e2e/**/*.spec.ts files use @playwright/test's own test()/expect(),
    // not vitest's -- without this, vitest's default *.spec.ts glob picks
    // them up too and fails trying to run them under the wrong runner.
    exclude: [...configDefaults.exclude, "e2e/**"],
  },
});
