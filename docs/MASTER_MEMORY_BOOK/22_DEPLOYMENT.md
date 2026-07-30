# Chapter 22: Deployment Architecture

## 🚀 High-Availability Containerization
NEXUS uses **Docker** to package and run both development and production environments, ensuring consistent behavior from local setups to production servers.

---

## 🏗️ Docker Container Configurations

The platform is split into two primary container profiles:

### 1. Main Backend Container (`Dockerfile` & `Dockerfile.prod`)
- Built on a lightweight, secure **Python 3.13-slim** base image.
- **Dependency Management**: Uses **Poetry** to manage packages, locking dependency versions to ensure reproducible builds.
- **Production Optimization (`Dockerfile.prod`)**:
  - Implements a multi-stage build process to keep final image sizes small.
  - Excludes development dependencies (such as pytest).
  - Uses **Gunicorn** running **Uvicorn** workers to handle concurrent web traffic.
  - Runs under a dedicated, non-root system user to improve container security.

### 2. Single-Page Application Frontend Container (`frontend/Dockerfile`)
- Built using a multi-stage Docker configuration:
  - **Stage 1 (Build)**: Mounts a **Node 20** image to install dependencies and compile Vite static assets.
  - **Stage 2 (Run)**: Copies the compiled static folder (HTML, JS, CSS) to a lightweight **Nginx** server image.
  - Nginx is configured to serve assets securely, handle SPA route fallbacks, and proxy WebSocket traffic.

---

## 🧭 Production Orchestration

In production, services are coordinated to support automated setups:

- **Reverse Proxy / SSL**: An edge router or reverse proxy (e.g., Traefik or Nginx) routes incoming domain requests, terminates SSL/TLS connections, and proxies WebSocket connections.
- **FastAPI Backend**: Serves API traffic and runs background execution and simulation loops.
- **Relational Database**: Runs a robust **PostgreSQL 16** instance with persistent volume mounts to secure trade records.
- **Static Frontend**: Nginx serves compiled React assets to browsers with optimized caching and security headers.
- This modular container architecture simplifies deployment, ensures environment consistency, and makes scaling individual services straightforward.
