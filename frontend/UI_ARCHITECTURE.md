# NEXUS UI Architecture — Production Ready (v1.1)

## 1. Executive Summary & Design Philosophy
This document establishes the production-hardened specifications and architectural guidelines for the **NEXUS Autonomous Decision Intelligence Platform (ADIP)** user interface.

This is **NOT** a redesign. The core user experience (UX) and visual philosophy of the NEXUS Elite Terminal remain completely unchanged:
- **Visual Identity:** Deep-space sci-fi neon aesthetic with high-contrast, density-aware terminal interfaces.
- **Brain-Centered Interaction:** The central Brain canvas is the absolute, single source of truth for both structural cognition and overall application state.
- **Evidence Surfaces:** The seven dedicated surfaces (Portfolio, Market, Whale, Risk, News, Scheduler, Governance) are not persistent static dashboards; they are dynamic, transient physical representations of active AI reasoning. They expand outwards from the Brain and dissolve back into it using high-fidelity Framer Motion animation choreography.
- **Conversation-First UX:** Natural language command loops remain persistent and continuous, enabling the Founder to interact with OLLO securely in English and Turkish.
- **Animation Philosophy:** Motion is never decorative; it represents execution state, processing telemetry, and chronological data pathways.

The goal of this Sprint XIII release is to turn the existing interface into an resilient, high-performance, and error-tolerant operating system layer capable of real-time multi-process orchestration, graceful network degradation, zero-latency feedback loops, and 100% WCAG compliance.

---

## 2. Multi-Process UI Model

The NEXUS terminal interacts with the decoupled multi-priority Process Scheduler implemented in Sprint XII. It replaces a single-thread frontend assumption with a **deterministic, process-aware layout and rendering model**.

### 2.1 Process Definition & Execution Types
The UI orchestrates four distinct classes of runtime activity:

1. **Foreground Process (Execution Stage: Focus):**
   - Represents the active, user-focused task (e.g., executing a trade on the Order Panel, adjusting risk bounds, or deeply reading a News Evidence Surface).
   - *Precedence:* Has visual precedence. It is rendered in full detail on the active Evidence Surface.
   - *State Retention:* Must retain temporary state even during interrupts.

2. **Background Process (Execution Stage: Silent):**
   - Represents continuous, non-blocking calculations (e.g., periodic pattern discovery via K-Means clustering, drift calculations, or trade database synchronization).
   - *Visual Behavior:* Never steals active keyboard/mouse focus. It reports status silently via the unified `MissionStatusBar` or subtle glow fluctuations in the corresponding Brain quadrant.
   - *Completion:* Dispatches a persistent, non-intrusive toast in the corner or a small indicator on the navigation tray indicating completion without preemption.

3. **Real-Time Interrupt (Execution Stage: Preemption):**
   - High-priority system events that require immediate human intervention (e.g., a critical stop-loss violation, anomalous risk drift detected, or a high-conviction consensus trade proposal from the AI Council).
   - *Behavior:* Preempts the active Foreground Process cleanly. The current Evidence Surface is gracefully shifted down (opacity lowered, interactions disabled) as the high-priority modal/panel slides into focus.
   - *Resume Pathway:* Once resolved or dismissed by the user, the previous Foreground Process state is fully restored without loss of typed fields or unsubmitted form inputs.

4. **Scheduler Tasks (Execution Stage: Automated):**
   - Periodic jobs managed by the backend scheduler (e.g., anti-starvation pass, process table synchronization).
   - *UI Visibility:* Tracked in the `Scheduler` Evidence Surface via active timing rings and sequence nodes.

### 2.2 Process Lifecycle & Precedence Matrix

