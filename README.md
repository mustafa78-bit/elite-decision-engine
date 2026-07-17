# Elite Decision Engine

Multi-module intelligence engine for crypto trading signal evaluation, decision-making, and production deployment.

## Architecture

```
app.py                   # CLI entrypoint
api/                     # HTTP API + WebSocket server
├── app.py               #   APIApp factory
├── routes.py            #   Health, decisions, intelligence, features, modules
├── schemas.py           #   APIResponse, PaginatedResponse, HealthStatus, MetricsResponse, DecisionResponse, IntelligenceResponse
├── errors.py            #   APIException, NotFoundError, ValidationError, ServiceUnavailableError
├── middleware.py         #   RequestTimingMiddleware, error_handler
├── websocket.py         #   WSManager, WSEvent, WSEventType
└── __init__.py          #   Public schema exports
core/                    # Shared framework
├── engine.py            #   DecisionEngine — orchestrates signal evaluation
├── intelligence.py      #   IntelligenceBundle — multi-module fusion
├── cache.py             #   TTLCache, cached decorator (thread-safe, RLock)
├── retry.py             #   RetryConfig, RetryHandler, with_retry (exponential backoff + jitter)
├── scheduler.py         #   Scheduler, GracefulShutdown (thread-based, signal handlers)
├── health.py            #   HealthChecker — check(), is_ready(), is_alive(), get_metrics()
├── validation.py        #   ConfigValidator, validate_env, validate_port, validate_positive_float, validate_threshold
├── serialization.py     #   SerializableMixin, serialize_list
├── dashboard.py         #   DashboardAggregator — portfolio, intelligence, risk, monitoring
└── __init__.py
dto/                     # Data transfer objects
├── models.py            #   DashboardDTO, PortfolioDTO, TradeDTO, IntelligenceDTO, RiskDTO, MonitoringDTO, NotificationDTO, WebSocketDTO
└── __init__.py
decision/                # Core decision logic
├── engine.py            #   Extended decision engine
├── models.py            #   TradeOutcome, Decision models
├── confidence.py        #   Confidence scoring
├── fusion.py            #   Intelligence fusion
├── trade_memory.py      #   TradeMemoryStore (in-memory)
└── __init__.py
sentiment/               # Sentiment analysis module
news/                    # News analysis module
whale/                   # Whale tracking module
liquidity/               # Liquidity analysis module
orderflow/               # Order flow analysis module
market_structure/        # Market structure module
macro/                   # Macro analysis module
scoring/                 # Scoring engine
filters/                 # Market shock + BTC filters
execution/               # Execution bridge
models/                  # Shared models
utils/                   # Utilities
database.py              # SQLAlchemy setup + Signal/Trade tables
config.py                # Environment-based settings
tests/                   # Pytest suite (521 tests)
```

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run (CLI)
python app.py

# Run (API server)
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000

# Run tests
pytest
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health status (modules, database, uptime) |
| GET | `/ready` | Readiness probe |
| GET | `/live` | Liveness probe |
| GET | `/metrics` | Runtime metrics |
| GET | `/decisions` | Decision history (paginated, filterable) |
| GET | `/decisions/:id` | Single decision by signal ID |
| GET | `/intelligence` | Unified intelligence score + module scores |
| GET | `/features` | All module features |
| GET | `/modules` | Module diagnostics |

All responses follow `{ success, data?, error?, version, timestamp }` format.

## WebSocket Events

Connect and receive real-time events: decision, signal, intelligence, health, metrics, trade, error.

## Production

```bash
# Docker
docker build -t elite-decision-engine .
docker run -p 8000:8000 --env-file .env elite-decision-engine
```

Features: multi-stage build, HEALTHCHECK, graceful shutdown, config validation, request timing middleware, retry with exponential backoff + jitter, thread-safe TTL cache, scheduler, health probes (readiness/liveness).

## Testing

```bash
pytest                          # All tests (521)
pytest -v                        # Verbose
pytest tests/test_api_routes.py  # Single file
pytest -k "health"               # Keyword filter
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `localhost` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_DB` | `decision_engine` | Database name |
| `CHECK_INTERVAL` | `10` | Evaluation interval (s) |
| `MIN_SCORE` | `85` | Minimum signal score |
| `MAX_OPEN_TRADES` | `3` | Max concurrent trades |
| `WHALE_ENABLED` | `true` | Enable whale module |
| `LIQUIDITY_ENABLED` | `true` | Enable liquidity module |
| `ORDERFLOW_ENABLED` | `true` | Enable orderflow module |
| `MARKET_STRUCTURE_ENABLED` | `true` | Enable market structure module |
