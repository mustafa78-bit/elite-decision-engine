# Sprint: Crystal AI Brain Hero (Command Deck transformation)

## Product context — read this before touching code

NEXUS's design direction is locked (decided after many iterations, do not redesign the layout, only implement/refine it):

- NOT a crypto dashboard. NOT a Bloomberg/TradingView clone. It's a **living AI Operating System**.
- Hero visual: a **large crystal AI brain** — a living digital organism that continuously breathes, pulses, evolves, illuminates different internal regions, and broadcasts intelligence. It must never look static.
- Around/behind it: living holographic energy ripples (NOT water — they must read as holographic intelligence radiating from the AI core) that expand, fade, regenerate, merge, and softly interfere with each other.
- Aesthetic: dark cinematic environment, premium glassmorphism, Apple Vision Pro-level material quality, Iron Man/JARVIS atmosphere, enterprise luxury, minimal UI — information supports the brain, never competes with it.
- Motion: everything moves slowly and breathes. No busy/distracting animation. Cinematic, premium easing only.
- Micro-details where they fit naturally: crystal refraction, glass reflections, volumetric lighting, holographic dust/floating particles, subtle bloom, chromatic dispersion, soft vignette. Elegant, never exaggerated.
- **A reference video for the exact brain look is included in this branch at `docs/design/crystal_brain_reference.mp4`.** Watch it before implementing — it is the definitive visual target ("kesin olan" = the confirmed/final one), takes priority over your own interpretation of the written brief above if the two ever conflict. Implement the hero using CSS/SVG/Canvas (gradients, blur, blend modes, animated particles) to match what's shown in that video — you don't need to embed the video itself in the app, it's a design reference only.

## Current state (verified by reading the actual code, not docs)

- App's landing route is `/command-deck` → `frontend/src/pages/CommandDeck.tsx` (`App.tsx` redirects `/` there).
- `CommandDeck.tsx` currently renders `OLLOCommander` (`frontend/src/components/hq/OLLOCommander.tsx`) — today this is just an 80px breathing circle (radial gradient div) showing greeting/briefing text. This is the placeholder to replace/upgrade into the full crystal brain hero described above.
- There's a **separate, disconnected** page `frontend/src/pages/AIExperience.tsx` at route `/ai-experience`, containing `AIChat`, `SignalFeed`, `AnalysisDashboard` components (`frontend/src/components/ai/`). Decision: **merge this into command-deck**, it should not remain a separate page.
- Backend AI/chat logic already exists and should be reused, not duplicated: `services/ollo/` (`ollo_service.py`, `personality.py`, `context.py`, `parser.py`, `planner.py`) backing `api/routes/ollo.py` (`/ollo/greet`, `/ollo/query`, `/ollo/briefing`, `/ollo/status`). Ollo is explicitly designed to never give financial advice or generate trading signals — it's a narration/explanation/navigation layer. Frontend API client: `frontend/src/api/ollo.ts`.

## Scope for this sprint

1. **Build the crystal brain hero component** replacing the current `OLLOCommander` breathing-circle, per the design brief above. It is the dominant visual on `/command-deck`.
2. **Voice input**: integrate the Web Speech API `SpeechRecognition` (with `webkitSpeechRecognition` fallback for Chromium browsers) supporting both `tr-TR` and `en-US`. User can either toggle language or the component can auto-detect from `navigator.language` as a starting default, with a manual override control. **Feature-detect and gracefully fall back to text input** when `SpeechRecognition` isn't available (e.g. Firefox) — this must not break the page for unsupported browsers.
3. **Voice output**: use `SpeechSynthesis` to speak the brain's responses back in the same language the user used (match TR/EN voice). Also show the response as text simultaneously (don't rely on audio alone).
4. **Conversational routing**: when the user's query implies navigation intent (e.g. "portföyümü göster" / "show my portfolio", "risk durumumu göster" / "show my risk"), the brain should respond conversationally AND navigate via `react-router`'s `useNavigate` to the relevant existing route (`/portfolio`, `/risk`, `/scanner`, `/analytics`, `/journal`, etc. — see the full route list in `frontend/src/App.tsx`). Use the existing `/ollo/query` backend endpoint for the actual language understanding/response generation; do not build a separate NLU layer on the frontend. If the backend response doesn't currently carry a structured "intent/route" field, propose the smallest reasonable addition to `services/ollo/parser.py` / `ollo_service.py` and the `/ollo/query` response shape to carry one, and use it — call this out clearly in your summary since it changes an existing API contract.
5. **Merge `/ai-experience` into command-deck**: fold `AIChat`, `SignalFeed`, `AnalysisDashboard` (or their relevant functionality) into the new hero experience or its immediate surrounding panels, then remove the standalone `/ai-experience` route and page (update `App.tsx` accordingly — redirect old links to `/command-deck` rather than 404ing, same pattern already used for other retired routes like `/whale` → `/command-deck`).
6. Everything else already on `CommandDeck.tsx` (mission ring, subsystem health bars) should keep working — this is an upgrade of the hero/AI section, not a full page rewrite.

## Explicit non-goals

- Do not change the overall page layout/composition beyond what's described — the design is locked, this is implementation, not a new concept.
- Do not touch backend trading/decision logic (scoring, risk, execution) — this sprint is frontend + the narrow Ollo response-shape addition described in point 4 only.
- Do not add authentication/account changes.

## Acceptance criteria

- `/command-deck` (and `/`) shows the crystal brain hero as the dominant visual, animated/alive per the brief, not a static image.
- Clicking a mic control starts voice capture in the currently selected/detected language; speaking a supported query gets both a spoken (TTS) and written response in the same language.
- At least a handful of representative navigation intents (portfolio, risk, scanner, analytics, journal) correctly route via voice or text query.
- Browsers without `SpeechRecognition` support still get a fully functional **text** version of the same experience — no crash, no dead UI.
- `/ai-experience` route no longer exists as a separate page; its functionality lives inside command-deck; old links redirect instead of 404.
- `npm run build` (in `frontend/`) succeeds with no new TypeScript errors.
- Existing command-deck features (mission ring, subsystem health) still render and function.
