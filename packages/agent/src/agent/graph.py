from langgraph.graph import StateGraph, END
from loguru import logger
from .state import AgentState
from .nodes import supervisor_node, researcher_node, analyst_node, judge_node


def _route_after_judge(state: AgentState) -> str:
    """
    After Judge scores a report:
    - Score >= 0.6 → accept report, move to next domain
    - Score < 0.6 and retries left → send back to Analyst
    - Score < 0.6 and no retries → accept anyway, mark as low quality
    """
    report = state["current_report"]
    score = report["quality_score"]
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if score >= 0.6:
        logger.info(f"  ✓ Report accepted (score={score:.2f})")
        return "accept"
    elif retry_count < max_retries:
        logger.warning(f"  ↻ Re-routing to Analyst (score={score:.2f}, retry {retry_count+1}/{max_retries})")
        return "retry"
    else:
        logger.warning(f"  ✗ Accepting low-quality report after {max_retries} retries (score={score:.2f})")
        return "accept"


def _accept_report(state: AgentState) -> AgentState:
    """Accept current report and advance to next domain."""
    reports = list(state.get("reports", []))
    reports.append(state["current_report"])

    next_index = state["current_domain_index"] + 1

    return {
        **state,
        "reports": reports,
        "current_domain_index": next_index,
        "current_report": None,
        "extracted_context": "",
        "retry_count": 0,
    }


def _retry_analyst(state: AgentState) -> AgentState:
    """Increment retry count and go back to Analyst."""
    return {
        **state,
        "retry_count": state.get("retry_count", 0) + 1,
    }


def _should_continue(state: AgentState) -> str:
    """Check if there are more domains to process."""
    if state.get("status") == "failed":
        return "end"

    idx = state["current_domain_index"]
    total = len(state.get("domains_to_process", []))

    if idx >= total:
        logger.info(f"All {total} domains processed. Agent complete.")
        return "end"

    next_domain = state["domains_to_process"][idx]
    logger.info(f"Moving to domain {idx+1}/{total}: '{next_domain}'")
    return "continue"


def _finalize(state: AgentState) -> AgentState:
    """Mark the run as complete."""
    logger.info(f"=== AGENT COMPLETE: {len(state['reports'])} reports generated ===")
    for r in state["reports"]:
        logger.info(f"  [{r['domain']}] {r['title']} (score={r['quality_score']:.2f})")
    return {**state, "status": "complete"}


def build_graph() -> StateGraph:
    """Build and compile the Signal agent graph."""
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("judge", judge_node)
    graph.add_node("accept_report", _accept_report)
    graph.add_node("retry_analyst", _retry_analyst)
    graph.add_node("finalize", _finalize)

    # Entry point
    graph.set_entry_point("supervisor")

    # Supervisor → check if we have domains
    graph.add_conditional_edges(
        "supervisor",
        _should_continue,
        {"continue": "researcher", "end": "finalize"},
    )

    # Researcher → Analyst → Judge
    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "judge")

    # Judge → route based on score
    graph.add_conditional_edges(
        "judge",
        _route_after_judge,
        {"accept": "accept_report", "retry": "retry_analyst"},
    )

    # After retry → back to Analyst
    graph.add_edge("retry_analyst", "analyst")

    # After accepting → check if more domains
    graph.add_conditional_edges(
        "accept_report",
        _should_continue,
        {"continue": "researcher", "end": "finalize"},
    )

    # Finalize → END
    graph.add_edge("finalize", END)

    return graph.compile()