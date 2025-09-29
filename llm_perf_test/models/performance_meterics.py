
from pydantic import BaseModel


class PerformanceMetrics(BaseModel):
    """Data class to store performance metrics"""
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_time: float
    tokens_per_second: float
    time_to_first_token: float
    request_id: str
    prompt: str = ''  # Optional, default to ''
    reasoning_tokens: int = 0  # Optional, default to 0
