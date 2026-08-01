import { describe, expect, it } from "vitest";
import { renderHook } from "../test-utils";
import { ThemeProvider, useTheme } from "../../components/theme/ThemeProvider";

describe("ThemeProvider", () => {
  it("provides default theme values", () => {
    const { result } = renderHook(() => useTheme(), {
      wrapper: ({ children }) => <ThemeProvider>{children}</ThemeProvider>,
    });
    expect(result.current.mode).toBe("dark");
    expect(result.current.contrast).toBe("normal");
    expect(result.current.density).toBe("compact");
    expect(typeof result.current.reducedMotion).toBe("boolean");
  });
});
