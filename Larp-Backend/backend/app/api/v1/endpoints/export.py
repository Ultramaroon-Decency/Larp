"""BibTeX export endpoint for research references."""

from typing import Any, List
from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

router = APIRouter()


class BibtexExportRequest(BaseModel):
    """Payload for exporting research references to BibTeX format."""

    title: str = Field(default="Research References", description="Title of the research project")
    sources: List[dict[str, Any]] = Field(default_factory=list, description="List of research sources")


@router.post("/bibtex", summary="Export BibTeX References")
async def export_bibtex(body: BibtexExportRequest) -> Response:
    """Generate and return formatted BibTeX text content for references."""
    bib_entries = []

    for idx, source in enumerate(body.sources, 1):
        source_id = str(source.get("id", f"ref_{idx}"))
        title = source.get("title", f"Reference {idx}")
        authors = source.get("authors") or "Anonymous"
        year = source.get("year") or 2024
        journal = source.get("journal") or "Academic Journal"
        doi = source.get("doi") or ""
        url = source.get("url") or ""

        entry_key = f"ref_{idx}_{source_id}".replace("-", "_")

        entry = (
            f"@article{{{entry_key},\n"
            f"  title = {{{title}}},\n"
            f"  author = {{{authors}}},\n"
            f"  journal = {{{journal}}},\n"
            f"  year = {{{year}}}"
        )
        if doi:
            entry += f",\n  doi = {{{doi}}}"
        if url:
            entry += f",\n  url = {{{url}}}"
        entry += "\n}\n"

        bib_entries.append(entry)

    content = "\n".join(bib_entries) if bib_entries else f"% No sources provided for {body.title}\n"

    clean_title = "".join(c for c in body.title if c.isalnum() or c in (" ", "_")).rstrip().replace(" ", "_")
    filename = f"{clean_title.lower() or 'references'}.bib"

    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
