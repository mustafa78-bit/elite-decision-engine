# Chapter 19: Security Architecture

## 🛡️ Enterprise Security Blueprint
NEXUS implements a defense-in-depth security model designed to secure high-frequency trading operations, protect user identity, and validate data integrity. The platform's security controls are structured across multiple layers, including API gateways, authentication middleware, and database encryption.

---

## 🔒 Default-Deny REST Endpoint Hardening
All endpoints in NEXUS are secured using a **Default-Deny** paradigm (`api/middleware.py`). By default, every REST route requires a valid, signed JSON Web Token (JWT) in the `Authorization: Bearer <JWT>` header.

Only a designated set of paths is explicitly whitelisted for public access:
- `/health` (system diagnostic check)
- `/auth/register` (user registration)
- `/auth/login` (user session authentication)
- Any incoming request failing to present a valid token on a protected path is immediately rejected with a `401 Unauthorized` status code before reaching any business logic.

---

## 🔑 JWT Authentication & Signature Validation
User sessions are managed using **JSON Web Tokens (JWT)** generated via the standard HS256 algorithm:
- Password storage is secured using robust, one-way cryptographic hashing algorithms, preventing plain-text exposure in the database.
- JWT signatures are generated on the server using a cryptographically secure key.
- Tokens contain structured claims, including user identifier, username, and token expiration parameters.
- Token validation is executed on every protected request. If a token's expiration timestamp is breached or the cryptographic signature is invalid, the request is rejected immediately.

---

## 🔒 WebSocket Token Handshake
To prevent unauthorized sniffing of streaming market telemetry or active position updates, NEXUS enforces explicit token validation on WebSocket connection handshakes:
- Real-time endpoints (e.g., `/ws/trades`, `/ws/notifications`) read the JWT token directly from the query parameters: `?token=<JWT>`.
- The connection is validated against the cryptographic signature key before the handshake is completed.
- If the token is invalid or missing, the server rejects the connection with a specific close code (`4001`), keeping data pipelines isolated and secure.

---

## 🛡️ Global Security Headers & CORS Policy
The API gateway appends standard security headers on all HTTP responses:
- `X-Content-Type-Options: nosniff`: Prevents browsers from MIME-sniffing responses.
- `X-Frame-Options: DENY`: Blocks clickjacking attacks by preventing the HUD from being rendered inside third-party frames or iframes.
- `X-XSS-Protection: 1; mode=block`: Activates built-in browser cross-site scripting filters.
- `Content-Security-Policy (CSP)`: Configured in the index layout to restrict script, style, and data source origins while allowing TradingView widgets to run securely.
- `CORS Policies`: Explicitly limits cross-origin resource sharing to trusted, configured domain paths (`CORS_ORIGINS`), blocking unauthorized cross-origin requests.
- `Strict-Transport-Security (HSTS)`: Applied in production environments with a max-age of 1 year, forcing connections over secure HTTPS.