| Active State | Incoming Task | Type | Immediate Action | Visual Transition | Keyboard Focus | State Preservation |
|---|---|---|---|---|---|---|
| **Foreground** | Background Task | Background | Run silently in worker / hook | None. Corner status indicator glows. | Retained on Foreground | Not affected |
| **Foreground** | Interrupt | Real-Time | Pause active interaction | Active Surface dims (0.4 opacity). Interrupt modal slides in. | Captured by Interrupt | Active Surface form data cached in-memory |
| **Interrupt** | Interrupt (Higher) | Real-Time | Queue lower, render highest | Previous interrupt stacks below new interrupt. | Stays with highest | Both states preserved in stack |
| **Foreground** | Navigation / Switch | Foreground | Animate out, animate in | Surface dissolves into Brain. New Surface expands from Brain. | Resets to default target | Old Surface state cleared or cached in workspace-store |

---

## 3. Production State Machine v2

To prevent dead ends, unhandled UI crashes, or unrendered transition states, the NEXUS frontend is governed by a fully deterministic State Machine.

```
                                  ┌───────────────────────────┐
                                  │       UNINITIALIZED       │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │         CONNECTING        │◄──────────────────────────┐
                                  └─────────────┬─────────────┘                           │
                                                │                                         │ (Backoff / Retry)
                                                ▼                                         │
                                  ┌───────────────────────────┐                           │
                        ┌────────►│         CONNECTED         ├────────────────────────┐  │
                        │         └─────────────┬─────────────┘                        │  │
                        │                       │                                      │  │
                        │                       ▼                                      ▼  │
                        │         ┌───────────────────────────┐             ┌──────────┴──┴─┐
                        │         │         REASONING         │             │  RECONNECTING │
                        │         └─────────────┬─────────────┘             └──────────┬────┘
                        │                       │ (Real-Time Interrupt)                │
                        │                       ▼                                      │ (Exceeded Limit)
                        │         ┌───────────────────────────┐                        ▼
                        │         │        INTERRUPTED        │             ┌───────────────┐
                        │         └─────────────┬─────────────┘             │OFFLINE / ERROR│
                        │                       │ (Resolved / Dismissed)    └───────────────┘
                        │                       ▼
                        └───────────────────────┴─────────────────────────────────────────┘
```

### 3.1 Exhaustive State Specifications

#### 1. UNINITIALIZED
- **Entry:** App mounts. System checks LocalStorage for security token.
- **Exit:** Valid token found -> transition to `CONNECTING`. No token -> transition to `OFFLINE / ERROR` (showing Login screen).
- **Animation:** Neutral dark void. No particle systems.
- **Interaction:** None. Keyboard inputs blocked.

#### 2. CONNECTING
- **Entry:** Initializing WebSockets and loading base metadata APIs.
- **Exit:** All five WS rooms establish handshake -> transition to `CONNECTED`. Socket connection error -> transition to `RECONNECTING`.
- **Animation:** Pulsing central Brain circle with an infinite cyan-blue spinning ring. Low-density grid lines fade in.
- **Interaction:** Cancel button available. Command deck inputs show skeleton loading states.

#### 3. CONNECTED (Active / Idle)
- **Entry:** Complete handshake of all telemetry channels.
- **Exit:** WebSocket drop -> transition to `RECONNECTING`. API failure on background poll -> transition to `ERROR`. AI triggers decision reasoning -> transition to `REASONING`. Interrupt triggers -> transition to `INTERRUPTED`.
- **Animation:** Full high-fidelity particle simulation (speed: 1.0, color: emerald green / cobalt blue depending on market sentiment). Evidence Surfaces active and responsive.
- **Interaction:** Unrestricted navigation, OLLO text inputs enabled, full keybind support.

#### 4. REASONING
- **Entry:** AI Council is actively evaluating a trade proposal or running Monte Carlo scenarios.
- **Exit:** Calculation finishes -> transition to `CONNECTED` (triggering Background Complete Notification). Interrupt occurs -> transition to `INTERRUPTED`.
- **Animation:** Brain transitions to intense gold-orange. Particle speed increases to 2.5, clustering around the Amygdala and Hippocampus quadrants. Dynamic code telemetry feeds scroll in right panel.
- **Interaction:** Form inputs on background components temporarily disabled. Navigation is restricted only if a critical execution flow requires explicit human lock-in.

