import { describe, expect, it, vi } from "vitest";
import { render, screen } from "../test-utils";
import NotificationItem from "../../components/notifications/NotificationItem";
import type { NotificationRow } from "../../api/notifications";

function makeNotification(overrides: Partial<NotificationRow>): NotificationRow {
  return {
    id: 1,
    event_type: "TRADE_OPENED",
    payload: {},
    read: false,
    created_at: "2026-08-16T12:00:00Z",
    ...overrides,
  };
}

describe("NotificationItem", () => {
  it("renders a human sentence for TRADE_OPENED, not a raw key=value dump", () => {
    render(
      <NotificationItem
        notification={makeNotification({
          event_type: "TRADE_OPENED",
          payload: { trade_id: 1, user_id: null, symbol: "BTCUSDT", side: "LONG", entry: 60000 },
        })}
        onMarkRead={vi.fn()}
      />,
    );

    expect(screen.getByText("BTCUSDT LONG opened @ 60000")).toBeInTheDocument();
    expect(screen.queryByText(/trade_id=/)).not.toBeInTheDocument();
  });

  it("renders a human sentence for TRADE_CLOSED with a signed PnL", () => {
    render(
      <NotificationItem
        notification={makeNotification({
          event_type: "TRADE_CLOSED",
          payload: { trade_id: 1, symbol: "ETHUSDT", side: "SHORT", pnl: 12.5, close_reason: "TP" },
        })}
        onMarkRead={vi.fn()}
      />,
    );

    expect(screen.getByText("ETHUSDT SHORT closed, PnL +12.50 (TP)")).toBeInTheDocument();
  });

  it("renders a human sentence for SYSTEM_HEALTH_DEGRADED including the detail", () => {
    render(
      <NotificationItem
        notification={makeNotification({
          event_type: "SYSTEM_HEALTH_DEGRADED",
          payload: { component: "scanner", status: "degraded", detail: "timeout" },
        })}
        onMarkRead={vi.fn()}
      />,
    );

    expect(screen.getByText("scanner degraded — timeout")).toBeInTheDocument();
  });

  it("falls back gracefully for an unrecognized event type", () => {
    render(
      <NotificationItem
        notification={makeNotification({ event_type: "SOMETHING_NEW", payload: { foo: "bar" } })}
        onMarkRead={vi.fn()}
      />,
    );

    // Renders twice -- once as the label (no EVENT_LABEL_KEYS entry falls
    // back to the raw event_type) and once as the message body (no
    // messages.* entry falls back the same way) -- still no raw payload
    // key=value dump, which is the actual bug this guards against.
    expect(screen.getAllByText("SOMETHING_NEW")).toHaveLength(2);
    expect(screen.queryByText(/foo=/)).not.toBeInTheDocument();
  });
});
