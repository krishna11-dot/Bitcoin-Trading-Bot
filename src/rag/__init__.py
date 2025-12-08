"""
RAG System for Market Pattern Matching

PURPOSE:
    Natural language pattern matching for historical market conditions.
    NOT for reading CSV files (use pandas for that).

USE CASES:
    - Find similar historical market patterns
    - Provide context for LLM responses
    - Pattern matching: "What happened last time BTC was at this price?"

NOT FOR:
    - Reading structured CSV data (wrong tool)
    - Extracting tabular data (use pandas/SQL instead)
"""

from src.rag.rag_system import RAGSystem

__all__ = ['RAGSystem']
