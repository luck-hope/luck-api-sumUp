"""模拟上游:OpenAI 与 Anthropic 兼容端点,返回确定性的假 usage,用于原型自测。"""
from __future__ import annotations

import asyncio
import json

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

app = FastAPI()


def fake_usage_openai(payload: dict) -> dict:
    prompt = len(json.dumps(payload.get("messages", []), ensure_ascii=False)) // 3
    completion = 20
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
        "prompt_tokens_details": {"cached_tokens": int(prompt * 0.8)},
    }


def fake_usage_anthropic(payload: dict) -> dict:
    prompt = len(json.dumps(payload.get("messages", []), ensure_ascii=False)) // 3
    return {
        "input_tokens": int(prompt * 0.2),
        "output_tokens": 30,
        "cache_read_input_tokens": int(prompt * 0.7),
        "cache_creation_input_tokens": int(prompt * 0.1),
    }


@app.post("/v1/chat/completions")
async def chat(request: Request):
    payload = await request.json()
    usage = fake_usage_openai(payload)
    model = payload.get("model", "mock-gpt")
    if payload.get("stream"):
        async def gen():
            for i in range(3):
                yield f"data: {json.dumps({'id': 'c', 'choices': [{'delta': {'content': 'x'}}]})}\n\n".encode()
                await asyncio.sleep(0.05)
            final = {"id": "c", "choices": [], "usage": usage}
            yield f"data: {json.dumps(final)}\n\ndata: [DONE]\n\n".encode()
        return StreamingResponse(gen(), media_type="text/event-stream")
    return JSONResponse({"id": "c", "model": model, "choices": [{"message": {"role": "assistant", "content": "ok"}}], "usage": usage})


@app.post("/v1/messages")
async def messages(request: Request):
    payload = await request.json()
    usage = fake_usage_anthropic(payload)
    if payload.get("stream"):
        async def gen():
            start = {"type": "message_start", "message": {"usage": usage}}
            yield f"event: message_start\ndata: {json.dumps(start)}\n\n".encode()
            for _ in range(3):
                yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'delta': {'text': 'y'}})}\n\n".encode()
                await asyncio.sleep(0.05)
            delta = {"type": "message_delta", "usage": {"output_tokens": usage["output_tokens"]}}
            yield f"event: message_delta\ndata: {json.dumps(delta)}\n\n".encode()
        return StreamingResponse(gen(), media_type="text/event-stream")
    return JSONResponse({"id": "m", "role": "assistant", "content": [{"type": "text", "text": "ok"}], "usage": usage})


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")
