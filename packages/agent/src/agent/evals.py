"""
Nightly eval pipeline — scores a random sample of past reports
and tracks quality drift over time in LangSmith.
"""
import os
import random
from datetime import datetime, timezone
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

from langsmith import Client
from langsmith.evaluation import evaluate
from langchain_ollama import ChatOllama

llm = ChatOllama(model="mistral", temperature=0.0)
ls_client = Client()

DATASET_NAME = "signal-report-quality"


def create_or_update_dataset(reports: list[dict]):
    """
    Push recent reports to a LangSmith dataset for eval tracking.
    Creates the dataset if it doesn't exist.
    """
    try:
        dataset = ls_client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Signal intelligence report quality evaluation dataset",
        )
        logger.info(f"Created LangSmith dataset: {DATASET_NAME}")
    except Exception:
        dataset = ls_client.read_dataset(dataset_name=DATASET_NAME)
        logger.info(f"Using existing LangSmith dataset: {DATASET_NAME}")

    # Add reports as examples
    for report in reports:
        ls_client.create_example(
            inputs={
                "domain": report["domain"],
                "title": report["title"],
                "summary": report["summary"],
                "key_themes": report.get("key_themes", []),
                "notable_signals": report.get("notable_signals", []),
            },
            outputs={
                "sentiment": report["sentiment"],
                "quality_score": report["quality_score"],
            },
            dataset_id=dataset.id,
        )

    logger.info(f"Added {len(reports)} examples to dataset")
    return dataset


def score_report(inputs: dict) -> dict:
    """Target function for LangSmith evaluator."""
    prompt = f"""Rate this intelligence report from 0.0 to 1.0.

Title: {inputs['title']}
Summary: {inputs['summary']}
Key Themes: {', '.join(inputs.get('key_themes', []))}
Notable Signals: {', '.join(inputs.get('notable_signals', []))}

Respond with just a number between 0.0 and 1.0."""

    response = llm.invoke(prompt)
    try:
        score = float(response.content.strip())
        return {"score": max(0.0, min(1.0, score))}
    except Exception:
        return {"score": 0.5}


def quality_evaluator(run, example) -> dict:
    """LangSmith evaluator function."""
    predicted_score = run.outputs.get("score", 0.5)
    expected_score = example.outputs.get("quality_score", 0.5)
    delta = abs(predicted_score - expected_score)
    return {
        "key": "quality_consistency",
        "score": 1.0 - delta,
        "comment": f"predicted={predicted_score:.2f}, expected={expected_score:.2f}",
    }


def run_evals():
    """
    Pull recent reports from PostgreSQL, push to LangSmith dataset,
    run evaluation, and log results.
    """
    from storage.db import get_recent_reports

    logger.info("Starting nightly eval run...")

    reports = get_recent_reports(limit=20)
    if not reports:
        logger.warning("No reports found for eval. Run pipeline first.")
        return

    # Convert db rows to dicts with list fields
    report_dicts = []
    for r in reports:
        report_dicts.append({
            "domain": r["domain"],
            "title": r["title"],
            "summary": r["summary"],
            "key_themes": [t.strip() for t in r.get("key_themes", "").split(",") if t.strip()],
            "notable_signals": [s.strip() for s in r.get("notable_signals", "").split(",") if s.strip()],
            "sentiment": r["sentiment"],
            "quality_score": r["quality_score"],
        })

    # Sample up to 10 for eval
    sample = random.sample(report_dicts, min(10, len(report_dicts)))
    logger.info(f"Running evals on {len(sample)} reports")

    dataset = create_or_update_dataset(sample)

    results = evaluate(
        score_report,
        data=DATASET_NAME,
        evaluators=[quality_evaluator],
        experiment_prefix="signal-nightly-eval",
        metadata={"run_date": datetime.now(timezone.utc).isoformat()},
    )

    logger.info(f"Eval complete. Results in LangSmith project 'signal'")
    return results


if __name__ == "__main__":
    run_evals()