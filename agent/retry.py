"""Retry policies with exponential backoff for agent tasks"""
import time

class RetryPolicy:
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay

    def should_retry(self, attempt: int) -> bool:
        return attempt < self.max_attempts

    def delay_for(self, attempt: int) -> float:
        return self.base_delay * (2 ** (attempt - 1))
