"""
Services module for ERP Copilot framework.
Contains LLM integration and knowledge base services.
"""

from .llm_client import LLMClient
from .knowledge_base import KnowledgeBaseManager

__all__ = ['LLMClient', 'KnowledgeBaseManager']
