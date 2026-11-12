# Architecture

```
                 Browser
                    |
        Frontend: nginx + static web app (80)
                    |  /api/*  (reverse proxy, prefix stripped)
        Backend: FastAPI (8000)  ----------------------+
           |            |                              |
   /chat (quick)    /jobs (long)                       |
           |            |                              |
           |        Redis queue  ->  Celery worker (progress, retries, results)
           |                                |
           +--------- AI harness -----------+
                      |  (model, context, permissions, tool loop)
          +-----------+--------------+
          |                          |
    Claude API               Tool dispatcher (allow-list)
                               |              |
                    Market tools            Python sandbox
                    (yfinance / MCP)        (internal network, no internet,
                                             read-only, CPU/RAM/pid limits)
```

## Components
| Component | Role |
|---|---|
| Frontend (nginx) | Chat UI, candlestick charts, tables, tool trace; proxies `/api` to the backend |
| Backend (FastAPI) | `/chat` for quick answers, `/jobs` for long analyses, `/health` |
| AI harness | Builds context, calls Claude, runs the tool loop, enforces the allow-list |
| Tools | Price history, indicators (SMA/RSI/MACD), fundamentals, comparison |
| Sandbox | Runs model-written Python for projections and what-if scenarios |
| Redis + Celery | Background processing with progress tracking, retries, saved results |

## Data flow
1. User asks a question in the web app.
2. The browser calls `/api/chat` (or `/api/jobs`); nginx forwards it to FastAPI.
3. The harness sends the question and tool schemas to Claude.
4. Claude requests tools; the dispatcher runs only allow-listed tools.
5. Market data returns with its source; calculations run in the sandbox.
6. Claude writes the answer with Sources and Assumptions; the browser draws charts from the tool results.
7. Long analyses go through Redis to a Celery worker; the browser polls `/api/jobs/{id}`.

## AWS deployment (draw this in the diagram)
- EC2 instance (Ubuntu, Docker Compose): frontend, api, worker, redis, sandbox
- Security group: 22 (SSH), 80 (web app), 8000 (API docs and load tests)
- Secrets: `.env` on the instance (Anthropic API key)
- External: Claude API, Yahoo Finance
- Optional upgrades: ElastiCache for Redis, ECS/Fargate for workers, S3 for saved results