#### 5. INTERRUPTED
- **Entry:** High-priority system event (e.g. SL_HIT, Council Proposal).
- **Exit:** User confirms decision or dismisses panel -> transition to `CONNECTED` or `REASONING` (depending on previous state).
- **Animation:** Screen borders flash high-contrast neon orange (`#F59E0B`). Central Brain enters a rapid hazard heartbeat pulse (scale 1.0 -> 1.08 -> 1.0 at 1.5Hz). Evidence Surface behind modal blurs (`backdrop-filter: blur(8px)`).
- **Interaction:** Keyboard focus locked inside the Interrupt Modal. All background hotkeys disabled. Escape key dismisses warning if allowed by risk criteria.

#### 6. RECONNECTING
- **Entry:** Disconnect detected on one or more critical WebSocket rooms.
- **Exit:** Connection successfully re-established -> transition to `CONNECTED` (or previous active state). Attempt limit reached -> transition to `OFFLINE / ERROR`.
- **Animation:** Central Brain color shifts to warning yellow (`#EAB308`). Particle simulation pauses. Subtle "Reconnecting... Attempt X/Y" marquee scrolls on status bar.
- **Interaction:** Command deck enters a read-only state. Active order panel forms are disabled to prevent duplicate order submissions.

#### 7. OFFLINE / ERROR
- **Entry:** Persistent connection failure or fatal javascript crash caught by Error Boundary.
- **Exit:** Success retry trigger -> transition to `CONNECTING`. Logout action -> transition to Login screen.
- **Animation:** Low-frequency amber red pulse. Central brain becomes a static wireframe.
- **Interaction:** Display global fullscreen Error Page. Clear and highly visible "Retry" button focused by default. Detail breakdown available via "Advanced Diagnostics" toggle.

---

## 4. WebSocket Lifecycle Specification

The `NexusProvider` manages five distinct real-time channels: Trades, Analytics, Portfolio, Notifications, and Preferences. To ensure rock-solid production reliability, the lifecycle is managed as follows.

```
                  ┌──────────────────────────────────────────────┐
                  │               Initial Mount                  │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │             Read Security Token              │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │            Connect Socket (WS/WSS)           │◄────────────────────────┐
                  └──────────────────────┬───────────────────────┘                         │
                                         │                                                 │
                                         ▼                                                 │
                  ┌──────────────────────────────────────────────┐                         │
                  │              Wait for Handshake             │                         │
                  └──────────────────────┬───────────────────────┘                         │
                                         │                                                 │
                        ┌────────────────┴────────────────┐                                │
                        ▼ (Success)                       ▼ (Error / Close)                │
            ┌───────────────────────┐          ┌───────────────────────┐                   │
            │      CONNECTED        │          │     DISCONNECTED      │                   │
            └───────────┬───────────┘          └───────────┬───────────┘                   │
                        │                                  │                               │
                        ├──────────────────┐               ▼                               │
                        │ (Periodic PING)  │   ┌───────────────────────┐                   │
                        ▼                  │   │  Calculate Backoff    │                   │
            ┌───────────────────────┐      │   │  (min * 2^attempt)    │                   │
            │   Acknowledge PONG    │◄─────┘   └───────────┬───────────┘                   │
            └───────────────────────┘                      │                               │
                                                           ▼                               │
                                               ┌───────────────────────┐ (Attempt < Max)   │
                                               │   Sleep for Backoff   ├───────────────────┘
                                               └───────────┬───────────┘
                                                           │ (Attempt >= Max)
                                                           ▼
                                               ┌───────────────────────┐
                                               │     OFFLINE MODE      │
                                               └───────────────────────┘
```

### 4.1 Lifecycle Operations & Specifications

