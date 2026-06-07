from typing import TypedDict, Any
from datetime import datetime


class SignalBatch(TypedDict):
    """A batch of raw signals for one domain."""
    domain: str
    signals: list[dict]
    signal_count: int


class IntelligenceReport(TypedDict):
    """Structured output from the Analyst node."""
    domain: str
    title: str
    summary: str
    key_themes: list[str]
    notable_signals: list[str]
    sentiment: str          # "bullish" | "bearish" | "neutral"
    quality_score: float    # 0.0 - 1.0, set by Judge node
    quality_feedback: str
    generated_at: str


class AgentState(TypedDict):
    """
    The full state object that flows through every node in the graph.
    LangGraph reads and writes this at each step.
    """
    # Input
    run_id: str
    hours_lookback: int

    # Set by Supervisor
    batches: list[SignalBatch]
    domains_to_process: list[str]
    current_domain_index: int

    # Set by Researcher
    current_batch: SignalBatch | None
    extracted_context: str

    # Set by Analyst
    current_report: IntelligenceReport | None

    # Set by Judge
    reports: list[IntelligenceReport]
    failed_domains: list[str]

    # Control flow
    retry_count: int
    max_retries: int
    status: str   # "running" | "complete" | "failed"
    error: str | None