import asyncio
import os
import ssl
import time
from typing import List,Optional
import uuid

import aiohttp

from llm_perf_test import log
from llm_perf_test.builders import PerformanceMetricsBuilder, DefaultPerformanceMetricsBuilder
from llm_perf_test.models import PerformanceMetrics


class LLMPerformanceTester:
    """Class to perform performance testing on LLM APIs"""
    def __init__(self,
                 base_url: str,
                 api_key: str,
                 model: str,
                 result_dir: str = "",
                 api_version: str = "",
                 verify_ssl: bool = True,
                 metrics_builder: Optional[PerformanceMetricsBuilder] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.api_version = api_version
        self.verify_ssl = verify_ssl
        self.result_dir = result_dir
        self.metrics_builder = metrics_builder or DefaultPerformanceMetricsBuilder()
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "api-key": self.api_key  # For Azure OpenAI compatibility
        }

    def save_raw_response(self, content: str, request_id: str) -> None:
        """Save raw JSON response to a file"""
        if not self.result_dir:
            return
        filename = os.path.join(self.result_dir, f"response_{request_id}.json")
        try:
            with open(filename, "w", encoding='utf-8') as f:
                f.write(content)
            log(f"Raw response saved to {filename}")
        except Exception as e:
            log(f"Failed to save raw response: {str(e)}", "error")

    def get_ssl_context(self) -> ssl.SSLContext|bool:
        """Create SSL context based on verification setting"""
        if not self.verify_ssl:
            # Create an SSL context that doesn't verify certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            return ssl_context
        return False  # Use default SSL verification
 
    async def single_request(self,
                           session: aiohttp.ClientSession,
                           prompt: str,
                           temperature: float = 0.0,
                           use_streaming: bool = False) -> PerformanceMetrics:

        """Perform a single request and measure performance"""
        def _build_endpoint():
            # For Azure OpenAI, use chat/completions endpoint
            url = f"{self.base_url}/chat/completions"
            if self.api_version!='' and "api-version" not in url:
                url += f"?api-version={self.api_version}"
            return url
        
        def _build_payload():
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "stream": use_streaming
            }
            if use_streaming:
                payload["stream_options"] = {"include_usage": True}  # Request usage in streaming
            return payload

        def _build_headers():
            headers = self.headers.copy()
            headers.update({
                "x-conversation-id": str(uuid.uuid4()),          # custom
                "x-ms-client-request-id": str(uuid.uuid4())      # Azure trace (GUID)
            })
            return headers
        

        async def _check_response_status(response):
            if response.status != 200:
                error_text = await response.text()
                raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_text,
                            headers=response.headers
                        )
        
        start_time = time.time()
        
        try:
            async with session.post(_build_endpoint(),
                                  headers=_build_headers(),
                                  json=_build_payload()) as response:

                await _check_response_status(response)
                result = await self.metrics_builder.build(start_time, response, prompt, use_streaming)
                if result is None:
                    raise ValueError("Failed to extract performance metrics from response.")
                metrics, content = result
                if content:
                    self.save_raw_response(content, metrics.request_id)
                return metrics
                
        except Exception as e:
            log(f"Request failed: {str(e)}", "error")
            raise

    async def concurrent_test(self,
                            prompts: List[str],
                            concurrent_requests: int,
                            request_timeout: int,
                            use_streaming: bool = False) -> List[PerformanceMetrics]:
        """Run concurrent requests to test throughput"""
        
        # Create SSL context and connector with SSL verification settings
        ssl_context = self.get_ssl_context()
        connector = aiohttp.TCPConnector(
            limit=concurrent_requests * 2,
            ssl=ssl_context
        )
        timeout = aiohttp.ClientTimeout(total=request_timeout)  # 5 minute timeout
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            
            for prompt in prompts:
                task = self.single_request(session,prompt,use_streaming=use_streaming)
                tasks.append(task)
            
            # Run requests concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_results = [r for r in results if isinstance(r, PerformanceMetrics)]
            exceptions = [r for r in results if isinstance(r, Exception)]
            
            if exceptions:
                log(f"Warning: {len(exceptions)} requests failed", "warning")
                for i, exc in enumerate(exceptions[:3]):  # Show first 3 exceptions
                    log(f"  Exception {i+1}: {str(exc)}", "warning")

            return valid_results
