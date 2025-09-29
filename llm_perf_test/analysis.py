from statistics import mean, median, stdev
from typing import List, Optional

from pydantic import BaseModel
from llm_perf_test.models import (
    config,
    PerformanceMetrics,
    Summary,
    TokensPerSecond,
    ResponseTimes,
    TimeToFirstToken
)

class Analysis(BaseModel):
    """Analysis of performance test results."""
    summary: Summary
    tokens_per_second: TokensPerSecond
    response_times: ResponseTimes
    time_to_first_token: TimeToFirstToken
    results: Optional[List[PerformanceMetrics]] = None  # Optional, store individual results

    @classmethod
    def from_results(cls, results: List[PerformanceMetrics]):
        """Create Analysis from a list of PerformanceMetrics and configuration"""
        tokens_per_second = [r.tokens_per_second for r in results]
        total_times = [r.total_time for r in results]
        completion_tokens = [r.completion_tokens for r in results]
        time_to_first_tokens = [r.time_to_first_token for r in results]
        
        total_tokens_generated = sum(completion_tokens)
        total_time_elapsed = sum(total_times)
        total_tokens = [r.total_tokens for r in results]
        total_tokens_sum = sum(total_tokens)
        total_reasoning_tokens = sum(r.reasoning_tokens for r in results)
        total_prompt_tokens = sum(r.prompt_tokens for r in results)

        # Calculate summary statistics
        summary = Summary(
            total_requests=len(results),
            successful_requests=len(results),
            total_tokens=total_tokens_sum,
            total_prompt_tokens=total_prompt_tokens,
            total_tokens_generated=total_tokens_generated,
            total_reasoning_tokens=total_reasoning_tokens,
            total_time_elapsed=round(total_time_elapsed, 2),
            average_tokens_per_request=round(mean(total_tokens), 2)
        )

        # Calculate tokens per second statistics
        tps_stats = TokensPerSecond(
            mean=round(mean(tokens_per_second), 2),
            median=round(median(tokens_per_second), 2),
            min=round(min(tokens_per_second), 2),
            max=round(max(tokens_per_second), 2),
            std_dev=round(stdev(tokens_per_second) if len(tokens_per_second) > 1 else 0, 2)
        )

        # Calculate response time statistics
        rt_stats = ResponseTimes(
            mean=round(mean(total_times), 2),
            median=round(median(total_times), 2),
            min=round(min(total_times), 2),
            max=round(max(total_times), 2),
            std_dev=round(stdev(total_times) if len(total_times) > 1 else 0, 2)
        )

        # Calculate time to first token statistics
        ttft_stats = TimeToFirstToken(
            mean=round(mean(time_to_first_tokens), 2),
            median=round(median(time_to_first_tokens), 2),
            min=round(min(time_to_first_tokens), 2),
            max=round(max(time_to_first_tokens), 2)
        )

        return cls(
            summary=summary,
            tokens_per_second=tps_stats,
            response_times=rt_stats,
            time_to_first_token=ttft_stats,
            results=results
        )
    
    def __print_table__(self) -> str:
        """Print table for each result"""
        headers = ["Request ID", "Total Tokens", "Prompt Tokens", "Completion Tokens", "Reasoning Tokens", "Total Time (s)", "Tokens/Sec", "Time to First Token (s)"]
        lines = [" | ".join(headers), "-" * 100]
        if not self.results:
            return "\n".join(lines)
        for r in self.results or []:
            line = f"{r.request_id} | {r.total_tokens} | {r.prompt_tokens} | {r.completion_tokens} | {r.reasoning_tokens} | {r.total_time:.2f} | {r.tokens_per_second:.2f} | {r.time_to_first_token:.2f}"
            lines.append(line)
        return "\n".join(lines)
    
    def to_markdown(self) -> str:
        """
        Return a full Markdown representation:
        - Detailed per-request table
        - Summary
        - Tokens/sec stats
        - Response time stats
        - Time to first token stats
        """
        lines: list[str] = []

        # --- NEW: configuration section ---
        if config:
            lines.append(config.markdown)
            lines.append("")  # blank line

        # Per-request table
        if self.results:
            lines.append("### Per-Request Metrics")
            headers = ["Request ID","Prompt size(KB)","Total tokens","Prompt tokens","Completion tokens","Reasoning tokens","Total Time (s)","Tokens/Sec","TTFT (s)"]
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("|" + "|".join(["---"] * len(headers)) + "|")
            for r in self.results or []:
                prompt_bytes = r.prompt.encode("utf-8")
                prompt_size_bytes = len(prompt_bytes)
                prompt_size_kb = round(prompt_size_bytes / 1024, 2)
                lines.append(f"| {r.request_id} | {prompt_size_kb} | {r.total_tokens} | {r.prompt_tokens} | {r.completion_tokens} | "
                             f"{r.reasoning_tokens} | {r.total_time:.2f} | {r.tokens_per_second:.2f} | {r.time_to_first_token:.2f} |")
            lines.append("")

        # Helper to dump any dataclass as a two‑column table
        def dc_table(title: str, obj) -> list[str]:
            block = [f"### {title}", "| Metric | Value |", "|---|---|"]
            data = obj.model_dump() if hasattr(obj, "model_dump") else getattr(obj, "dict", {})
            for k, v in data.items():
                name = k.replace("_", " ").title()
                block.append(f"| {name} | {v} |")
            block.append("")
            return block

        lines.extend(dc_table("Summary", self.summary))
        lines.extend(dc_table("Tokens / Second Stats", self.tokens_per_second))
        lines.extend(dc_table("Response Time Stats (s)", self.response_times))
        lines.extend(dc_table("Time To First Token (s)", self.time_to_first_token))

        return "\n".join(lines)

    def __str__(self) -> str:
        """String representation of the Analysis instance."""
        return f"{self.__print_table__()}\n{self.summary}\n{self.tokens_per_second}\n{self.response_times}\n{self.time_to_first_token}"
