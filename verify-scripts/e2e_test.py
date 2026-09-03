"""端到端验证 usage-gateway：启动 mock 上游 + 网关，发请求确认落库统计。"""
import json
import sqlite3
import sys
import threading
import time
import os

sys.path.insert(0, r"D:\Hermes\usage-gateway")
import gateway

# 用临时数据目录，避免污染真实数据
import tempfile
_TMP = tempfile.mkdtemp(prefix="usage-gw-test-")
gateway.DB_PATH = os.path.join(_TMP, "usage.db")
gateway.DATA_DIR = os.path.dirname(gateway.DB_PATH)

# mock 上游
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
import httpx

mock = FastAPI()

def est(text):
    return max(1, len(text) // 2)

@mock.post("/v1/chat/completions")
async def mock_chat(request: Request):
    body = await request.json()
    msgs = body.get("messages", [])
    stream = bool(body.get("stream", False))
    pt = est(json.dumps(msgs, ensure_ascii=False))
    ct = 15
    usage = {"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": pt + ct}
    if stream:
        def gen():
            yield f"data: {json.dumps({'choices':[{'delta':{'content':'hi'},'finish_reason':None}]})}\n\n"
            yield f"data: {json.dumps({'choices':[{'delta':{},'finish_reason':'stop'}]})}\n\n"
            yield f"data: {json.dumps({'choices':[],'usage':usage})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream")
    return JSONResponse({
        "id": "mock", "model": body.get("model", "mock-model"),
        "choices": [{"message": {"role": "assistant", "content": "hi"}, "finish_reason": "stop"}],
        "usage": usage,
    })

# 配置网关：mock 上游指向本机 8001，端口 4100
cfg = gateway.DEFAULT_CONFIG
cfg["listen_port"] = 4100
cfg["upstreams"] = [
    {"name": "mock", "protocol": "openai", "base_url": "http://127.0.0.1:8101/v1", "api_key": "sk-mock", "models": ["mock-*"]},
    {"name": "sensenova", "protocol": "openai", "base_url": "https://token.sensenova.cn/v1", "api_key": "sk-test", "models": ["sensenova-*"]},
]
cfg["default_upstream"] = "mock"
gateway.CONFIG.clear(); gateway.CONFIG.update(cfg)
gateway.SESSION_GAP_SECONDS = cfg.get("session_gap_minutes", 30) * 60
gateway.init_db()

def run_mock():
    uvicorn.run(mock, host="127.0.0.1", port=8101, log_level="warning")
def run_gate():
    uvicorn.run(gateway.app, host="127.0.0.1", port=4100, log_level="warning")

threading.Thread(target=run_mock, daemon=True).start()
threading.Thread(target=run_gate, daemon=True).start()
time.sleep(3)

base = "http://127.0.0.1:4100"

# 1) 真实用户消息（任务1 用户指令 A）
r1 = httpx.post(f"{base}/v1/chat/completions", json={
    "model": "mock-model", "messages": [
        {"role": "user", "content": "帮我看看项目结构"},
        {"role": "assistant", "content": "好的", "tool_calls": [{"id": "t1", "type": "function", "function": {"name": "read_dir", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "t1", "content": "[files...]"},
        {"role": "user", "content": "帮我看看项目结构"},  # 同一轮（用户重发）
    ]}, timeout=15)
print("req1(同轮重发) status:", r1.status_code)

# 2) 任务2 新用户指令（换 hash → 新 turn，同 session）
r2 = httpx.post(f"{base}/v1/chat/completions", json={
    "model": "mock-model", "messages": [
        {"role": "user", "content": "统计一下 token 用量"},
    ]}, timeout=15)
print("req2(新指令) status:", r2.status_code)

# 3) 流式
r3 = httpx.post(f"{base}/v1/chat/completions", json={
    "model": "mock-model", "messages": [{"role": "user", "content": "stream test"}], "stream": True}, timeout=15)
print("req3(流式) status:", r3.status_code)

time.sleep(1)

# 统计
print("\n=== /stats.json ===")
s = httpx.get(f"{base}/stats.json", timeout=10).json()
print(json.dumps(s, ensure_ascii=False, indent=2))

# SQLite 原始
print("\n=== sessions / turns ===")
import sqlite3 as sq
con = sq.connect(gateway.DB_PATH)
con.row_factory = sq.Row
for row in con.execute("SELECT id, label, started_at FROM sessions"):
    print(" session", dict(row))
for row in con.execute("SELECT id, session_id, label FROM turns"):
    print(" turn", dict(row))
for row in con.execute("SELECT id, session_id, turn_id, model, input_tokens, output_tokens FROM requests"):
    print(" request", dict(row))
con.close()
