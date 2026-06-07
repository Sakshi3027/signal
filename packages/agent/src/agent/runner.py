import uuid
from datetime import datetime, timezone
from loguru import logger
from dotenv import load_dotenv
from .graph import build_graph
from .state import AgentState

load_dotenv()


def run_agent(hours_lookback: int = 72) -> list[dict]:
    """
    Run the Signal agent graph end-to-end.
    Returns list of generated intelligence reports.
    """
    run_id = str(uuid.uuid4())[:8]
    logger.info(f"Starting Signal agent run [{run_id}]")

    graph = build_graph()

    initial_state: AgentState = {
        "run_id": run_id,
        "hours_lookback": hours_lookback,
        "batches": [],
        "domains_to_process": [],
        "current_domain_index": 0,
        "current_batch": None,
        "extracted_context": "",
        "current_report": None,
        "reports": [],
        "failed_domains": [],
        "retry_count": 0,
        "max_retries": 2,
        "status": "running",
        "error": None,
    }

    final_state = graph.invoke(initial_state)

    reports = final_state.get("reports", [])
    logger.info(f"Agent run [{run_id}] complete — {len(reports)} reports")
    return reports


if __name__ == "__main__":
    reports = run_agent()
    print("\n" + "="*60)
    for report in reports:
        print(f"\n📊 {report['title']}")
        print(f"Domain: {report['domain']} | Sentiment: {report['sentiment']} | Score: {report['quality_score']:.2f}")
        print(f"\nSummary: {report['summary']}")
        print(f"\nKey Themes:")
        for t in report['key_themes']:
            print(f"  • {t}")
        print(f"\nNotable Signals:")
        for s in report['notable_signals']:
            print(f"  • {s}")
        print(f"\nJudge Feedback: {report['quality_feedback']}")
        print("="*60)