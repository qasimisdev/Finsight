# Contributing

## Branches and pull requests
1. Pick a Jira ticket and move it to **In Progress**.
2. Create a branch named with the key: `FH-7-price-tool`.
3. Commit small, with messages that start with the key: `FH-7 add price history tool`.
4. Open a pull request into `main`. Put the key in the title. The other team member reviews it.
5. CI must be green (ruff + pytest) before merging. Then move the ticket to **Done**.

`main` is protected: no direct pushes.

## Documented contributions
| Area | Owner |
|---|---|
| AI harness, tools, sandbox, worker, deploy | Muhammad Qasim |
| Research, diagrams, comparison/projection tool, CI, docs, slides | Javeria |

## Local checks
```bash
cd backend
ruff check .
pytest
```

## Secrets
Never commit `.env`. Use `.env.example` for variable names only.
