# Sprint XII v2 — High-Performance Cognitive Process Scheduler

This document specifies the design, implementation, data models, APIs, and verification of the high-performance **Cognitive Process Scheduler** implemented as part of Sprint XII v2 in the NEXUS Decision Operating System.

---

## 1. Core Architectural Concepts

The Cognitive Scheduler coordinates the concurrent execution of multiple decoupled cognitive operations (such as multi-workstation opportunity scanning, automated deep research, risk assessment, debate, and calibration) under strict, deterministic execution guarantees.

### 1.1 Cognitive Process Model
Each scheduler execution unit is defined as a `CognitiveProcess` tracking:
- **`process_id`**: A unique string identifier.
- **`name`**: Descriptive label of the process.
- **`owner`**: Module or workstation agent owning the process.
- **`priority`**: Numerical execution rank (lower is higher priority).
- **`state`**: Current lifecycle phase (`PENDING`, `RUNNING`, `SUSPENDED`, `COMPLETED`, `FAILED`).
- **`version`**: Monotonically increasing version counter.
- **`working_memory`**: Private dictionary representing its isolated scratchpad.
- **`checkpoint_data`**: Temporary progress data saved for suspend/resume actions.
- **`manifest`**: Boundaries defining maximum resource utilization constraints.

### 1.2 Resource Manifest
Each process registers a `ResourceManifest` containing:
- **`default_cpu_share`** / **`ceiling_cpu_share`**: CPU allocations.
- **`max_duration_seconds`**: The strict deadline after which the task is preempted.
- **`max_memory_mb`**: Maximum allowed memory size.

---

## 2. Dynamic State Transitions

```
    [Create] ──▶ PENDING ────(De-queue)────▶ RUNNING
                   ▲                            │
                   │                            ├───(Yield / Interrupt)──▶ SUSPENDED
                   │                            │                              │
                (Resume)                        ├───(Violate Limits) ──▶ FAILED│
                   │                            │                              │
                   └────────────────────────────┼──────────────────────────────┘
                                                ▼
                                            COMPLETED
```

---

## 3. Concurrency & Transaction Integrity

### 3.1 Versioned Optimistic Concurrency
To ensure thread safety and prevent stale state overwrites in shared process pools, a version validation model is strictly enforced:
- Every state mutation or memory-slice update requires verifying that the target process's current `version` matches the expectation of the caller.
- On match, the change is written and the version is incremented.
- On mismatch, a `VersionValidationError` is raised, forcing rollback.

### 3.2 Shared Versioned Queue
The global scheduling task queue is thread-safe and versioned. Dequeuing operations always prioritize lower-priority numbers first (priority queueing).

### 3.3 Commit-or-Retry
Updates to the task queue can use `commit_or_retry()`, which transactionally applies actions and retries up to 5 times on collision detection.

---

## 4. Safety & Preemption Mechanisms

### 4.1 Local Real-Time Interrupt Path
Allows immediate preemption of running processes (e.g. on emergency risk triggers or workstation priority shifts). The process checkpoints its current progress and transitions into `SUSPENDED`.

### 4.2 Yield-Point Enforcement
Processes can register local yield points (`yield_point()`) to gracefully check if they have been requested to suspend, and return control to the scheduler.

### 4.3 Atomic Duration Enforcement & violations
Scheduler tick limits are actively monitored. Exceeding `max_duration_seconds` results in a `SchedulingGuaranteeViolation` and immediate preemption into `FAILED`.

### 4.4 Scheduler Degraded Mode & Drift Detection
The actual resource usage of active processes is constantly measured. Exceeding resource manifests triggers **Manifest Drift Detection** and forces the scheduler to enter **Degraded Mode**, dropping lower priority tasks (`priority > 5`) to maintain system stability.

---

## 5. API Reference

All routes are registered under the prefix `/api/v1/scheduler`.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/scheduler/status` | `GET` | Observability metrics, drift alerts, violations, queue size. |
| `/api/v1/scheduler/enqueue` | `POST` | Enqueues and registers a new process. |
| `/api/v1/scheduler/interrupt` | `POST` | Preempts a running process immediately. |
| `/api/v1/scheduler/resume` | `POST` | Resumes a suspended process from its last checkpoint. |
| `/api/v1/scheduler/step` | `POST` | Triggers a single scheduler tick slice. |
| `/api/v1/scheduler/degraded` | `POST` | Manually toggle degraded mode. |
| `/api/v1/scheduler/distributed/sync` | `POST` | distributed synchronization payload enqueuing. |
