# Elite Decision Engine

## Project Rules

- One feature = one commit.
- Never modify unrelated files.
- Preserve existing architecture.
- Do not rewrite working components.
- Always review git diff before commit.
- Run relevant tests before commit.
- Never commit failing code.

## Architecture

TradingSignal
    ↓
DecisionPipeline
    ↓
ExecutionLoop
    ↓
TradeEngine
    ↓
Trade (SQLAlchemy)
    ↓
PaperExecutor

## Current Milestone

Execution Loop v1 complete.

Current branch:

execution-layer

Latest milestone:

Execution Loop v1 orchestration.

Next milestone:

End-to-End Integration Test

Goal:

TradingSignal
↓

ExecutionLoop

↓

DecisionPipeline

↓

TradeEngine

↓

Trade(DB)

↓

PaperExecutor

↓

TP / SL verification

## Coding Style

- Small commits
- Dependency Injection
- Logging instead of print
- Type hints
- Preserve SQLAlchemy models
- No duplicate logic

## Before every commit

git diff

Compile

Run tests

Commit

Push