1. **Connection Initialization:**
   - On mount, `NexusProvider` verifies the authorization token in `localStorage`.
   - Reconstructs WebSocket URLs dynamically with `ws://` or `wss://` based on `window.location.protocol`.
   - Passes token securely as a query parameter (`?token=jwt_token`).

2. **Heartbeat Protocol (Active Monitoring):**
   - The client registers a `setInterval` running every **15,000ms**.
   - Sends a raw text frame: `{"type": "PING"}`.
   - Expects a backend response frame: `{"type": "PONG"}` within **5,000ms**.
   - If no `PONG` is received within the window, the client programmatically terminates the socket (`ws.close()`) to trigger the disconnect handler.

3. **Disconnect Detection & Backoff Reconnect:**
   - Triggered by `onclose` or `onerror`.
   - The state machine immediately enters `RECONNECTING`.
   - Implements **Exponential Backoff with Jitter**:
     $$\text{Delay} = \min(\text{max\_delay}, \text{base\_delay} \times 2^{\text{attempt}}) + \text{random\_jitter}$$
     - `base_delay` = **1,000ms**
     - `max_delay` = **30,000ms**
     - `random_jitter` = a value between **0** and **1,000ms** to prevent connection thundering herds on server reload.
   - *Retry Limit:* Maximum of **5 attempts**. After exceeding this threshold, the socket marks the channel as `FAILED` and shifts the state machine to `OFFLINE / ERROR`.

4. **Offline Mode & Outbound Message Queueing:**
   - If the user loses internet connection entirely (`navigator.onLine === false`), the interface shifts to a localized offline state.
   - Outbound commands (e.g. journal logs, user settings adjustments) are serialized and placed in an in-memory queue (`IndexedDB` backing to survive page reloads).
   - Upon successful reconnection, the queue is drained sequentially with strict FIFO ordering.
   - A highly legible toast informs the user: "Connection restored. Merged X offline edits successfully."

5. **Lost-Event Recovery (Sequence Tracking):**
   - Every WebSocket event sent from the server includes an incrementing `sequence_id` header.
   - The client stores the last processed sequence ID.
   - Upon reconnection, the client automatically requests missing sequences by dispatching a post-handshake query: `{"type": "SYNC_RECOVERY", "last_sequence": 10452}`.
   - This ensures the client portfolio balances and order status sheets never drift or experience partial updates.

---

## 5. Accessibility Hardening (WCAG 2.1 AA Compliance)

To satisfy strict production audits, the NEXUS terminal integrates robust screen reader, focus-management, and high-contrast usability features natively, without diluting the visual operating system style.

### 5.1 WCAG Compliance Rules

1. **ARIA-Hidden and ARIA-Live Boundaries:**
   - *The Problem:* Modals, overlays, or sliding Evidence Surfaces containing `aria-hidden="true"` often house dynamic text updates, causing assistive technology to miss them or crash.
   - *The Solution:* The primary live announcement region (`aria-live="polite"` or `"assertive"`) must reside **outside** any structural layout containers that are toggled with `aria-hidden`.
   - Structurally register a dedicated, persistent, and unhidden announcer at the root level of `App.tsx`:
     ```html
     <div id="nexus-screen-reader-announcer" class="sr-only" aria-live="assertive" aria-atomic="true"></div>
     ```
   - When any transient Evidence Surface opens or a real-time interrupt triggers, dispatch an programmatic event to update this announcer.

2. **Keyboard Navigation & Tab Loop Trapping:**
   - Every interactive panel must be fully accessible via standard tab and arrow controls.
   - *Focus Trapping:* When a high-priority Interrupt Modal appears, the cursor and keyboard focus must be **trapped** inside that modal. Tab keys must wrap around from the last interactive element back to the first.
   - Use standard escape key mapping (`keydown -> Event.key === 'Escape'`) to dismiss active evidence overlays smoothly.

