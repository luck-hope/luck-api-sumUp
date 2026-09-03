"""验证 usage-gateway 对两个商汤模型名的真实路由 + 统计落库。"""
import json
import httpx
import time

BASE = "http://127.0.0.1:4000"

def test(model):
    print(f"\n=== model={model} ===")
    try:
        r = httpx.post(f"{BASE}/v1/chat/completions", json={
            "model": model,
            "messages": [{"role": "user", "content": "用一句话回答：1+1等于几？"}],
            "max_tokens": 40,
        }, timeout=60)
        print("status:", r.status_code)
        print("body:", r.text[:300])
    except Exception as e:
        print("异常:", repr(e))

# 两个都是商汤的模型名
test("deepseek-v4-flash")
test("sensenova-6.8-flash-lite")

time.sleep(1)
print("\n=== 统计（应该记录了上面两个请求）===")
try:
    s = httpx.get(f"{BASE}/stats.json", timeout=10).json()
    print("今日请求:", s["today"]["requests"])
    print("会话数:", s["today"]["sessions"])
    print("命中率:", s["today"]["hit_rate"])
except Exception as e:
    print("异常:", repr(e))
