# FinSight: AI Stock Market Assistant

A conversational assistant that brings market data, company research and analysis into one chat interface.
It is built around an **AI harness**: the code that coordinates the model (Claude), its context, its permissions and the analysis workflow.

> Educational analysis, not financial advice. Every answer lists its sources and assumptions.

## Features
- **Technical analysis:** candlestick charts with volume, SMA/EMA/RSI/MACD, trends.
- **Fundamental analysis:** financial statements, earnings, valuation ratios.
- **Python-powered calculations:** comparisons, projections, what-if scenarios (run in an isolated sandbox).
- **Explanations:** interactive charts and tables with sources and assumptions.
- **Background jobs:** long analyses run on Celery workers with progress and retries.

## Architecture
```
Browser -> Frontend (nginx, :80) --/api/*--> Backend FastAPI (:8000) -> Claude (tool calling)
                                                  |                        |
                                                  |                        +-> Market tools (yfinance / MCP)
                                                  |                        +-> Python sandbox (isolated container)
                                                  +-> Redis queue -> Celery worker
```
The frontend and backend are connected automatically: nginx serves the web page and forwards every
`/api/...` request to the backend, so there is no URL or CORS configuration.
Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Repository layout
| Path | Purpose |
|---|---|
| `backend/app/` | FastAPI app and the harness (Claude tool loop) |
| `backend/tools/` | Market data, indicators and the tool allow-list |
| `backend/sandbox/` | Isolated Python execution service |
| `backend/worker/` | Celery tasks for background analysis |
| `backend/tests/` | Automated tests (run in CI) |
| `frontend/public/` | Chat UI (HTML, CSS, JS, Plotly charts) |
| `frontend/nginx.conf` | Serves the UI and proxies `/api` to the backend |
| `docker-compose.yml` | Runs everything: frontend, api, worker, redis, sandbox |
| `docs/` | Architecture, Miro export, slides |

## Quick start
```bash
cp .env.example .env        # add ANTHROPIC_API_KEY
docker compose up -d --build
```
- Web app: `http://localhost` (on a server: `http://<server-ip>`)
- API docs: `http://localhost:8000/docs`

API examples:
```bash
curl -X POST localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"message": "Compare AAPL and MSFT over 1 year"}'

curl -X POST localhost:8000/jobs -H 'Content-Type: application/json' \
  -d '{"message": "Full technical and fundamental review of NVDA"}'
curl localhost:8000/jobs/<job_id>
```

## Development
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ruff check .
pytest
```

## Workflow
- Every change goes through a branch and a pull request. Branch name starts with the Jira key, e.g. `FH-7-price-tool`.
- CI (GitHub Actions) lints and tests the backend and checks the frontend on every PR.
- See [CONTRIBUTING.md](CONTRIBUTING.md).

## Team
- Muhammad Qasim
- Javeria
