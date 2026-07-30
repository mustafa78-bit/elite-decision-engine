# Chapter 30: Glossary of Terms

## 📌 Purpose
This glossary provides a unified dictionary of technical and operational terms used across the NEXUS platform. Using consistent nomenclature ensures that human developers, quantitative architects, and future AI assistants can communicate with complete clarity.

---

## 📖 Glossary of Terms

* **Average True Range (ATR)**: A technical indicator that measures asset volatility by analyzing the range of price movements over a specific period (typically 14 candles). Used in NEXUS to calculate dynamic stop-loss and take-profit targets.
* **Calmar Ratio**: A risk-adjusted performance metric that measures portfolio returns relative to maximum drawdown. Used by portfolio managers to evaluate downside risk.
* **Closed Beta**: A testing phase where access to the platform is restricted to a limited group of verified users (typically 10-50 testers) to gather qualitative and operational feedback.
* **Cognitive Conflict**: A logical contradiction detected between different analysis methods (e.g. bullish macro indicators vs. bearish short-term oscillators). Detected by the Evidence Engine to adjust final confidence scores.
* **Cumulative Volume Delta (CVD)**: A market metric that tracks the net difference between buying and selling volume over time. Used by the Whale Agent to monitor institutional accumulation.
* **Default-Deny**: A security design pattern where all incoming requests are blocked by default. Access is only granted if a request presents a valid, verified authorization token or targets an explicitly whitelisted path.
* **DetachedInstanceError**: A common database error that occurs when trying to access lazy-loaded attributes on an ORM instance after its database session has been closed. Prevented in NEXUS by using decoupled dictionary payloads.
* **Decision Pipeline**: The multi-stage process that ingests, filters, scores, and validates trading signals before they are routed to the execution engine.
* **Drawdown**: The peak-to-trough decline of portfolio equity over a specific period, expressed as a percentage.
* **Evidence**: A standardized, auditable data payload (e.g. technical indicators, sentiment ratings, agent logs) used to justify trading decisions.
* **Execution Loop**: The background coordinator that polls for new signals, monitors active paper positions, and executes take-profit and stop-loss targets.
* **FIFO Eviction**: A cache clearance strategy where the oldest items in memory are removed first to make room for new data. Used to prevent memory leaks in high-frequency environments.
* **Founder Alpha**: A development phase where the platform's founder uses the system daily to manage portfolios and make decisions, ensuring product development is guided by real-world usage.
* **HttpOnly Cookie**: A secure cookie configuration that prevents browser scripts (such as JavaScript) from accessing stored session tokens, protecting them from XSS attacks.
* **HUD Layout**: A high-density user interface optimized to display key metrics and telemetry on a single screen, reducing cognitive load for active traders.
* **JSON Web Token (JWT)**: A secure, signed token format used to transmit user session identities between browser clients and API backends.
* **Learning Intelligence Engine (LIE)**: The cognitive engine that analyzes historical decisions and performance to identify patterns and refine future confidence scores.
* **Multi-Agent Council**: A collective of specialized virtual analysts (Trend, Risk, Technical, Whale, Sentiment) that debate market conditions to generate comprehensive trade justifications.
* **Open Interest (OI)**: The total number of active, outstanding derivative contracts (such as futures) that have not been settled. Used to measure market liquidity and momentum.
* **Paper Trading**: A zero-risk market simulation where trades and orders are executed in memory using real-time price feeds, validating strategies without exposing capital.
* **Position Sizing**: The process of calculating the size or volume of a position based on portfolio risk limits and underlying asset volatility (ATR).
* **Relative Strength Index (RSI)**: A momentum oscillator that measures the speed and change of price movements, indicating overbought or oversold conditions.
* **Risk Engine**: The pre-flight safety coordinator that evaluates signals against portfolio drawdown limits, position capacities, and volatility parameters.
* **Sharpe Ratio**: A risk-adjusted return metric that measures excess portfolio returns relative to total volatility, providing an index of trading efficiency.
* **Sortino Ratio**: A risk-adjusted return metric similar to the Sharpe ratio, but focusing purely on downside volatility to protect the system from penalizing positive upside momentum.
* **Source Trace**: An auditable trace record detailing the exact origin, timestamp, and inputs used to compute a piece of evidence.
* **Vite**: A modern, high-speed frontend build tool used to compile and serve React single-page applications.
* **WebSocket**: A bi-directional, persistent communication protocol that allows servers to push real-time updates to client browsers without polling overhead.
* **XSS (Cross-Site Scripting)**: A security vulnerability where malicious scripts are injected into trusted web applications. Mitigated in NEXUS using secure Content Security Policies (CSP).