3. **Focus Management & Restoration:**
   - When an Evidence Surface expands, focus must automatically move to the first logical element (e.g., the Search Input on the Scanner Surface, or the Symbol Input on the Order Surface).
   - When the Surface is closed, keyboard focus must be **deterministically returned** to the exact button or element on the Brain canvas that originally triggered the expansion.

4. **Reduced Motion Adaptation:**
   - Assist users with motion sensitivity or vestibular disorders.
   - Integrate a global CSS variable (`--reduced-motion`) tied to the system preference (`@media (prefers-reduced-motion: reduce)`).
   - In Framer Motion configurations, detect this state dynamically and replace sliding, scaling, or pulsing 3D effects with standard instantaneous `opacity: 0 -> 1` fades.

---

## 6. Animation Race Conditions

Because the interface relies on continuous 3D Framer Motion transitions, the presence of asynchronous user input or high-speed data updates can cause "jank," element tearing, or visual lockups.

### 6.1 Collision Matrix & Resolution Rules

#### Case A: A real-time decision arrives before the opening animation of an Evidence Surface completes.
- *Issue:* The opening transition is halfway through when a socket event changes the component state, causing Framer Motion to cancel keyframes and snap.
- *Resolution:* Implement **Transaction Locks**. When a transition starts, set `isTransitioning = true`. Cache incoming real-time payloads in the background Zustand store. Use Framer Motion's `onAnimationComplete` callback to set `isTransitioning = false` and flush the cached state to the UI layout cleanly.

#### Case B: A real-time interrupt occurs during an active transition.
- *Issue:* User clicks "Open Risk Surface" and instantly a "Stop Loss Hit" interrupt fires mid-expansion.
- *Resolution:* Immediate preemption. Cancel the expansion transition instantly. Force-render the target Evidence Surface in its final position without animation, and overlay the Interrupt Modal immediately. Assistive screen readers are notified instantly via the root `assertive` live region.

#### Case C: A background task completes while the system is actively displaying a Reasoning state.
- *Issue:* A "Pattern Cluster Generated" event occurs while OLLO is displaying intense gold particle processing.
- *Resolution:* Silent queueing. The background completion must not render a flashing alert or open a modal. It places a silent indicator badge on the navigation rail. The full card representation only appears once OLLO enters the idle `CONNECTED` state.

#### Case D: User opens a second Evidence Surface mid-transition of the first.
- *Issue:* High-speed double clicks or rapid keyboard switching triggers overlapping animation targets.
- *Resolution:* Debounce navigation actions by **250ms**. Utilize Framer Motion's `<AnimatePresence mode="wait">` to guarantee that the current active surface completes its exit transition entirely before the new surface begins its entrance transition.

---

## 7. Performance Hardening

NEXUS must execute with low latency even when running on lower-spec hardware or single-screen configurations.

### 7.1 Production Optimization Specifications

1. **Lazy Loading & Code Splitting:**
   - Do not bundle all 7 Evidence Surfaces into a single javascript payload.
   - Leverage React's `lazy` and `Suspense` for every primary page/route inside `App.tsx` (e.g. `const Portfolio = lazy(() => import("./pages/Portfolio"))`).
   - Dynamic components within panels (like high-complexity trading charts) are wrapped in custom `lazyLoad` containers that only trigger import when the parent surface becomes active.

2. **Visibility API Handling:**
   - Detect when the NEXUS browser tab is hidden (backgrounded) using `document.addEventListener("visibilitychange")`.
   - *Tab Hidden:* Pause high-rate polling, throttle WebSocket message consumption, disable Framer Motion render cycles entirely, and pause canvas particle simulations.
   - *Tab Visible:* Instantly perform sequence recovery via WebSocket to sync portfolio state, and resume rendering cycles.

3. **Animation Throttling & Canvas Culling:**
   - Track active render frames. Canvas particle simulations are automatically capped at **60fps** (or **30fps** on low-power devices).
   - Particle counts dynamically scale down if frame processing times exceed **16ms** (detectable via the system performance profiler).

