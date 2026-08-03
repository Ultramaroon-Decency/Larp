"""Research job endpoints backed by ResearchService."""

from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, Response, status
from fastapi.responses import HTMLResponse

from app.dependencies import (
    get_agent_manager,
    get_current_user,
    get_report_service,
    get_research_service,
)
from app.schemas.common import PaginatedResponse, ResponseEnvelope
from app.schemas.research import (
    ResearchCancelResponse,
    ResearchJobCreate,
    ResearchJobDetailsRead,
    ResearchJobRead,
    ResearchJobStatusResponse,
    SaveMetadataRequest,
    UpdateProgressRequest,
)
from app.services.agent_manager import AgentManager
from app.services.report_service import ReportService
from app.services.research_service import ResearchService

router = APIRouter()


@router.post(
    "/",
    summary="Create Research Job",
    response_model=ResponseEnvelope[ResearchJobRead],
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Research job successfully created and background worker enqueued."},
        401: {"description": "Unauthorized access token."},
        402: {"description": "Payment Required: Budget balance exceeded."},
        422: {"description": "Validation Error: Unprocessable entity payload."},
    },
)
async def create_research_job(
    body: ResearchJobCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service),
    agent_manager: AgentManager = Depends(get_agent_manager),
) -> ResponseEnvelope[ResearchJobRead]:
    """Create a new multi-step research job and dispatch AgentManager pipeline asynchronously."""
    user_id = UUID(current_user["id"])
    job = await research_service.create_job(user_id=user_id, data=body)

    # Dispatch AgentManager pipeline in background (Planner -> Search -> FactChecker -> Citation -> Report)
    background_tasks.add_task(
        agent_manager.run_pipeline,
        job_id=job.id,
        user_id=user_id,
        query=body.query,
        depth=body.depth,
    )

    return ResponseEnvelope(
        success=True,
        message="Research job created and agent pipeline dispatched",
        data=job,
    )


@router.get(
    "/history",
    summary="List Research History",
    response_model=ResponseEnvelope[PaginatedResponse[ResearchJobRead]],
)
async def list_research_history(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    status: str | None = Query(None, description="Filter by status (pending, in_progress, completed, failed)"),
    depth: str | None = Query(None, description="Filter by depth (quick, standard, deep)"),
    search: str | None = Query(None, description="Keyword search in job title or query"),
    order_by: str | None = Query("-created_at", description="Sorting field (e.g. -created_at, created_at, title, -title)"),
    current_user: dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service),
) -> ResponseEnvelope[PaginatedResponse[ResearchJobRead]]:
    """List, search, filter, and paginate the authenticated user's research job history."""
    user_id = UUID(current_user["id"])
    paginated_history = await research_service.list_user_history(
        user_id=user_id,
        page=page,
        page_size=page_size,
        status=status,
        depth=depth,
        search=search,
        order_by=order_by,
    )

    return ResponseEnvelope(
        success=True,
        message="Research history retrieved successfully",
        data=paginated_history,
    )


@router.get(
    "/{job_id}",
    summary="Get Research Job Details",
    response_model=ResponseEnvelope[ResearchJobDetailsRead],
)
async def get_research_job(
    job_id: UUID,
    current_user: dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service),
) -> ResponseEnvelope[ResearchJobDetailsRead]:
    """Get full research job details including generated report and web sources (cached in Redis)."""
    user_id = UUID(current_user["id"])
    job_details = await research_service.get_job_details(job_id=job_id, user_id=user_id)

    return ResponseEnvelope(
        success=True,
        message="Research job details retrieved successfully",
        data=job_details,
    )


@router.get(
    "/{job_id}/status",
    summary="Track Job Execution Status",
    response_model=ResponseEnvelope[ResearchJobStatusResponse],
)
async def track_job_status(
    job_id: UUID,
    current_user: dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service),
) -> ResponseEnvelope[ResearchJobStatusResponse]:
    """Track execution status of an active research job."""
    user_id = UUID(current_user["id"])
    job_status = await research_service.get_job_status(job_id=job_id, user_id=user_id)

    return ResponseEnvelope(
        success=True,
        message="Research job status retrieved successfully",
        data=job_status,
    )


