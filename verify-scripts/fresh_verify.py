"""用最新代码 + 最新配置在独立端口启动全新网关，发真实商汤请求验证。
若新实例 200 → 问题在旧进程；若也 500 → 代码 bug。
"""
import json
import os
import sqlite3
import sys
import threading
import time

sys.path.insert(0, r"D:\Hermes\usage-gateway")
import gateway

# 隔离数据目录
import tempfile
_TMP = tempfile.mkdtemp(prefix="usage-gw-fresh-")
gateway.DB_PATH = os.path.join(_TMP, "usage.db")
gateway.init_db()

# 打印网关内存里的 sensenova key 长度（确认加载的是最新配置）
for u in gateway.CONFIG.get("upstreams", []):
    if u.get("name") == "sensenova":
        print(f"网关内存 sensenova key_len = {len(u.get('api_key',''))}")

import uvicorn
import httpx

def run_gate():
    uvicorn.run(gateway.app, host="127.0.0.1", port=4300, log_level="warning")

threading.Thread(target=run_gate, daemon=True).start()
time.sleep(3)

base = "http://127.0.0.1:4300"
print("\n=== 发真实商汤请求到新网关 ===")
try:
    r = httpx.post(f"{base}/v1/chat/completions", json={
        "model": "sensenova-6.8-flash-lite",
        "messages": [{"role": "user", "content": "用一句话回答：1+1等于几？"}],
        "max_tokens": 50,
    }, timeout=60)
    print("status:", r.status_code)
    print("body:", r.text[:400])
except Exception as exc:
    print("异常:", repr(exc))

time.sleep(1)
print("\n=== stats ===")
try:
    s = httpx.get(f"{base}/stats.json", timeout=10).json()
    print("requests:", s["today"]["requests"], "sessions:", s["today"]["sessions"])
except Exception as exc:
    print("stats 异常:", repr(exc))
