
import json
import time
from aiohttp import ClientResponse
from llm_perf_test import log
from llm_perf_test.builders import PerformanceMetricsBuilder
from llm_perf_test.models import PerformanceMetrics

class DefaultPerformanceMetricsBuilder(PerformanceMetricsBuilder):
    """Default implementation of PerformanceMetricsBuilder"""

    async def build(self, start_time: float, response: ClientResponse, prompt: str, streaming: bool) ->  tuple[PerformanceMetrics, str] | None:
        return  await (self._build_streaming(start_time, response, prompt) if streaming else self._build_non_streaming(start_time, response, prompt))

    async def _build_non_streaming(self, start_time: float, response: ClientResponse, prompt: str) -> tuple[PerformanceMetrics, str] | None:
        try:
            end_time = time.time()
            result = await response.json()
            content = result.get("choices")[0].get("message").get("content")
            usage = result.get('usage', {})
            log(f"🔢 Usage received: {usage}")
            total_tokens = usage.get('total_tokens', 0)
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            reasoning_tokens = (usage.get('completion_tokens_details') or {}).get('reasoning_tokens', 0)
            total_time = end_time - start_time
            tokens_per_second = total_tokens / total_time if total_time > 0 else 0
            request_id = result.get('id', 'unknown')
            metrics = PerformanceMetrics(
                total_tokens=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_time=total_time,
                tokens_per_second=tokens_per_second,
                time_to_first_token=total_time,
                request_id=request_id,
                prompt=prompt,
                reasoning_tokens=reasoning_tokens
            )
            return metrics, content
        except Exception as e:
            log(f"Failed to parse response body: {str(e)}", "error")
            return None

    async def _build_streaming(self, start_time: float, response: ClientResponse, prompt: str) -> tuple[PerformanceMetrics, str] | None:
        content = ""
        first_token_time = None
        total_tokens = prompt_tokens = completion_tokens = reasoning_tokens = 0
        request_id = "unknown"
        try:
            async for line in response.content:
                if line:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if first_token_time is None:
                                first_token_time = time.time()
                            choices = data.get('choices', [])
                            if choices and choices[0].get('delta', {}).get('content'):
                                content += choices[0]['delta']['content']
                            usage = data.get('usage', {})
                            if usage:
                                log("🔢 Usage received: {usage}")
                                completion_tokens = usage.get('completion_tokens', 0)
                                reasoning_tokens = (usage.get('completion_tokens_details') or {}).get('reasoning_tokens', 0)
                                prompt_tokens = usage.get('prompt_tokens', 0)
                                total_tokens = usage.get('total_tokens', 0)
                            request_id = data.get('id', request_id)
                        except json.JSONDecodeError:
                            continue
            end_time = time.time()
            total_time = end_time - start_time
            time_to_first_token = (first_token_time - start_time) if first_token_time else total_time
            tokens_per_second = total_tokens / total_time if total_time > 0 else 0
            metrics = PerformanceMetrics(
                total_tokens=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_time=total_time,
                tokens_per_second=tokens_per_second,
                time_to_first_token=time_to_first_token,
                request_id=request_id,
                prompt=prompt,
                reasoning_tokens=reasoning_tokens
            )
            return metrics, content
        except Exception as e:
            log(f"Failed to parse streaming response: {str(e)}", "error")
            return None
