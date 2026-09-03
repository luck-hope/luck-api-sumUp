"""
本地透明代理网关 (基于 aiohttp)
默认监听 http://127.0.0.1:8045，自动解析 /v1/chat/completions
"""
import time
import json
import asyncio
from aiohttp import web, ClientSession, ClientTimeout
from .counter import TokenStatsTracker


class LocalGatewayProxy:
    def __init__(self, port: int = 8045, upstream_url: str = "https://api.openai.com", on_token_update=None):
        self.port = port
        self.upstream_url = upstream_url.rstrip('/')
        self.on_token_update = on_token_update
        self.tracker = TokenStatsTracker()
        self.app = web.Application()
        self.app.router.add_route('*', '/{tail:.*}', self.handle_proxy)
        self.runner = None
        self.site = None

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '127.0.0.1', self.port)
        await self.site.start()

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()

    async def handle_proxy(self, request: web.Request) -> web.StreamResponse:
        target_path = request.match_info['tail']
        target_url = f"{self.upstream_url}/{target_path}"

        headers = dict(request.headers)
        headers.pop('Host', None)
        body = await request.read()

        model_name = "unknown"
        first_prompt_title = "新请求任务"
        try:
            if body:
                payload = json.loads(body.decode('utf-8'))
                model_name = payload.get('model', 'unknown')
                messages = payload.get('messages', [])
                if messages:
                    last_user_msg = next((m.get('content', '') for m in reversed(messages) if m.get('role') == 'user'), "")
                    if last_user_msg:
                        first_prompt_title = str(last_user_msg).strip().split('\n')[0][:30]
        except Exception:
            pass

        start_time = time.time()
        first_byte_time = None

        timeout = ClientTimeout(total=600)
        async with ClientSession(timeout=timeout) as session:
            try:
                async with session.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    data=body,
                    params=request.rel_url.query
                ) as upstream_res:
                    response = web.StreamResponse(
                        status=upstream_res.status,
                        headers=dict(upstream_res.headers)
                    )
                    await response.prepare(request)

                    input_tok = 0
                    output_tok = 0
                    cached_tok = 0

                    async for chunk in upstream_res.content.iter_any():
                        if first_byte_time is None:
                            first_byte_time = time.time()
                        await response.write(chunk)

                        # 解析流式 chunks 的 usage 信息
                        chunk_str = chunk.decode('utf-8', errors='ignore')
                        if "usage" in chunk_str:
                            for line in chunk_str.split('\n'):
                                if line.startswith("data: ") and line.strip() != "data: [DONE]":
                                    try:
                                        data = json.loads(line[6:])
                                        usage = data.get("usage")
                                        if usage:
                                            input_tok = usage.get("prompt_tokens", 0)
                                            output_tok = usage.get("completion_tokens", 0)
                                            prompt_details = usage.get("prompt_tokens_details", {})
                                            cached_tok = prompt_details.get("cached_tokens", 0)
                                    except Exception:
                                        pass

                    await response.write_eof()

                    ttft_ms = int((first_byte_time - start_time) * 1000) if first_byte_time else 0
                    cost = self.tracker.record_transaction(model_name, input_tok, output_tok, cached_tok)

                    if self.on_token_update:
                        self.on_token_update({
                            "model": model_name,
                            "title": first_prompt_title,
                            "input_tokens": input_tok,
                            "output_tokens": output_tok,
                            "cached_tokens": cached_tok,
                            "ttft_ms": ttft_ms,
                            "cost_cny": cost,
                            "hit_rate": (f"{round(cached_tok / input_tok * 100)}%" if input_tok > 0 else "0%")
                        })

                    return response
            except Exception as e:
                return web.Response(text=f"Gateway Proxy Error: {str(e)}", status=502)