@router.patch(
    "/{job_id}/metadata",
    summary="Save Job Metadata",
    response_model=ResponseEnvelope[ResearchJobRead],
)
async def save_job_metadata(
    job_id: UUID,
    body: SaveMetadataRequest,
    current_user: dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service),
) -> ResponseEnvelope[ResearchJobRead]:
    """Save / update metadata or configuration for a research job."""
    user_id = UUID(current_user["id"])
    updated_job = await research_service.save_metadata(
        job_id=job_id, user_id=user_id, data=body
    )

    return ResponseEnvelope(
        success=True,
        message="Research job metadata saved successfully",
        data=updated_job,
    )


@router.patch(
    "/{job_id}/progress",
    summary="Update Job Progress",
    response_model=ResponseEnvelope[ResearchJobStatusResponse],
)
async def update_job_progress(
    job_id: UUID,
    body: UpdateProgressRequest,
    current_user: dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service),
) -> ResponseEnvelope[ResearchJobStatusResponse]:
    """Update research job execution status and progress metrics."""
    user_id = UUID(current_user["id"])
    updated_status = await research_service.update_progress(
        job_id=job_id, user_id=user_id, data=body
    )

    return ResponseEnvelope(
        success=True,
        message="Research job progress updated successfully",
        data=updated_status,
    )


@router.post(
    "/{job_id}/cancel",
    summary="Cancel Research Job",
    description="Cancel an active or queued research job owned by the authenticated user.",
    response_model=ResearchCancelResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Research job cancelled successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "research_id": "123e4567-e89b-12d3-a456-426614174000",
                        "status": "cancelled",
                        "message": "Research cancelled successfully.",
                    }
                }
            },
        },
        401: {"description": "Unauthorized access token."},
        403: {"description": "Forbidden: User does not own this research job."},
        404: {"description": "Research job not found."},
        409: {"description": "Conflict: Invalid status transition (job is completed, failed, or already cancelled)."},
        500: {"description": "Unexpected error."},
    },
)
async def cancel_research_job(
    job_id: UUID = Path(..., description="ID of the research job to cancel"),
    current_user: dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service),
) -> ResearchCancelResponse:
    """Cancel a queued or running research job."""
    user_id = UUID(current_user["id"])
    return await research_service.cancel_research(job_id=job_id, user_id=user_id)


@router.delete(
    "/{job_id}",
    summary="Delete Research Job",
    response_model=ResponseEnvelope[None],
)
async def delete_research_job(
    job_id: UUID,
    current_user: dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service),
) -> ResponseEnvelope[None]:
    """Delete a research job by ID."""
    user_id = UUID(current_user["id"])
    await research_service.delete_job(job_id=job_id, user_id=user_id)

    return ResponseEnvelope(
        success=True,
        message="Research job deleted successfully",
        data=None,
    )


@router.get("/{job_id}/export/markdown", summary="Export Report as Markdown")
async def export_report_markdown(
    job_id: UUID,
    current_user: dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service),
    report_service: ReportService = Depends(get_report_service),
):
    """Export research report as Markdown text file."""
    user_id = UUID(current_user["id"])
    job_details = await research_service.get_job_details(job_id=job_id, user_id=user_id)
    report_content = job_details.report.content_markdown if job_details.report else "# Report Not Ready"

    return Response(
        content=report_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=report_{job_id}.md"},
    )


@router.get("/{job_id}/export/html", summary="View Report HTML", response_class=HTMLResponse)
async def export_report_html(
    job_id: UUID,
    current_user: dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service),
    report_service: ReportService = Depends(get_report_service),
):
    """Export research report as styled HTML5 document."""
    user_id = UUID(current_user["id"])
    job_details = await research_service.get_job_details(job_id=job_id, user_id=user_id)
    markdown_content = job_details.report.content_markdown if job_details.report else "# Report Not Ready"
    title = job_details.title or "Research Report"
    html_content = report_service.generate_html(markdown_content, title=title)

    return HTMLResponse(content=html_content)


@router.get("/{job_id}/export/pdf", summary="Export Report as PDF")
async def export_report_pdf(
    job_id: UUID,
    current_user: dict = Depends(get_current_user),
    research_service: ResearchService = Depends(get_research_service),
    report_service: ReportService = Depends(get_report_service),
):
    """Export research report as printable PDF document."""
    user_id = UUID(current_user["id"])
    job_details = await research_service.get_job_details(job_id=job_id, user_id=user_id)
    markdown_content = job_details.report.content_markdown if job_details.report else "# Report Not Ready"
    title = job_details.title or "Research Report"
    html_content = report_service.generate_html(markdown_content, title=title)
    pdf_bytes = report_service.generate_pdf(html_content)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{job_id}.pdf"},
    )
