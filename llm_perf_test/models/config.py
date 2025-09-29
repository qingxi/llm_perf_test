import datetime
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from llm_perf_test.log import log


class Config(BaseSettings, case_sensitive=False):
    """Configuration for LLM performance testing"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_assignment=True,
        cli_parse_args=True
    )
    base_url: str = Field(default="",alias="LLM_URL", description="Base URL for the LLM API")
    api_key: str = Field(default="",alias="LLM_API_KEY", description="API key for authentication",exclude=True)
    model: str = Field(default="",alias="LLM_MODEL", description="Model name to use")
    api_version: str = Field(default="",alias="LLM_API_VERSION", description="API version (optional)")
    verify_ssl: bool = Field(default=False,alias="LLM_VERIFY_SSL", description="Verify SSL certificates")
    use_streaming: bool = Field(default=False,alias="LLM_USE_STREAMING", description="Use streaming responses")
    concurrent: int = Field(default=0,alias="LLM_CONCURRENT", description="Number of concurrent requests")
    request_delay_seconds: int = Field(default=0, alias="LLM_REQUEST_DELAY_SECONDS", description="Delay between requests")
    request_timeout: int = Field(default=6000, alias="LLM_REQUEST_TIMEOUT", description="Request timeout in milliseconds")
    use_common_prompt: bool = Field(default=False, alias="LLM_USE_COMMON_PROMPT", description="Use a common prompt for all requests")
    output_markdown_path: str = Field(default="", alias="LLM_OUTPUT_MARKDOWN_PATH", description="Path to save Markdown output")
    result_dir: str = Field(default="", alias="LLM_RESULT_DIR", description="Directory to save results")
    test_dataset_dir: str = Field(default="", alias="LLM_TEST_DATASET_DIR", description="Path to CSV file or json file with test prompts")
    
    def __init__(self, **data):
        super().__init__(**data)
        # Compute once to ensure consistent paths
        analysis_filename = f"analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if not self.output_markdown_path:
            self.output_markdown_path = os.path.join(self._setup_analysis_dir(), analysis_filename + ".md")
        if not self.result_dir:
            # Set result_dir to the directory where the module is running (current working directory)
            self.result_dir = self._setup_results_dir(subdir=analysis_filename)
        if not self.base_url:
            raise ValueError("Base URL must be provided")
        if not self.model:
            raise ValueError("Model name must be provided")

    def _setup_results_dir(self, subdir: str = "") -> str:
        """Return the directory where the module is running (current working directory).
        If a subdir is provided, return CWD/subdir; otherwise return CWD.
        """
        cwd = os.getcwd()
        result_dir = os.path.join(cwd, subdir) if subdir else cwd
        os.makedirs(result_dir, exist_ok=True)
        return result_dir

    def _setup_analysis_dir(self) -> str:  
        cwd = os.getcwd()
        analysis_dir = os.path.join(cwd, "analysis")
        os.makedirs(analysis_dir, exist_ok=True)
        return analysis_dir
    
    @property
    def llm_endpoint(self) -> str:
        """Construct the full LLM endpoint URL"""
        base_url_value = str(self.base_url)
        llm_url = f"{base_url_value.rstrip('/')}/chat/completions"
        if self.api_version:
            llm_url += f"?api-version={self.api_version}"
        return llm_url

    @property
    def llm_headers(self) -> dict:
        """Construct headers for LLM API requests"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["api-key"] = self.api_key
        return headers

    @property
    def markdown(self) -> str:
        """Generate a markdown representation of the configuration"""
        lines = [
            "### Test Configuration",
            "| Setting | Value |",
            "|---------|-------|"
        ]
        for k, v in self.model_dump().items():
            lines.append(f"| {k} | {v} |")
        return "\n".join(lines)

    
config = Config()
log(f"Configuration loaded: {config.model_dump()}", "info")