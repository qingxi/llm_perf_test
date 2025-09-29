
from pydantic import BaseModel

class Summary(BaseModel):
    """Summary of performance test results."""
    total_requests: int
    successful_requests: int
    total_tokens: int  # input + output
    total_prompt_tokens: int
    total_tokens_generated: int
    total_reasoning_tokens: int
    total_time_elapsed: float
    average_tokens_per_request: float

    def __str__(self) -> str:
        """String representation of the Summary instance."""
        lines = ["Summary:", "-" * 40]
        for field in self.model_dump():
            display_name = field.replace('_', ' ').title()
            lines.append(f"{display_name}: {self.model_dump()[field]}")
        lines.append("-" * 40)
        return "\n".join(lines)

class TokensPerSecond(BaseModel):
    """Statistics for tokens processed per second."""
    mean: float
    median: float
    min: float
    max: float
    std_dev: float

    def __str__(self) -> str:
        """String representation of the TokensPerSecond instance."""
        lines = ["Tokens Per Second:", "-" * 40]
        for field in self.model_dump():
            display_name = field.replace('_', ' ').title()
            lines.append(f"{display_name}: {self.model_dump()[field]}")
        lines.append("-" * 40)
        return "\n".join(lines)


class ResponseTimes(BaseModel):
    """Statistics for response times."""
    mean: float
    median: float
    min: float
    max: float
    std_dev: float

    def __str__(self) -> str:
        """String representation of the ResponseTimes instance."""
        lines = ["Response Times (s):", "-" * 40]
        for field in self.model_dump():
            display_name = field.replace('_', ' ').title()
            lines.append(f"{display_name}: {self.model_dump()[field]}")
        lines.append("-" * 40)
        return "\n".join(lines)

class TimeToFirstToken(BaseModel):
    """Statistics for time to first token."""
    mean: float
    median: float
    min: float
    max: float

    def __str__(self) -> str:
        """String representation of the TimeToFirstToken instance."""
        lines = ["Time To First Token (s):", "-" * 40]
        for field in self.model_dump():
            display_name = field.replace('_', ' ').title()
            lines.append(f"{display_name}: {self.model_dump()[field]}")
        lines.append("-" * 40)
        return "\n".join(lines)