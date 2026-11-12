from typing import Literal

from celery.result import AsyncResult
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.harness import run_chat
from worker.tasks import celery_app, run_analysis

app = FastAPI(title="FinSight API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class Msg(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[Msg] = Field(default_factory=list, max_length=20)

    def messages(self) -> list[dict]:
        past = [m.model_dump() for m in self.history]
        return past + [{"role": "user", "content": self.message}]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):
    """Quick questions: answered inside the request."""
    return run_chat(req.messages())


@app.post("/jobs")
def create_job(req: ChatRequest):
    """Long analyses: queued in Redis and processed by a Celery worker."""
    task = run_analysis.delay(req.messages())
    return {"job_id": task.id}


@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    res = AsyncResult(job_id, app=celery_app)
    payload = {"job_id": job_id, "state": res.state}
    if res.state == "PROGRESS":
        payload["progress"] = res.info
    elif res.state == "SUCCESS":
        payload["result"] = res.result
    elif res.state == "FAILURE":
        payload["error"] = str(res.info)
    return payload
