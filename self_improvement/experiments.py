"""A/B Testing and performance experimentation framework"""
import time
from typing import Callable, Dict, Any

class ExperimentRunner:
    @staticmethod
    def benchmark(name: str, fn_a: Callable, fn_b: Callable, iterations: int = 50) -> Dict[str, Any]:
        start_a = time.time()
        for _ in range(iterations):
            fn_a()
        dur_a = time.time() - start_a

        start_b = time.time()
        for _ in range(iterations):
            fn_b()
        dur_b = time.time() - start_b

        winner = "A" if dur_a < dur_b else "B"
        return {
            "experiment": name,
            "duration_a": round(dur_a, 4),
            "duration_b": round(dur_b, 4),
            "winner": winner,
            "improvement_pct": round(abs(dur_a - dur_b) / max(dur_a, dur_b) * 100, 2)
        }
