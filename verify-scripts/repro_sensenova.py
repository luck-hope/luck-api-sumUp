"""复现网关对商汤的转发逻辑，捕获真实异常定位 500 根因。"""
import asyncio
import json
import sys
import traceback

sys.path.insert(0, r"D:\Hermes\usage-gateway")
import gateway

async def main():
    # 1) 选上游
    try:
        up = gateway.pick_upstream("sensenova-6.8-flash-lite")
        print("选中上游:", up["name"], up["base_url"], "key_len:", len(up.get("api_key", "")))
    except Exception as e:
        print("pick_upstream 异常:", repr(e)); return

    # 2) URL 拼接
    url = gateway.upstream_url(up, "/v1/chat/completions")
    print("转发 URL:", url)

    # 3) 请求体
    payload = {
        "model": "sensenova-6.8-flash-lite",
        "messages": [{"role": "user", "content": "用一句话回答：1+1等于几？"}],
        "max_tokens": 50,
    }
    headers = {"content-type": "application/json", "accept": "application/json"}
    headers["authorization"] = f"Bearer {up['api_key']}"

    # 4) 真实转发
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300, connect=10), **gateway._client_kwargs(up)) as http:
            resp = await http.post(url, json=payload, headers=headers)
        print("上游状态:", resp.status_code)
        print("上游响应头:", dict(resp.headers))
        text = resp.text
        print("上游响应前 500 字符:", text[:500])
    except Exception as e:
        print("转发异常:")
        traceback.print_exc()

import httpx
asyncio.run(main())
