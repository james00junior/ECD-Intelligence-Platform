#!/usr/bin/env python3
"""
Compare local Ollama models for analytics query planning.

Examples:
    # Benchmark installed models only (no download):
    uv run python scripts/compare_planner_models.py --suite extended --details

    # Explicitly compare Qwen vs Llama (both must already be installed):
    uv run python scripts/compare_planner_models.py \\
        --suite extended \\
        --models qwen3.5:0.8b llama3.1:8b \\
        --details

    # Only download if you explicitly opt in:
    uv run python scripts/compare_planner_models.py --models phi4-mini --pull
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass

from app.config.benchmark_suites import SUITES, BenchmarkCase
from app.config.local_models import (
    DEFAULT_BENCHMARK_MODELS,
    RECOMMENDED_PLANNER_MODELS,
)
from app.config.settings import get_settings
from app.services.llm_query_planner import build_llm_query_plan
from langchain_ollama import ChatOllama


@dataclass
class CaseResult:
    question: str
    expected_intent: str | None
    predicted_intent: str | None
    category: str
    notes: str
    correct: bool
    latency_ms: float
    error: str | None = None


@dataclass
class ModelResult:
    model: str
    installed: bool
    pulled: bool
    cases: list[CaseResult]
    accuracy: float
    supported_accuracy: float
    advanced_accuracy: float
    avg_latency_ms: float
    errors: int


def _ollama_base_url() -> str:
    return get_settings().ollama_base_url.rstrip("/")


def _list_installed_models() -> set[str]:
    request = urllib.request.Request(f"{_ollama_base_url()}/api/tags")

    with urllib.request.urlopen(request, timeout=5) as response:
        payload = json.load(response)

    names: set[str] = set()

    for model in payload.get("models", []):
        names.add(model["name"])

        if ":" in model["name"]:
            names.add(model["name"].split(":", 1)[0])

    return names


def _pull_model(model: str) -> None:
    body = json.dumps({"name": model, "stream": True}).encode("utf-8")
    request = urllib.request.Request(
        f"{_ollama_base_url()}/api/pull",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    print(f"Pulling {model}...")

    with urllib.request.urlopen(request, timeout=3600) as response:
        while True:
            line = response.readline()

            if not line:
                break

            status = json.loads(line.decode("utf-8")).get("status")

            if status:
                print(f"  {status}", end="\r")

    print(f"\n  {model} ready")


def _model_installed(model: str, installed: set[str]) -> bool:
    if model in installed:
        return True

    base = model.split(":", 1)[0]

    return any(
        name == model or name.startswith(f"{base}:")
        for name in installed
    )


def _evaluate_model(
    model: str,
    suite: tuple[BenchmarkCase, ...],
) -> ModelResult:
    cases: list[CaseResult] = []

    llm = ChatOllama(
        model=model,
        base_url=_ollama_base_url(),
        temperature=0,
    )

    for item in suite:
        started = time.perf_counter()
        error = None
        predicted_intent = None

        try:
            plan = build_llm_query_plan(item.question, llm=llm)
            predicted_intent = plan.intent if plan else None
        except Exception as exc:
            error = str(exc)

        latency_ms = (time.perf_counter() - started) * 1000
        correct = predicted_intent == item.expected_intent

        cases.append(
            CaseResult(
                question=item.question,
                expected_intent=item.expected_intent,
                predicted_intent=predicted_intent,
                category=item.category,
                notes=item.notes,
                correct=correct,
                latency_ms=latency_ms,
                error=error,
            )
        )

    accuracy = sum(1 for case in cases if case.correct) / len(cases)

    supported = [
        case for case in cases if case.category in {"supported", "paraphrase"}
    ]
    advanced = [case for case in cases if case.category == "advanced"]

    supported_accuracy = (
        sum(1 for case in supported if case.correct) / len(supported)
        if supported
        else 0.0
    )
    advanced_accuracy = (
        sum(1 for case in advanced if case.correct) / len(advanced)
        if advanced
        else 0.0
    )
    avg_latency_ms = sum(case.latency_ms for case in cases) / len(cases)
    errors = sum(1 for case in cases if case.error)

    return ModelResult(
        model=model,
        installed=True,
        pulled=False,
        cases=cases,
        accuracy=accuracy,
        supported_accuracy=supported_accuracy,
        advanced_accuracy=advanced_accuracy,
        avg_latency_ms=avg_latency_ms,
        errors=errors,
    )


def _print_catalog() -> None:
    print("Recommended local planner models:\n")

    for spec in RECOMMENDED_PLANNER_MODELS:
        print(f"  {spec.ollama_tag:16}  {spec.approx_size:8}  {spec.description}")

        if spec.hf_name:
            print(f"  {'':16}  HF: {spec.hf_name}")

        print()


def _print_summary(results: list[ModelResult]) -> None:
    print("\nSummary")
    print("-" * 88)
    print(
        f"{'Model':20} {'Overall':>10} {'Supported':>12} "
        f"{'Advanced':>12} {'Avg ms':>10} {'Errors':>8}"
    )
    print("-" * 88)

    for result in sorted(
        results,
        key=lambda item: (-item.accuracy, item.avg_latency_ms),
    ):
        if not result.installed:
            print(f"{result.model:20} {'skipped (not installed)':>58}")
            continue

        print(
            f"{result.model:20} "
            f"{result.accuracy:>9.0%} "
            f"{result.supported_accuracy:>11.0%} "
            f"{result.advanced_accuracy:>11.0%} "
            f"{result.avg_latency_ms:>10.0f} "
            f"{result.errors:>8}"
        )

    print("-" * 88)


def _print_details(results: list[ModelResult]) -> None:
    for result in results:
        if not result.installed:
            continue

        print(f"\n{result.model}")
        print("-" * len(result.model))

        for case in result.cases:
            status = "OK" if case.correct else "MISS"

            if case.error:
                status = "ERR"

            print(
                f"[{status}] [{case.category}] "
                f"expected={case.expected_intent!r} "
                f"got={case.predicted_intent!r} "
                f"({case.latency_ms:.0f} ms)"
            )
            print(f"      Q: {case.question}")

            if case.notes:
                print(f"      Note: {case.notes}")

            if case.error:
                print(f"      E: {case.error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark Ollama models for analytics query planning.",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["llama3.1:8b", "qwen3.5:0.8b"],
        help="Ollama model tags to benchmark (default: llama3.1:8b vs qwen3.5:0.8b)",
    )
    parser.add_argument(
        "--suite",
        choices=sorted(SUITES),
        default="extended",
        help="Question suite to run",
    )
    parser.add_argument(
        "--pull",
        action="store_true",
        help="Pull missing models before benchmarking",
    )
    parser.add_argument(
        "--catalog",
        action="store_true",
        help="Print recommended model catalog and exit",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Print per-question results",
    )

    args = parser.parse_args(argv)

    if args.catalog:
        _print_catalog()
        return 0

    suite = SUITES[args.suite]

    try:
        installed = _list_installed_models()
    except urllib.error.URLError as exc:
        print(
            "Could not reach Ollama. Start it first "
            f"({get_settings().ollama_base_url}).",
            file=sys.stderr,
        )
        print(exc, file=sys.stderr)
        return 1

    print(f"Running {args.suite} suite ({len(suite)} questions)")

    results: list[ModelResult] = []

    for model in args.models:
        if not _model_installed(model, installed):
            if not args.pull:
                print(
                    f"Skipping {model}: not installed. "
                    f"Run: ollama pull {model}",
                    file=sys.stderr,
                )
                results.append(
                    ModelResult(
                        model=model,
                        installed=False,
                        pulled=False,
                        cases=[],
                        accuracy=0.0,
                        supported_accuracy=0.0,
                        advanced_accuracy=0.0,
                        avg_latency_ms=0.0,
                        errors=0,
                    )
                )
                continue

            _pull_model(model)
            installed = _list_installed_models()

        print(f"\nBenchmarking {model}...")
        results.append(_evaluate_model(model, suite))

    if args.json:
        print(
            json.dumps(
                [asdict(result) for result in results],
                indent=2,
            )
        )
    else:
        _print_summary(results)

        if args.details:
            _print_details(results)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
