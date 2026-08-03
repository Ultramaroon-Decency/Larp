"""Unit tests for Research Cancellation API endpoint POST /api/v1/research/{research_id}/cancel."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.research_job import ResearchJob


@pytest.mark.asyncio
async def test_cancel_queued_research(client: AsyncClient, db_session: AsyncSession, auth_headers: dict):
    """✓ Test cancelling a queued (pending) research job succeeds with 200 OK."""
    from app.core.security import decode_access_token
    token = auth_headers["Authorization"].split(" ")[1]
    payload = decode_access_token(token)
    user_uuid = uuid.UUID(payload.sub)

    job = ResearchJob(
        id=uuid.uuid4(),
        user_id=user_uuid,
        title="Queued Job",
        query="Test query queued",
        status="pending",
        depth="standard",
    )
    db_session.add(job)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/research/{job.id}/cancel",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["research_id"] == str(job.id)
    assert data["status"] == "cancelled"
    assert data["message"] == "Research cancelled successfully."

    # Verify status in database
    await db_session.refresh(job)
    assert job.status == "cancelled"
    assert job.cancelled_at is not None


@pytest.mark.asyncio
async def test_cancel_running_research(client: AsyncClient, db_session: AsyncSession, auth_headers: dict):
    """✓ Test cancelling a running (in_progress) research job succeeds with 200 OK."""
    from app.core.security import decode_access_token
    token = auth_headers["Authorization"].split(" ")[1]
    payload = decode_access_token(token)
    user_uuid = uuid.UUID(payload.sub)

    job = ResearchJob(
        id=uuid.uuid4(),
        user_id=user_uuid,
        title="Running Job",
        query="Test query running",
        status="in_progress",
        depth="deep",
    )
    db_session.add(job)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/research/{job.id}/cancel",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["research_id"] == str(job.id)
    assert data["status"] == "cancelled"

    await db_session.refresh(job)
    assert job.status == "cancelled"
    assert job.cancelled_at is not None


@pytest.mark.asyncio
async def test_cancel_completed_research(client: AsyncClient, db_session: AsyncSession, auth_headers: dict):
    """✓ Test cancelling a completed research job returns 409 Conflict."""
    from app.core.security import decode_access_token
    token = auth_headers["Authorization"].split(" ")[1]
    payload = decode_access_token(token)
    user_uuid = uuid.UUID(payload.sub)

    job = ResearchJob(
        id=uuid.uuid4(),
        user_id=user_uuid,
        title="Completed Job",
        query="Test query completed",
        status="completed",
        depth="standard",
    )
    db_session.add(job)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/research/{job.id}/cancel",
        headers=auth_headers,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_cancel_failed_research(client: AsyncClient, db_session: AsyncSession, auth_headers: dict):
    """✓ Test cancelling a failed research job returns 409 Conflict."""
    from app.core.security import decode_access_token
    token = auth_headers["Authorization"].split(" ")[1]
    payload = decode_access_token(token)
    user_uuid = uuid.UUID(payload.sub)

    job = ResearchJob(
        id=uuid.uuid4(),
        user_id=user_uuid,
        title="Failed Job",
        query="Test query failed",
        status="failed",
        depth="standard",
    )
    db_session.add(job)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/research/{job.id}/cancel",
        headers=auth_headers,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_cancel_already_cancelled_research(client: AsyncClient, db_session: AsyncSession, auth_headers: dict):
    """✓ Test cancelling an already cancelled research job returns 409 Conflict."""
    from app.core.security import decode_access_token
    token = auth_headers["Authorization"].split(" ")[1]
    payload = decode_access_token(token)
    user_uuid = uuid.UUID(payload.sub)

    job = ResearchJob(
        id=uuid.uuid4(),
        user_id=user_uuid,
        title="Already Cancelled Job",
        query="Test query cancelled",
        status="cancelled",
        depth="standard",
    )
    db_session.add(job)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/research/{job.id}/cancel",
        headers=auth_headers,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_unauthorized_cancellation(client: AsyncClient, db_session: AsyncSession, auth_headers: dict):
    """✓ Test unauthorized cancellation (non-owner or missing token) returns 401 Unauthorized."""
    # Create job owned by owner_uuid
    owner_uuid = uuid.uuid4()
    job = ResearchJob(
        id=uuid.uuid4(),
        user_id=owner_uuid,
        title="Other User Job",
        query="Test query unauthorized",
        status="pending",
        depth="standard",
    )
    db_session.add(job)
    await db_session.commit()

    # User B (auth_headers) attempts to cancel owner_uuid's job -> 401
    response = await client.post(
        f"/api/v1/research/{job.id}/cancel",
        headers=auth_headers,
    )
    assert response.status_code == 401

    # Unauthenticated request (no headers) -> 401
    unauth_response = await client.post(f"/api/v1/research/{job.id}/cancel")
    assert unauth_response.status_code == 401


@pytest.mark.asyncio
async def test_cancel_nonexistent_research(client: AsyncClient, auth_headers: dict):
    """✓ Test cancelling a non-existent research job returns 404 Not Found."""
    random_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/research/{random_id}/cancel",
        headers=auth_headers,
    )
    assert response.status_code == 404
