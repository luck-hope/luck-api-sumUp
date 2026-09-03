"""真实商汤端到端验证：启动 usage-gateway（读真实 config.json），发一个真实商汤请求。"""
import json
import os
import sqlite3
import sys
import threading
import time

sys.path.insert(0, r"D:\Hermes\usage-gateway")
import gateway

# 用临时 DB，避免污染真实数据
import tempfile
_TMP = tempfile.mkdtemp(prefix="usage-gw-sn-")
gateway.DB_PATH = os.path.join(_TMP, "usage.db")
gateway.init_db()

import uvicorn
import httpx

def run_gate():
    uvicorn.run(gateway.app, host="127.0.0.1", port=4200, log_level="warning")

threading.Thread(target=run_gate, daemon=True).start()
time.sleep(3)

base = "http://127.0.0.1:4200"

# 真实商汤模型请求（走 config.json 的 sensenova 上游）
print("=== 真实商汤请求 ===")
try:
    r = httpx.post(f"{base}/v1/chat/completions", json={
        "model": "sensenova-6.8-flash-lite",
        "messages": [{"role": "user", "content": "用一句话回答：1+1等于几？"}],
        "max_tokens": 50,
    }, timeout=60)
    print("status:", r.status_code)
    print("body head:", r.text[:200])
except Exception as exc:
    print("请求异常:", repr(exc))

time.sleep(1)

print("\n=== /stats.json ===")
try:
    s = httpx.get(f"{base}/stats.json", timeout=10)
    print("status:", s.status_code)
    print(json.dumps(s.json(), ensure_ascii=False, indent=2)[:800])
except Exception as exc:
    print("stats 异常:", repr(exc))

print("\n=== 数据库内容 ===")
con = sqlite3.connect(str(gateway.DB_PATH))
con.row_factory = sqlite3.Row
for row in con.execute("SELECT id, label FROM sessions"):
    print(" session:", dict(row))
for row in con.execute("SELECT id, session_id, label FROM turns"):
    print(" turn:", dict(row))
for row in con.execute("SELECT id, model, upstream, input_tokens, output_tokens, status FROM requests"):
    print(" request:", dict(row))
con.close()
