from abc import ABC, abstractmethod

class LoadPrompts(ABC):
    """Base class for loading prompts."""
    prompts: list[str] = []

    @abstractmethod
    def load_prompts(self):
        """Load and return a list of prompts."""
        pass