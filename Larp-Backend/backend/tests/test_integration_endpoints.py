"""Integration tests for frontend compatibility endpoints (/api/export/bibtex, /api/payments/log)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_export_bibtex_endpoint(client: AsyncClient):
    """POST /api/export/bibtex generates valid BibTeX reference content."""
    payload = {
        "title": "Quantum Computing Survey",
        "sources": [
            {
                "id": "src-1",
                "title": "Quantum Supremacy Demo",
                "authors": "A. Einstein, N. Bohr",
                "year": 2024,
                "journal": "Nature Physics",
                "doi": "10.1038/nphys1234",
                "url": "https://example.com/quantum",
            }
        ],
    }

    response = await client.post("/api/export/bibtex", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "@article{" in response.text
    assert "Quantum Supremacy Demo" in response.text
    assert "A. Einstein, N. Bohr" in response.text


@pytest.mark.asyncio
async def test_payments_log_endpoint(client: AsyncClient):
    """GET /api/payments/log returns x402 payment receipts tracking schema for SettingsView."""
    response = await client.get("/api/payments/log")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["mode"] == "simulation"
    assert "totalTransactions" in json_data
    assert "totalSpentUSDC" in json_data
    assert isinstance(json_data["receipts"], list)