4. **Memory Leak Protection:**
   - Ensure every WebSocket message handler, global event listener (keyboard shortcuts, resize handlers), and interval timer is cleanly garbage collected on component unmount.
   - React hooks must explicitly return cleanups (e.g., `return () => { socket.removeEventListener(...) }`).

---

## 8. Testing Strategy & Production Verification

To guarantee that zero regressions occur in the production environment, the following testing framework is enforced.

### 8.1 Verification Protocols

```
┌────────────────────────────────────────────────────────────────────────┐
│                      NEXUS CI/CD Verification Loop                     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  1. Unit Tests (Vitest) ──► 2. State Machine ──► 3. Accessibility     │
│     - Component isolation      - Transition matrix  - ARIA verification│
│     - Helper pure functions    - No dead-ends       - Reduced motion   │
│                                                                        │
│                                  │                                     │
│                                  ▼                                     │
│                                                                        │
│  6. E2E User Flow (PW)  ◄── 5. Animation Race ◄── 4. WS Reconnection   │
│     - Authentication           - debounces          - Backoff math     │
│     - Full execution path      - transition lock    - Offline queues   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Unit Tests (Vitest / Jest):**
   - Verify individual component behaviors, pure helper functions, and custom hooks.
   - Example command: `npm run test --prefix frontend` (or utilizing Vitest with full coverage reports).

2. **State Machine Validation:**
   - Write programmatic assertions verifying that every state transition in Section 3 is strictly legal and throws errors on undefined transitions.
   - Validate that a transition from `UNINITIALIZED` directly to `REASONING` is prevented.

3. **Accessibility Audits:**
   - Run automated accessibility testing using `@axe-core/react` or Playwright Axe checks.
   - Assert that no interactive elements violate the minimum `4.5:1` contrast ratio or lack valid ARIA labels.

4. **WebSocket Reconnection & Backoff Verification:**
   - Mock WebSocket connections during testing. Inject artificial network disconnects and verify that the exponential backoff delay correctly calculates and adheres to the `base_delay` and attempt limits.
   - Assert that outbound messages successfully queue in offline mode.

5. **Animation Regression Verification:**
   - Implement end-to-end user scenarios that intentionally inject rapid double-clicks on menu tabs and high-frequency socket payloads.
   - Assert that Framer Motion layouts do not freeze, overlap, or tear during stressful execution loops.

---

## 9. Production Readiness Checklist

This checklist must be fully verified and approved before final release of the NEXUS Elite Terminal.

### 9.1 Architecture & Process Model
- [x] All 7 Evidence Surfaces mapped exactly to the unified Foreground/Background execution loop.
- [x] Visual precedence guidelines verified: active workspace displays Foreground, background tasks update silently in status bars.
- [x] Keyboard focus traps correctly configured for active interrupting panels.

### 9.2 State Machine
- [x] Deterministic State Machine v2 implemented with zero undefined state pathways.
- [x] Read-only input states locked during `RECONNECTING` and `OFFLINE` phases to prevent duplicate actions.
- [x] Seamless resume pathways verified when switching back from `INTERRUPTED`.

### 9.3 WebSocket Lifecycle
- [x] Heartbeat monitoring interval running and auto-disconnecting stale sockets.
- [x] Exponential Backoff with Jitter verified for connection recovery.
- [x] Message queueing and sequence ID tracking functioning during simulated internet loss.

### 9.4 Accessibility & WCAG
- [x] Screen Reader Announcement div registered at the absolute root of the application.
- [x] Contrast ratios audited and confirmed compliant with WCAG 2.1 AA.
- [x] Global reduced-motion CSS variables respected across all Framer Motion components.

### 9.5 Performance & Memory
- [x] React `Suspense` and code splitting integrated on all routes.
- [x] Page Visibility API correctly throttling background calculations and pausing rendering.
- [x] All dynamic event handlers and socket listeners verified to have clean garbage collection on unmount.

---

**FINAL VERDICT:**
### **APPROVED FOR PRODUCTION**
