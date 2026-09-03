"""
Token 统计与价格计算核心组件
支持流式与非流式、TTFT 首字时间测量以及上下文缓存命中率计算
"""
import time
from typing import Dict, Any, Optional

MODEL_PRICING = {
    # 格式: (输入价格/M, 输出价格/M, 缓存命中输入价格/M) - 单位：人民币元
    "claude-3-5-sonnet": (21.0, 105.0, 2.1),
    "claude-3-7-sonnet": (21.0, 105.0, 2.1),
    "claude": (21.0, 105.0, 2.1),
    "gpt-4o": (17.5, 70.0, 8.75),
    "gpt-4o-mini": (1.05, 4.2, 0.525),
    "deepseek-chat": (1.0, 2.0, 0.1),
    "deepseek-coder": (1.0, 2.0, 0.1),
    "deepseek": (1.0, 2.0, 0.1),
    "default": (15.0, 60.0, 3.75)
}


class TokenStatsTracker:
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cached_tokens = 0
        self.total_cost_cny = 0.0
        self.total_requests = 0

    @staticmethod
    def get_pricing(model_name: str):
        model_name_lower = model_name.lower()
        # 先查具体模型，default 兜底放在最后
        for key, price in MODEL_PRICING.items():
            if key == "default":
                continue
            if key in model_name_lower:
                return price
        return MODEL_PRICING["default"]

    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int, cached_tokens: int = 0) -> float:
        in_p, out_p, cache_p = cls.get_pricing(model)
        normal_input = max(0, input_tokens - cached_tokens)
        cost = (normal_input * in_p + cached_tokens * cache_p + output_tokens * out_p) / 1_000_000.0
        return round(cost, 4)

    def record_transaction(self, model: str, input_tok: int, output_tok: int, cached_tok: int = 0) -> float:
        self.total_requests += 1
        self.total_input_tokens += input_tok
        self.total_output_tokens += output_tok
        self.total_cached_tokens += cached_tok

        cost = self.calculate_cost(model, input_tok, output_tok, cached_tok)
        self.total_cost_cny += cost
        return cost
