import { useEffect, useRef } from "react";

export function useFocusTrap(active: boolean) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!active || !ref.current) return;

    const focusableSelectors = [
      "a[href]",
      "button:not([disabled])",
      "input:not([disabled])",
      "select:not([disabled])",
      "textarea:not([disabled])",
      '[tabindex]:not([tabindex="-1"])',
    ];

    const el = ref.current;
    const focusable = el.querySelectorAll<HTMLElement>(focusableSelectors.join(", "));
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    first?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };

    el.addEventListener("keydown", handleKeyDown);
    return () => el.removeEventListener("keydown", handleKeyDown);
  }, [active]);

  return ref;
}

export function useKeyboardShortcut(
  key: string,
  handler: () => void,
  options?: { ctrl?: boolean; meta?: boolean; alt?: boolean; shift?: boolean; enabled?: boolean },
) {
  useEffect(() => {
    if (options?.enabled === false) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (options?.ctrl && !e.ctrlKey) return;
      if (options?.meta && !e.metaKey) return;
      if (options?.alt && !e.altKey) return;
      if (options?.shift && !e.shiftKey) return;

      if (e.key.toLowerCase() === key.toLowerCase()) {
        e.preventDefault();
        handler();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [key, handler, options?.ctrl, options?.meta, options?.alt, options?.shift, options?.enabled]);
}

export function announceToScreenReader(message: string, priority: "polite" | "assertive" = "polite") {
  const id = "sr-announcement";
  let el = document.getElementById(id);
  if (!el) {
    el = document.createElement("div");
    el.id = id;
    el.setAttribute("role", "status");
    el.setAttribute("aria-live", priority);
    el.className = "sr-only";
    document.body.appendChild(el);
  }
  el.setAttribute("aria-live", priority);
  el.textContent = message;
}
