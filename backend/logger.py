"""
Logging and observability utilities
"""
import logging
import sys
from datetime import datetime
from typing import Any, Dict
from backend.config import settings


class StructuredLogger:
    """Structured logging for better observability"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure logger with structured format"""
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(getattr(logging, settings.log_level))
    
    def info(self, message: str, **context):
        """Log info with context"""
        self._log(logging.INFO, message, context)
    
    def error(self, message: str, **context):
        """Log error with context"""
        self._log(logging.ERROR, message, context)
    
    def warning(self, message: str, **context):
        """Log warning with context"""
        self._log(logging.WARNING, message, context)
    
    def debug(self, message: str, **context):
        """Log debug with context"""
        self._log(logging.DEBUG, message, context)
    
    def _log(self, level: int, message: str, context: Dict[str, Any]):
        """Internal method to log with context"""
        context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
        full_message = f"{message} | {context_str}" if context_str else message
        self.logger.log(level, full_message)


def get_logger(name: str) -> StructuredLogger:
    """Factory function to get logger instances"""
    return StructuredLogger(name)
