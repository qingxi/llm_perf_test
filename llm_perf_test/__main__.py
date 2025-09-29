import asyncio
import os
import aiohttp

from llm_perf_test import Analysis, LLMPerformanceTester, log
from llm_perf_test.load_datasets import LoadPromptsFromCsv, LoadPromptsFromRawPrompts
from llm_perf_test.models import config


async def main():
    """Main function to run the performance tests."""
    dir_path = os.path.join(config.test_dataset_dir)
    loader = (LoadPromptsFromRawPrompts(dir_path) if not config.use_common_prompt else LoadPromptsFromCsv(dir_path))

    loader.load_prompts()

    test_prompts = loader.prompts

    if not test_prompts:
        log("No test prompts found. Please add prompt files in the 'datasets' directory.")
        return

    log(f"Loaded {len(test_prompts)} prompts for testing.")

    # Initialize tester
    tester = LLMPerformanceTester(
        base_url=config.base_url,
        api_key=config.api_key,
        model=config.model,
        result_dir=config.result_dir,
        api_version=config.api_version,
        verify_ssl=config.verify_ssl
    )

    log("Starting LLM Performance Test...")
    log(f"Endpoint: {config.base_url}")
    log(f"Model: {config.model}")
    log(f"SSL Verification: {config.verify_ssl}")
    log(f"Using Streaming: {config.use_streaming}")
    log("-" * 50)

    # Test 1: Sequential Requests
    log("Test 1: Sequential Requests")
    results = []
    for i, prompt in enumerate(test_prompts):
        log(f"  Request {i + 1}/{len(test_prompts)}...")
        log(f"    Prompt: {prompt.replace('\n', ' ')[:30]}...")
        try:
            # Create SSL context and connector with SSL verification settings
            ssl_context = tester.get_ssl_context()
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=config.request_timeout)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout,) as session:
                result = await tester.single_request(session, prompt, use_streaming=config.use_streaming)
                results.append(result)
                log(f"    ✓ {result.tokens_per_second:.2f} tokens/sec")
                if config.request_delay_seconds > 0:
                    log(f"    ⏱ Sleeping {config.request_delay_seconds} seconds before next request...")
                    await asyncio.sleep(config.request_delay_seconds)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            log(f"    ✗ Request Error: {str(e)}","error")

    if results:
        analysis = Analysis.from_results(results)
        log(f"Sequential Test Results:{analysis}")
        md = analysis.to_markdown()
        log(f"Markdown Output:\n{md}")
        if config.output_markdown_path:
            with open(config.output_markdown_path, "w", encoding='utf-8') as f:
                f.write(md)
            log(f"Markdown saved to {config.output_markdown_path}")
    if config.concurrent>0:
        # Test 2: Concurrent requests
        log(f"Test 2: Concurrent Requests ({config.concurrent})")
        try:
            concurrent_results = await tester.concurrent_test(
                test_prompts * 2,  # 2 requests total
                concurrent_requests=config.concurrent,
                request_timeout=config.request_timeout,
                use_streaming=config.use_streaming
            )
            
            if concurrent_results:
                concurrent_analysis = Analysis.from_results(concurrent_results)
                log(f"Concurrent Test Results:{concurrent_analysis}")
                md = concurrent_analysis.to_markdown()
                log(f"Markdown Output:\n{md}")
                if config.output_markdown_path:
                    base, ext = os.path.splitext(config.output_markdown_path)
                    concurrent_path = f"{base}_concurrent{ext}"
                    with open(concurrent_path, "w", encoding='utf-8') as f:
                        f.write(md)
                    log(f"Markdown saved to {concurrent_path}")
        
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            log(f"Concurrent test failed: {str(e)}", "error")
        
    log("Performance test completed!")


if __name__ == "__main__":
    # Run the performance test with the global cfg loaded from pydantic BaseSettings (.env + CLI)
    asyncio.run(main())