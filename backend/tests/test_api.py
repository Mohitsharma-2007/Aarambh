import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_market_heatmap():
    response = client.get("/api/v1/market/heatmap")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_market_sectors():
    response = client.get("/api/v1/market/sectors")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_ingestion_status():
    response = client.get("/api/v1/ingest/status")
    # If the database is empty or no status, it might be 200 list or dict
    assert response.status_code in [200, 404]

def test_ai_models():
    response = client.get("/api/v1/ai/providers")
    assert response.status_code == 200
    assert "providers" in response.json()

def test_cot_financial_futures():
    response = client.get("/api/v1/cot/financial-futures")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
