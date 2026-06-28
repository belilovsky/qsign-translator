from __future__ import annotations

import argparse
from statistics import mean
from time import perf_counter

from qsign_translator import SignPlanner
from qsign_translator.lexicon import load_default_lexicon

DEFAULT_CASES = [
    "Привет Александр",
    "Мне нужна помощь",
    "Сәлеметсіз бе көмек керек",
    "salam dostar",
    "Hello мен керек",
    "Спасибо большое",
]


def run_benchmark(iterations: int, warmup: int) -> None:
    planner = SignPlanner(load_default_lexicon())

    for _ in range(max(0, warmup)):
        for text in DEFAULT_CASES:
            planner.plan(text)

    durations_ms: list[float] = []
    for _ in range(max(1, iterations)):
        started = perf_counter()
        for text in DEFAULT_CASES:
            planner.plan(text)
        durations_ms.append((perf_counter() - started) * 1000)

    total_cases = len(DEFAULT_CASES) * max(1, iterations)
    print(f"cases={len(DEFAULT_CASES)} iterations={iterations} total_runs={total_cases}")
    print(f"batch_ms_avg={mean(durations_ms):.3f}")
    print(f"batch_ms_min={min(durations_ms):.3f}")
    print(f"batch_ms_max={max(durations_ms):.3f}")
    print(f"per_case_ms_avg={mean(durations_ms) / len(DEFAULT_CASES):.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Micro-benchmark the planner core.")
    parser.add_argument("--iterations", type=int, default=5000, help="Measured benchmark loops.")
    parser.add_argument("--warmup", type=int, default=500, help="Warmup loops before measuring.")
    args = parser.parse_args()
    run_benchmark(iterations=args.iterations, warmup=args.warmup)


if __name__ == "__main__":
    main()
