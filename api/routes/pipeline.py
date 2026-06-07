import uuid
import threading
from fastapi import APIRouter, BackgroundTasks
from loguru import logger
from api.models import PipelineRunResponse

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# Track running state
_pipeline_state = {"running": False, "last_run_id": None, "last_status": "idle"}


def _run_pipeline_background(run_id: str):
    """Run the full pipeline in a background thread."""
    global _pipeline_state
    _pipeline_state["running"] = True
    _pipeline_state["last_run_id"] = run_id

    try:
        from ingestion.pipeline import run_ingestion
        from agent.runner import run_agent
        from storage.runner import init_storage, store_reports

        logger.info(f"Background pipeline run [{run_id}] starting...")
        run_ingestion(hours_lookback=72)
        reports = run_agent(hours_lookback=72)
        init_storage()
        store_reports(reports, run_id=run_id)

        _pipeline_state["last_status"] = f"complete — {len(reports)} reports"
        logger.info(f"Background pipeline run [{run_id}] complete")
    except Exception as e:
        _pipeline_state["last_status"] = f"failed: {str(e)}"
        logger.error(f"Background pipeline run [{run_id}] failed: {e}")
    finally:
        _pipeline_state["running"] = False


@router.post("/run", response_model=PipelineRunResponse)
def trigger_pipeline(background_tasks: BackgroundTasks):
    """Trigger a full pipeline run in the background."""
    if _pipeline_state["running"]:
        return PipelineRunResponse(
            run_id=_pipeline_state["last_run_id"],
            status="already_running",
            reports_generated=0,
            message="Pipeline is already running. Check back in a few minutes.",
        )

    run_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(_run_pipeline_background, run_id)

    return PipelineRunResponse(
        run_id=run_id,
        status="started",
        reports_generated=0,
        message=f"Pipeline started with run_id={run_id}. Reports will appear shortly.",
    )


@router.get("/status")
def get_pipeline_status():
    """Get current pipeline run status."""
    return {
        "running": _pipeline_state["running"],
        "last_run_id": _pipeline_state["last_run_id"],
        "last_status": _pipeline_state["last_status"],
    }