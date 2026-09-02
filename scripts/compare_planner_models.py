#!/usr/bin/env python3
"""
Compare local Ollama models for analytics query planning and text-to-SQL.

Examples:
    uv run python scripts/compare_planner_models.py --pull --details \\
        --write docs/phase5-model-benchmark.md

    uv run python scripts/compare_planner_models.py --catalog
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
import urllib.error
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from langchain_ollama import ChatOllama

from app.config.benchmark_suites import (
    SUITES,
    TEXT_TO_SQL_SUITE,
    BenchmarkCase,
    SqlBenchmarkCase,
)
from app.config.local_models import (
    DEFAULT_BENCHMARK_MODELS,
    RECOMMENDED_PLANNER_MODELS,
)
from app.config.settings import get_settings
from app.services.llm_query_planner import build_llm_query_plan
from app.services.ollama_client import (
    list_installed_models,
    model_installed,
    ollama_base_url,
    pull_model,
)
from app.services.sql_guard import referenced_tables, validate_generated_sql
from app.services.text_to_sql import generate_select


JHB = ZoneInfo("Africa/Johannesburg")


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
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None


@dataclass
class SqlCaseResult:
    question: str
    organisation_id: int | None
    valid_select: bool
    org_scoped: bool | None
    tables_ok: bool
    executed: bool
    row_count: int | None
    latency_ms: float
    sql: str | None
    error: str | None = None
    notes: str = ""
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None


@dataclass
class ModelResult:
    model: str
    installed: bool
    pulled: bool
    cases: list[CaseResult]
    sql_cases: list[SqlCaseResult] = field(default_factory=list)
    accuracy: float = 0.0
    supported_accuracy: float = 0.0
    advanced_accuracy: float = 0.0
    sql_validity: float = 0.0
    sql_org_scope: float = 0.0
    avg_latency_ms: float = 0.0
    sql_avg_latency_ms: float = 0.0
    errors: int = 0
    total_prompt_tokens: int | None = None
    total_completion_tokens: int | None = None
    total_cost_usd: float | None = None


def _hardware_notes() -> str:
    parts = [platform.platform(), platform.machine()]
    try:
        brand = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            text=True,
            timeout=2,
        ).strip()
        mem = int(
            subprocess.check_output(
                ["sysctl", "-n", "hw.memsize"],
                text=True,
                timeout=2,
            ).strip()
        )
        parts.append(brand)
        parts.append(f"{mem / (1024 ** 3):.0f} GB RAM")
    except Exception:
        pass
    return " · ".join(part for part in parts if part)


def _sum_tokens(values: list[int | None]) -> int | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present)


def _evaluate_intent(
    model: str,
    suite: tuple[BenchmarkCase, ...],
) -> list[CaseResult]:
    cases: list[CaseResult] = []
    llm = ChatOllama(
        model=model,
        base_url=ollama_base_url(),
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
        cases.append(
            CaseResult(
                question=item.question,
                expected_intent=item.expected_intent,
                predicted_intent=predicted_intent,
                category=item.category,
                notes=item.notes,
                correct=predicted_intent == item.expected_intent,
                latency_ms=latency_ms,
                error=error,
            )
        )
    return cases


def _evaluate_sql(
    model: str,
    suite: tuple[SqlBenchmarkCase, ...],
    *,
    execute: bool,
) -> list[SqlCaseResult]:
    from langchain_ollama import ChatOllama as _ChatOllama

    llm = _ChatOllama(
        model=model,
        base_url=ollama_base_url(),
        temperature=0,
    )
    results: list[SqlCaseResult] = []

    for item in suite:
        started = time.perf_counter()
        generated = generate_select(
            item.question,
            organisation_id=item.organisation_id,
            llm=llm,
        )
        latency_ms = (time.perf_counter() - started) * 1000

        prompt_tokens = None
        completion_tokens = None
        cost_usd = None
        if generated is not None and generated.usages:
            prompt_tokens = _sum_tokens([u.prompt_tokens for u in generated.usages])
            completion_tokens = _sum_tokens(
                [u.completion_tokens for u in generated.usages]
            )
            costs = [u.cost_usd for u in generated.usages if u.cost_usd is not None]
            cost_usd = sum(costs) if costs else 0.0

        if generated is None:
            results.append(
                SqlCaseResult(
                    question=item.question,
                    organisation_id=item.organisation_id,
                    valid_select=False,
                    org_scoped=None,
                    tables_ok=False,
                    executed=False,
                    row_count=None,
                    latency_ms=latency_ms,
                    sql=None,
                    error="generation returned None",
                    notes=item.notes,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost_usd=cost_usd,
                )
            )
            continue

        valid_select = False
        org_scoped: bool | None = None
        tables_ok = True
        error = None
        try:
            sql = validate_generated_sql(
                generated.sql,
                organisation_id=item.organisation_id,
            )
            valid_select = True
            if item.must_include_org_filter:
                org_scoped = ":organisation_id" in sql
                if not org_scoped:
                    tables_ok = False
                    error = "missing organisation_id bind parameter"
            tables = referenced_tables(sql)
            missing = [name for name in item.expected_tables if name not in tables]
            if missing:
                tables_ok = False
                extra = f"missing tables: {', '.join(missing)}"
                error = f"{error}; {extra}" if error else extra
        except Exception as exc:
            sql = generated.sql
            error = str(exc)
            org_scoped = False if item.must_include_org_filter else None

        executed = False
        row_count = None
        if execute and valid_select and error is None:
            try:
                from app.tools.sql_tool import execute_sql

                rows = execute_sql(generated.sql, generated.parameters)
                executed = True
                row_count = len(rows)
            except Exception as exc:
                error = f"execution failed: {exc}"

        results.append(
            SqlCaseResult(
                question=item.question,
                organisation_id=item.organisation_id,
                valid_select=valid_select and error is None,
                org_scoped=org_scoped,
                tables_ok=tables_ok and (error is None or "missing tables" not in (error or "")),
                executed=executed,
                row_count=row_count,
                latency_ms=latency_ms,
                sql=generated.sql,
                error=error,
                notes=item.notes,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd,
            )
        )
    return results


def _summarise_model(
    model: str,
    pulled: bool,
    cases: list[CaseResult],
    sql_cases: list[SqlCaseResult],
) -> ModelResult:
    accuracy = sum(1 for case in cases if case.correct) / len(cases) if cases else 0.0
    supported = [case for case in cases if case.category in {"supported", "paraphrase"}]
    advanced = [case for case in cases if case.category == "advanced"]
    supported_accuracy = (
        sum(1 for case in supported if case.correct) / len(supported) if supported else 0.0
    )
    advanced_accuracy = (
        sum(1 for case in advanced if case.correct) / len(advanced) if advanced else 0.0
    )
    sql_validity = (
        sum(1 for case in sql_cases if case.valid_select) / len(sql_cases)
        if sql_cases
        else 0.0
    )
    org_cases = [case for case in sql_cases if case.org_scoped is not None]
    sql_org_scope = (
        sum(1 for case in org_cases if case.org_scoped) / len(org_cases)
        if org_cases
        else 0.0
    )
    avg_latency_ms = (
        sum(case.latency_ms for case in cases) / len(cases) if cases else 0.0
    )
    sql_avg_latency_ms = (
        sum(case.latency_ms for case in sql_cases) / len(sql_cases) if sql_cases else 0.0
    )
    prompt_tokens = _sum_tokens(
        [case.prompt_tokens for case in cases]
        + [case.prompt_tokens for case in sql_cases]
    )
    completion_tokens = _sum_tokens(
        [case.completion_tokens for case in cases]
        + [case.completion_tokens for case in sql_cases]
    )
    cost_values = [
        case.cost_usd
        for case in [*cases, *sql_cases]
        if case.cost_usd is not None
    ]
    total_cost = sum(cost_values) if cost_values else None

    return ModelResult(
        model=model,
        installed=True,
        pulled=pulled,
        cases=cases,
        sql_cases=sql_cases,
        accuracy=accuracy,
        supported_accuracy=supported_accuracy,
        advanced_accuracy=advanced_accuracy,
        sql_validity=sql_validity,
        sql_org_scope=sql_org_scope,
        avg_latency_ms=avg_latency_ms,
        sql_avg_latency_ms=sql_avg_latency_ms,
        errors=sum(1 for case in cases if case.error)
        + sum(1 for case in sql_cases if case.error),
        total_prompt_tokens=prompt_tokens,
        total_completion_tokens=completion_tokens,
        total_cost_usd=total_cost,
    )


def _print_catalog() -> None:
    print("Recommended local planner models:\n")
    for spec in RECOMMENDED_PLANNER_MODELS:
        print(f"  {spec.ollama_tag:16}  {spec.approx_size:8}  {spec.description}")
        if spec.hf_name:
            print(f"  {'':16}  HF: {spec.hf_name}")
        print()


def _print_summary(results: list[ModelResult]) -> None:
    print("\nIntent classification")
    print("-" * 100)
    print(
        f"{'Model':20} {'Overall':>10} {'Supported':>12} "
        f"{'Advanced':>12} {'Avg ms':>10} {'Errors':>8}"
    )
    print("-" * 100)
    for result in sorted(results, key=lambda item: (-item.accuracy, item.avg_latency_ms)):
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
    print("-" * 100)

    if any(result.sql_cases for result in results):
        print("\nText-to-SQL")
        print("-" * 88)
        print(
            f"{'Model':20} {'Valid SELECT':>14} {'Org scope':>12} "
            f"{'Avg ms':>10} {'Errors':>8}"
        )
        print("-" * 88)
        for result in sorted(
            results, key=lambda item: (-item.sql_validity, item.sql_avg_latency_ms)
        ):
            if not result.installed or not result.sql_cases:
                continue
            print(
                f"{result.model:20} "
                f"{result.sql_validity:>13.0%} "
                f"{result.sql_org_scope:>11.0%} "
                f"{result.sql_avg_latency_ms:>10.0f} "
                f"{sum(1 for case in result.sql_cases if case.error):>8}"
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
                f"[intent {status}] [{case.category}] "
                f"expected={case.expected_intent!r} "
                f"got={case.predicted_intent!r} "
                f"({case.latency_ms:.0f} ms)"
            )
            print(f"      Q: {case.question}")
            if case.error:
                print(f"      E: {case.error}")
        for case in result.sql_cases:
            status = "OK" if case.valid_select else "FAIL"
            print(
                f"[sql {status}] org={case.organisation_id!r} "
                f"({case.latency_ms:.0f} ms)"
            )
            print(f"      Q: {case.question}")
            if case.sql:
                compact = " ".join(case.sql.split())
                print(f"      SQL: {compact[:240]}")
            if case.error:
                print(f"      E: {case.error}")


def _recommend(results: list[ModelResult]) -> str | None:
    ranked = [
        result
        for result in results
        if result.installed and result.cases
    ]
    if not ranked:
        return None
    ranked.sort(
        key=lambda item: (
            -(item.accuracy * 0.6 + item.sql_validity * 0.4),
            item.avg_latency_ms,
        )
    )
    return ranked[0].model


def _render_markdown(
    *,
    results: list[ModelResult],
    suite_name: str,
    hardware: str,
    pulled: list[str],
    execute_sql: bool,
    blocked: str | None,
) -> str:
    now = datetime.now(JHB)
    recommend = _recommend(results)
    lines = [
        "# Phase 5 local model benchmark",
        "",
        f"- Date: {now.strftime('%-d %b %Y, %H:%M')} SAST (Africa/Johannesburg)",
        f"- Hardware: {hardware}",
        f"- Intent suite: `{suite_name}` ({len(SUITES[suite_name])} questions)",
        f"- Text-to-SQL suite: {len(TEXT_TO_SQL_SUITE)} questions",
        f"- Models requested: {', '.join(result.model for result in results) or 'none'}",
        f"- Models pulled this run: {', '.join(pulled) or 'none'}",
        f"- Live SQL execution against Postgres: {'yes' if execute_sql else 'no'}",
        "- Numbers are from a live Ollama run on this machine; they are not estimates."
        if blocked is None
        else f"- Live run blocked: {blocked}",
        "",
        "## Recommendation",
        "",
    ]
    if recommend:
        lines.append(
            f"**Default local planner model: `{recommend}`** — best combined "
            "intent accuracy and text-to-SQL validity among the models that ran, "
            "with latency as the tie-breaker."
        )
    else:
        lines.append("No model completed the suite in this run.")
    lines.extend(["", "## Intent classification", ""])
    lines.append("| Model | Overall | Supported / paraphrase | Advanced | Avg latency (ms) | Errors |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for result in results:
        if not result.installed:
            lines.append(f"| `{result.model}` | skipped (not installed) | | | | |")
            continue
        lines.append(
            f"| `{result.model}` | {result.accuracy:.0%} | "
            f"{result.supported_accuracy:.0%} | {result.advanced_accuracy:.0%} | "
            f"{result.avg_latency_ms:.0f} | {sum(1 for case in result.cases if case.error)} |"
        )

    if any(result.sql_cases for result in results):
        lines.extend(["", "## Text-to-SQL", ""])
        lines.append(
            "| Model | Valid SELECT | Org-scope when required | Avg latency (ms) | Executed | Errors |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|")
        for result in results:
            if not result.installed or not result.sql_cases:
                continue
            executed = sum(1 for case in result.sql_cases if case.executed)
            lines.append(
                f"| `{result.model}` | {result.sql_validity:.0%} | "
                f"{result.sql_org_scope:.0%} | {result.sql_avg_latency_ms:.0f} | "
                f"{executed}/{len(result.sql_cases)} | "
                f"{sum(1 for case in result.sql_cases if case.error)} |"
            )

        lines.extend(["", "### Per-question SQL", ""])
        for result in results:
            if not result.sql_cases:
                continue
            lines.append(f"#### `{result.model}`")
            lines.append("")
            for case in result.sql_cases:
                status = "pass" if case.valid_select else "fail"
                lines.append(f"- **{case.question}** — {status} ({case.latency_ms:.0f} ms)")
                if case.sql:
                    compact = " ".join(case.sql.split())
                    lines.append(f"  - SQL: `{compact}`")
                if case.error:
                    lines.append(f"  - Error: {case.error}")
            lines.append("")

    lines.extend(
        [
            "## How to reproduce",
            "",
            "```bash",
            "uv run python scripts/compare_planner_models.py --pull --details \\",
            "    --write docs/phase5-model-benchmark.md",
            "```",
            "",
            "Default models are the small laptop catalog tags in "
            "`DEFAULT_BENCHMARK_MODELS`. Use `--models ...` to override. "
            "Ollama must be running at `OLLAMA_BASE_URL` (default "
            "http://localhost:11434).",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark Ollama models for analytics planning and text-to-SQL.",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=list(DEFAULT_BENCHMARK_MODELS),
        help="Ollama model tags to benchmark (default: small catalog tags)",
    )
    parser.add_argument(
        "--suite",
        choices=sorted(SUITES),
        default="extended",
        help="Intent-classification suite to run",
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
    parser.add_argument(
        "--write",
        metavar="PATH",
        help="Write a markdown report (e.g. docs/phase5-model-benchmark.md)",
    )
    parser.add_argument(
        "--skip-sql",
        action="store_true",
        help="Skip the text-to-SQL suite",
    )
    parser.add_argument(
        "--execute-sql",
        action="store_true",
        default=True,
        help="Execute validated SQL against the local database (default: on)",
    )
    parser.add_argument(
        "--no-execute-sql",
        action="store_true",
        help="Validate generated SQL without executing it",
    )

    args = parser.parse_args(argv)

    if args.catalog:
        _print_catalog()
        return 0

    execute_sql = bool(args.execute_sql) and not args.no_execute_sql
    suite = SUITES[args.suite]
    hardware = _hardware_notes()
    pulled: list[str] = []
    blocked = None

    try:
        installed = list_installed_models()
    except urllib.error.URLError as exc:
        message = (
            "Could not reach Ollama. Start it first "
            f"({get_settings().ollama_base_url}). {exc}"
        )
        print(message, file=sys.stderr)
        if args.write:
            path = Path(args.write)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                _render_markdown(
                    results=[],
                    suite_name=args.suite,
                    hardware=hardware,
                    pulled=[],
                    execute_sql=execute_sql,
                    blocked=message,
                )
            )
            print(f"Wrote blocked-run report to {path}")
        return 1

    print(f"Running {args.suite} suite ({len(suite)} intent questions)")
    if not args.skip_sql:
        print(f"Text-to-SQL suite ({len(TEXT_TO_SQL_SUITE)} questions)")

    results: list[ModelResult] = []

    for model in args.models:
        did_pull = False
        if not model_installed(model, installed):
            if not args.pull:
                print(
                    f"Skipping {model}: not installed. Run: ollama pull {model}",
                    file=sys.stderr,
                )
                results.append(
                    ModelResult(model=model, installed=False, pulled=False, cases=[])
                )
                continue
            print(f"Pulling {model}...")
            try:
                pull_model(model, on_status=lambda status: print(f"  {status}", end="\r"))
                print(f"\n  {model} ready")
                did_pull = True
                pulled.append(model)
                installed = list_installed_models()
            except Exception as exc:
                print(f"Failed to pull {model}: {exc}", file=sys.stderr)
                results.append(
                    ModelResult(model=model, installed=False, pulled=False, cases=[])
                )
                continue

        print(f"\nBenchmarking {model}...")
        intent_cases = _evaluate_intent(model, suite)
        sql_cases: list[SqlCaseResult] = []
        if not args.skip_sql:
            print(f"  text-to-SQL ({len(TEXT_TO_SQL_SUITE)} questions)...")
            sql_cases = _evaluate_sql(model, TEXT_TO_SQL_SUITE, execute=execute_sql)
        results.append(
            _summarise_model(model, did_pull, intent_cases, sql_cases)
        )

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        _print_summary(results)
        if args.details:
            _print_details(results)

    if args.write:
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            _render_markdown(
                results=results,
                suite_name=args.suite,
                hardware=hardware,
                pulled=pulled,
                execute_sql=execute_sql,
                blocked=blocked,
            )
        )
        print(f"\nWrote {path}")

    recommend = _recommend(results)
    if recommend:
        print(f"\nRecommended default: {recommend}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
