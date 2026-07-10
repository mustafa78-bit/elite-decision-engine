import { describe, expect, it } from "vitest";
import { renderHook } from "../test-utils";
import { useWidgetRegistry } from "../../components/dashboard/widget-registry";

describe("WidgetRegistry", () => {
  it("returns all widgets", () => {
    const { result } = renderHook(() => useWidgetRegistry());
    const all = result.current.getAllWidgets();
    expect(all.length).toBeGreaterThan(40);
    expect(all[0]).toHaveProperty("id");
    expect(all[0]).toHaveProperty("name");
    expect(all[0]).toHaveProperty("category");
  });

  it("finds widget by id", () => {
    const { result } = renderHook(() => useWidgetRegistry());
    const widget = result.current.getWidget("kpi");
    expect(widget).not.toBeNull();
    expect(widget?.name).toBe("KPI Strip");
  });

  it("returns null for unknown id", () => {
    const { result } = renderHook(() => useWidgetRegistry());
    expect(result.current.getWidget("nonexistent")).toBeNull();
  });

  it("filters by category", () => {
    const { result } = renderHook(() => useWidgetRegistry());
    const riskWidgets = result.current.getWidgetsByCategory("risk");
    expect(riskWidgets.length).toBeGreaterThan(5);
    riskWidgets.forEach((w) => expect(w.category).toBe("risk"));
  });

  it("searches widgets by name", () => {
    const { result } = renderHook(() => useWidgetRegistry());
    const results = result.current.searchWidgets("chart");
    expect(results.length).toBeGreaterThan(0);
    results.forEach((w) => {
      const match =
        w.name.toLowerCase().includes("chart") ||
        w.description.toLowerCase().includes("chart") ||
        w.category.toLowerCase().includes("chart");
      expect(match).toBe(true);
    });
  });
});
