import uuid
from datetime import datetime, timezone
from loguru import logger
from langchain_ollama import ChatOllama
from .state import AgentState, SignalBatch, IntelligenceReport
from .tools import read_signals_for_domain, get_domain_stats

# Single shared LLM instance
llm = ChatOllama(model="mistral", temperature=0.3)


# ─────────────────────────────────────────
# NODE 1: SUPERVISOR
# Reads DuckDB stats, decides what to process
# ─────────────────────────────────────────
def supervisor_node(state: AgentState) -> AgentState:
    logger.info("=== SUPERVISOR: deciding what to investigate ===")

    stats = get_domain_stats(state["hours_lookback"])
    logger.info(f"Domain stats: {stats}")

    if not stats:
        logger.warning("No signals found in DB. Run ingestion first.")
        return {**state, "status": "failed", "error": "No signals in DB"}

    # Build batches for each domain that has signals
    batches = []
    domains_to_process = []

    for domain, count in stats.items():
        if count == 0:
            continue
        signals = read_signals_for_domain(
            domain=domain,
            hours_lookback=state["hours_lookback"],
            limit=25,
        )
        batch: SignalBatch = {
            "domain": domain,
            "signals": signals,
            "signal_count": len(signals),
        }
        batches.append(batch)
        domains_to_process.append(domain)
        logger.info(f"  Queued domain '{domain}' with {len(signals)} signals")

    return {
        **state,
        "batches": batches,
        "domains_to_process": domains_to_process,
        "current_domain_index": 0,
        "reports": [],
        "failed_domains": [],
        "status": "running",
    }


# ─────────────────────────────────────────
# NODE 2: RESEARCHER
# Takes current batch, extracts structured context
# ─────────────────────────────────────────
def researcher_node(state: AgentState) -> AgentState:
    idx = state["current_domain_index"]
    batch = state["batches"][idx]
    domain = batch["domain"]

    logger.info(f"=== RESEARCHER: extracting context for '{domain}' ===")

    # Format signals into a readable block for the LLM
    signal_lines = []
    for i, sig in enumerate(batch["signals"][:20], 1):
        title = sig.get("title", "")
        summary = (sig.get("summary") or "")[:300]
        source = sig.get("source_name", "")
        signal_lines.append(f"{i}. [{source}] {title}\n   {summary}")

    signals_text = "\n\n".join(signal_lines)

    prompt = f"""You are a signal analyst. Below are recent signals from the {domain.upper()} domain.

Extract and summarize the most important information:
- What are the 3-5 main themes or topics appearing across these signals?
- Which signals are most significant and why?
- What is the overall market/technology sentiment?

SIGNALS:
{signals_text}

Respond with a structured analysis in plain text. Be specific and concise."""

    logger.info(f"  Calling Mistral for context extraction ({len(batch['signals'])} signals)...")
    response = llm.invoke(prompt)
    extracted_context = response.content

    logger.info(f"  Extracted {len(extracted_context)} chars of context")

    return {
        **state,
        "current_batch": batch,
        "extracted_context": extracted_context,
        "retry_count": 0,
    }


# ─────────────────────────────────────────
# NODE 3: ANALYST
# Writes the final intelligence report
# ─────────────────────────────────────────
def analyst_node(state: AgentState) -> AgentState:
    batch = state["current_batch"]
    domain = batch["domain"]
    context = state["extracted_context"]

    logger.info(f"=== ANALYST: writing intelligence report for '{domain}' ===")

    prompt = f"""You are a senior intelligence analyst writing a briefing report.

Based on this analysis of recent {domain.upper()} signals:

{context}

Write a structured intelligence report with exactly this format:

TITLE: [compelling 1-line title for this briefing]

SUMMARY: [2-3 sentence executive summary of what is happening in this domain right now]

KEY_THEMES:
- [theme 1]
- [theme 2]
- [theme 3]

NOTABLE_SIGNALS:
- [most significant signal/development 1]
- [most significant signal/development 2]
- [most significant signal/development 3]

SENTIMENT: [exactly one of: bullish / bearish / neutral]

Be specific, factual, and concise. No filler phrases."""

    logger.info("  Calling Mistral for report generation...")
    response = llm.invoke(prompt)
    raw_report = response.content

    logger.info(f"  Generated report ({len(raw_report)} chars)")

    # Parse the structured response
    report = _parse_report(raw_report, domain)

    return {
        **state,
        "current_report": report,
    }


def _parse_report(raw: str, domain: str) -> IntelligenceReport:
    """Parse the LLM's structured text response into an IntelligenceReport."""
    lines = raw.strip().split("\n")

    title = ""
    summary = ""
    key_themes = []
    notable_signals = []
    sentiment = "neutral"

    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
        elif line.startswith("SUMMARY:"):
            summary = line.replace("SUMMARY:", "").strip()
            current_section = "summary"
        elif line.startswith("KEY_THEMES:"):
            current_section = "themes"
        elif line.startswith("NOTABLE_SIGNALS:"):
            current_section = "signals"
        elif line.startswith("SENTIMENT:"):
            raw_sentiment = line.replace("SENTIMENT:", "").strip().lower()
            if "bullish" in raw_sentiment:
                sentiment = "bullish"
            elif "bearish" in raw_sentiment:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
            current_section = None
        elif line.startswith("- "):
            item = line[2:].strip()
            if current_section == "themes":
                key_themes.append(item)
            elif current_section == "signals":
                notable_signals.append(item)
        elif current_section == "summary" and line:
            # Multi-line summary
            summary = (summary + " " + line).strip()

    # Fallbacks if parsing missed something
    if not title:
        title = f"{domain.upper()} Intelligence Brief"
    if not summary:
        summary = raw[:300]

    return IntelligenceReport(
        domain=domain,
        title=title,
        summary=summary,
        key_themes=key_themes[:5],
        notable_signals=notable_signals[:5],
        sentiment=sentiment,
        quality_score=0.0,       # will be set by Judge
        quality_feedback="",     # will be set by Judge
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ─────────────────────────────────────────
# NODE 4: JUDGE
# Scores the report, routes back if quality is low
# ─────────────────────────────────────────
def judge_node(state: AgentState) -> AgentState:
    report = state["current_report"]
    domain = report["domain"]

    logger.info(f"=== JUDGE: scoring report for '{domain}' ===")

    prompt = f"""You are a quality judge for intelligence reports. Score this report strictly.

REPORT:
Title: {report['title']}
Summary: {report['summary']}
Key Themes: {', '.join(report['key_themes'])}
Notable Signals: {', '.join(report['notable_signals'])}
Sentiment: {report['sentiment']}

Score this report on:
1. Specificity (does it mention concrete facts, not vague generalities?)
2. Completeness (does it have all sections filled with real content?)
3. Coherence (does it make sense as an intelligence briefing?)

Respond in exactly this format:
SCORE: [a number between 0.0 and 1.0]
FEEDBACK: [one sentence explaining the score]"""

    response = llm.invoke(prompt)
    raw = response.content.strip()

    # Parse score and feedback
    score = 0.5
    feedback = "Could not parse judge response"

    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("SCORE:"):
            try:
                score = float(line.replace("SCORE:", "").strip())
                score = max(0.0, min(1.0, score))
            except ValueError:
                pass
        elif line.startswith("FEEDBACK:"):
            feedback = line.replace("FEEDBACK:", "").strip()

    logger.info(f"  Quality score: {score:.2f} — {feedback}")

    scored_report = {**report, "quality_score": score, "quality_feedback": feedback}

    return {
        **state,
        "current_report": scored_report,
    }