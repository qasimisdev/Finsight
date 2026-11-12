"""The AI harness: coordinates the model, context, permissions and the tool-calling loop."""
from __future__ import annotations

import json
import os
from collections.abc import Callable

import anthropic

from tools.registry import TOOLS, dispatch

SYSTEM_PROMPT = """You are FinSight, an AI stock market assistant.
- Use the tools to fetch real data. Never invent prices or financial figures.
- For projections and what-if scenarios, use run_python and print the result.
- Every answer must end with two short sections: "Sources" and "Assumptions".
- You provide analysis for education, not financial advice. Say so briefly."""

MAX_STEPS = 8


def run_chat(
    messages: list[dict],
    on_step: Callable[[str], None] | None = None,
) -> dict:
    """Run the tool loop until Claude gives a final answer. Returns text plus tool trace."""
    client = anthropic.Anthropic()
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
    convo = list(messages)
    trace: list[dict] = []

    for step in range(MAX_STEPS):
        resp = client.messages.create(
            model=model,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=convo,
        )
        if resp.stop_reason != "tool_use":
            text = "".join(b.text for b in resp.content if b.type == "text")
            return {"answer": text, "trace": trace}

        convo.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            if on_step:
                on_step(f"step {step + 1}: {block.name}")
            output = dispatch(block.name, block.input)
            trace.append({"tool": block.name, "input": block.input, "output": output})
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(output, default=str)[:20000],
                }
            )
        convo.append({"role": "user", "content": results})

    return {"answer": "Stopped: too many tool steps.", "trace": trace}
