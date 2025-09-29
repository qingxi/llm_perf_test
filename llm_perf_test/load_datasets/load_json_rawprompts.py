import json
import os
from glob import glob

from llm_perf_test.load_datasets import LoadPrompts


class LoadPromptsFromRawPrompts(LoadPrompts):
    """Base class for loading prompts from a JSON file."""
    
    def __init__(self, dir_path: str):
        self.dir_path = dir_path
    
    def load_prompts(self):
        """Load all JSON files in a directory and extract the prompt from each."""

        json_files = glob(os.path.join(self.dir_path, "*.json"))
        prompts = []
        for json_file in json_files:
            with open(json_file, "r", encoding='utf-8') as file:
                request_json = json.loads(file.read())
            payload = request_json["messages"][0]["content"]
            prompts.append(payload)
        self.prompts = prompts