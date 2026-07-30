"""Report download and viewing REST API endpoints (Download PDF, Download Markdown, View HTML)."""

from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import HTMLResponse

from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user, get_report_service
from app.repositories.research_report_repository import ResearchReportRepository
from app.schemas.common import ResponseEnvelope
from app.schemas.research import ResearchReportRead
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/job/{job_id}/versions", response_model=ResponseEnvelope[Sequence[ResearchReportRead]])
async def list_report_versions(
    job_id: UUID,
    current_user: dict = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
) -> ResponseEnvelope[Sequence[ResearchReportRead]]:
    """List all historical report revisions for a research job ordered by version descending."""
    versions = await report_service.list_report_versions(job_id)

    return ResponseEnvelope(
        success=True,
        message="Report versions retrieved successfully",
        data=versions,
    )


@router.get("/{report_id}", response_model=ResponseEnvelope[ResearchReportRead])
async def get_report_by_id(
    report_id: UUID,
    current_user: dict = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
) -> ResponseEnvelope[ResearchReportRead]:
    """Retrieve research report by ID."""
    report = await report_service.report_repo.get_by_id(report_id)
    if not report:
        raise NotFoundError("Research report not found")

    return ResponseEnvelope(
        success=True,
        message="Research report retrieved successfully",
        data=ResearchReportRead.model_validate(report),
    )


@router.get("/{report_id}/markdown")
async def download_report_markdown(
    report_id: UUID,
    current_user: dict = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
):
    """Download research report as a Markdown (.md) file.

    Headers:
        Content-Type: text/markdown
        Content-Disposition: attachment; filename=report_{report_id}.md
    """
    report = await report_service.report_repo.get_by_id(report_id)
    content = report.content_markdown if report else "# Report Content Not Available"

    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.md"},
    )


@router.get("/{report_id}/html", response_class=HTMLResponse)
async def view_report_html(
    report_id: UUID,
    current_user: dict = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
):
    """View research report as a styled HTML document directly in the browser."""
    report = await report_service.report_repo.get_by_id(report_id)
    markdown_content = report.content_markdown if report else "# Report Content Not Available"
    title = report.title if report else "Research Report"

    html_content = report_service.generate_html(markdown_content, title=title)
    return HTMLResponse(content=html_content)


@router.get("/{report_id}/pdf")
async def download_report_pdf(
    report_id: UUID,
    current_user: dict = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
):
    """Download research report as a printable PDF (.pdf) file.

    Headers:
        Content-Type: application/pdf
        Content-Disposition: attachment; filename=report_{report_id}.pdf
    """
    report = await report_service.report_repo.get_by_id(report_id)
    markdown_content = report.content_markdown if report else "# Report Content Not Available"
    title = report.title if report else "Research Report"

    html_content = report_service.generate_html(markdown_content, title=title)
    pdf_bytes = report_service.generate_pdf(html_content)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"},
    )
