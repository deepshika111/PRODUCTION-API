"""
Monitoring and Logging for Production
Structured logging, metrics, and alerts
"""

import logging
import json
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable


class JSONFormatter (logging.Formatter):
    def format (self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }


        if hasattr(record, "extra_data"):
            log_obj.update(record.extra_data)
        return json.dumps(log_obj)



    def get_logger (name:str = 'production-api') :

        """ Creating a JSON Logger """

        logger = logging.getLogger (name)

        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter (JSONFormatter())
            logger.addHandler (handler)
            logger.setLevel (logging.INFO)

        return logger


class MetricsCollector:
    """Collect and aggregate metrics."""

    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "errors_total": 0,
            "latency_sum": 0,
            "latency_count": 0,
            "tokens_input": 0,
            "tokens_output": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def record_request(
        self,
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        error: bool = False,
        cache_hit: bool = False,
    ):
        self.metrics["requests_total"] += 1
        self.metrics["latency_sum"] += latency_ms
        self.metrics["latency_count"] += 1
        self.metrics["tokens_input"] += input_tokens
        self.metrics["tokens_output"] += output_tokens

        if error:
            self.metrics["errors_total"] += 1

        if cache_hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1

    def get_summary(self) -> dict:
        avg_latency = (
            self.metrics["latency_sum"] / self.metrics["latency_count"]
            if self.metrics["latency_count"] > 0
            else 0
        )
        error_rate = (
            self.metrics["errors_total"] / self.metrics["requests_total"]
            if self.metrics["requests_total"] > 0
            else 0
        )
        cache_hit_rate = (
            self.metrics["cache_hits"]
            / (self.metrics["cache_hits"] + self.metrics["cache_misses"])
            if (self.metrics["cache_hits"] + self.metrics["cache_misses"]) > 0
            else 0
        )

        return {
            "total_requests": self.metrics["requests_total"],
            "total_errors": self.metrics["errors_total"],
            "error_rate": f"{error_rate:.2%}",
            "avg_latency_ms": round(avg_latency, 2),
            "total_input_tokens": self.metrics["tokens_input"],
            "total_output_tokens": self.metrics["tokens_output"],
            "cache_hit_rate": f"{cache_hit_rate:.2%}",
        }

if __name__ == "__main__":
    from app.monitoring import get_logger, MetricsCollector, RequestTimer
    import time
    import json

    logger = get_logger()
    metrics = MetricsCollector()

    print('=== STRUCTURED LOGGING ===')
    print()
    logger.info('Application starting')
    logger.info('Processing request', extra={'extra_data': {'user_id': 'user-123', 'thread_id': 1}})
    logger.warning('Rate limit approaching', extra={'extra_data': {'current_rate': 18, 'limit': 20}})
    print()

    # Simulate some requests
    with RequestTimer() as timer:
        time.sleep(0.1)  # simulate work
    metrics.record_request(latency_ms=timer.elapsed_ms, input_tokens=50, output_tokens=100, cache_hit=False)
    print(f'Request 1: {timer.elapsed_ms:.1f}ms')

    with RequestTimer() as timer:
        time.sleep(0.05)
    metrics.record_request(latency_ms=timer.elapsed_ms, input_tokens=30, output_tokens=80, cache_hit=True)
    print(f'Request 2: {timer.elapsed_ms:.1f}ms (cache hit)')

    metrics.record_request(latency_ms=5.0, input_tokens=0, output_tokens=0, error=True)
    print('Request 3: error')

    print()
    print('=== METRICS SUMMARY ===')
    print(json.dumps(metrics.get_summary(), indent=2))




