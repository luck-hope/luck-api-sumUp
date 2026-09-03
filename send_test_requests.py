"""原型自测:向网关发一组模拟请求,验证 turn/session 归组与 usage 归一化。

场景:
1. turn1:同一用户指令下两次请求(第二次模拟 agent 循环:历史+tool 结果,尾随 user 不变)
2. 新指令 → turn2(同会话)
3. Anthropic 协议流式;消息里带 tool_result 块验证跳过逻辑
"""
import json

import httpx

GATEWAY = "http://127.0.0.1:4000"

Q1 = "帮我统计订单列表页的缓存命中率"


def main() -> None:
    with httpx.Client(timeout=30) as c:
        # 1. turn1 第一次请求
        r = c.post(f"{GATEWAY}/v1/chat/completions", json={
            "model": "mock-glm", "stream": False,
            "messages": [{"role": "user", "content": Q1}],
        })
        print("req1:", r.status_code)

        # 2. turn1 第二次请求(agent 循环:追加了 assistant+tool 消息,尾随 user 不变)
        r = c.post(f"{GATEWAY}/v1/chat/completions", json={
            "model": "mock-glm", "stream": True,
            "messages": [
                {"role": "user", "content": Q1},
                {"role": "assistant", "content": None, "tool_calls": [{"id": "t1", "type": "function", "function": {"name": "sql", "arguments": "{}"}}]},
                {"role": "tool", "tool_call_id": "t1", "content": "rows=42"},
            ],
        })
        print("req2 (stream):", r.status_code)

        # 3. 新指令 → 新 turn
        r = c.post(f"{GATEWAY}/v1/chat/completions", json={
            "model": "mock-glm", "stream": False,
            "messages": [{"role": "user", "content": "把这个报表导出成 Excel"}],
        })
        print("req3:", r.status_code)

        # 4. Anthropic 流式,带 tool_result 块(应被跳过)
        r = c.post(f"{GATEWAY}/v1/messages", json={
            "model": "mock-claude", "stream": True, "max_tokens": 100,
            "messages": [
                {"role": "user", "content": "看看今天的日志有没有报错"},
                {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "u1", "content": "no error"}]},
            ],
        })
        print("req4 (anthropic stream):", r.status_code)

    stats = httpx.get(f"{GATEWAY}/stats.json").json()
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
