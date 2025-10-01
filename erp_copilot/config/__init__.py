"""
Configuration module for ERP Copilot framework.
Contains LLM settings and endpoint configurations.
"""

from .llm_config import LLMConfig
from .erp_endpoints import ERP_ENDPOINTS, ACTION_MAPPINGS

__all__ = ['LLMConfig', 'ERP_ENDPOINTS', 'ACTION_MAPPINGS']
