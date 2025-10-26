"""
CLLM - Command-Line LLM Toolkit

A bash-centric command-line interface for interacting with large language models
across multiple providers using a unified API.
"""

__version__ = "0.1.0"

from .client import LLMClient

__all__ = ["LLMClient"]
