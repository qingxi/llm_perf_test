from abc import ABC, abstractmethod
from aiohttp import ClientResponse
from llm_perf_test.models import PerformanceMetrics


class PerformanceMetricsBuilder(ABC):
    """Abstract base class for building performance metrics from API responses"""
    @abstractmethod
    async def build(self, start_time: float, response: ClientResponse, prompt: str, streaming: bool) ->  tuple[PerformanceMetrics, str] | None:
        """Build PerformanceMetrics from the response"""
        pass