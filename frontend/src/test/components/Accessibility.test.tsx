import { describe, expect, it } from "vitest";
import { renderHook } from "../test-utils";
import { useKeyboardShortcut } from "../../lib/accessibility";

describe("useKeyboardShortcut", () => {
  it("registers and fires handler", () => {
    let fired = false;
    renderHook(() =>
      useKeyboardShortcut("k", () => {
        fired = true;
      }),
    );
    const event = new KeyboardEvent("keydown", { key: "k" });
    window.dispatchEvent(event);
    expect(fired).toBe(true);
  });

  it("respects ctrl modifier", () => {
    let fired = false;
    renderHook(() =>
      useKeyboardShortcut("s", () => {
        fired = true;
      }, { ctrl: true }),
    );
    const event = new KeyboardEvent("keydown", { key: "s", ctrlKey: true });
    window.dispatchEvent(event);
    expect(fired).toBe(true);
  });

  it("does not fire when disabled", () => {
    let fired = false;
    renderHook(() =>
      useKeyboardShortcut("k", () => {
        fired = true;
      }, { enabled: false }),
    );
    const event = new KeyboardEvent("keydown", { key: "k" });
    window.dispatchEvent(event);
    expect(fired).toBe(false);
  });
});
