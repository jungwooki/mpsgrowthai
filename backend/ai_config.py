"""Shared AI configuration for status, extraction, and interpretation."""
import os


def model_name():
    return (os.getenv('OPENAI_MODEL') or '').strip() or 'gpt-4.1'
