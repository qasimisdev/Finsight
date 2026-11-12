"""Python sandbox service.

Runs untrusted code in a child process with a timeout and resource limits.
The container itself is isolated by docker-compose: internal network only (no internet),
read-only filesystem, dropped capabilities, memory/CPU/pid limits.
"""
import resource
import subprocess
import sys

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="FinSight Sandbox")

TIMEOUT_SECONDS = 10
MAX_OUTPUT = 20000


class RunRequest(BaseModel):
    code: str


def _limits() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT_SECONDS, TIMEOUT_SECONDS))
    resource.setrlimit(resource.RLIMIT_AS, (400 * 1024 * 1024, 400 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
def run(req: RunRequest):
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", req.code],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            preexec_fn=_limits,
            cwd="/tmp",
        )
        return {
            "stdout": proc.stdout[:MAX_OUTPUT],
            "stderr": proc.stderr[:MAX_OUTPUT],
            "exit_code": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "timeout", "exit_code": -1}
