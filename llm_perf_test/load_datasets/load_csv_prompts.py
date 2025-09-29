import csv
import os
from glob import glob

from llm_perf_test.load_datasets import LoadPrompts

class LoadPromptsFromCsv(LoadPrompts):
    """Class for loading prompts from CSV files."""
    
    def __init__(self, dir_path: str):
        self.dir_path = dir_path
        self.column_index = 2
        self.has_header = True

    def load_prompts(self):
        """
        Read all CSV files in the directory and return the values from the specified column (0-based).
        column_index=2 => third column.
        """

        prompts: list[str] = []
        csv_files = glob(os.path.join(self.dir_path, "*.csv"))
        for csv_file in csv_files:
            with open(csv_file, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                if self.has_header:
                    next(reader, None)
                for row in reader:
                    if len(row) > self.column_index:
                        val = row[self.column_index].strip()
                        if val:
                            prompts.append(val)
        self.prompts = prompts