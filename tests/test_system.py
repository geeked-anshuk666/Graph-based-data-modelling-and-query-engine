import pytest
from httpx import AsyncClient, ASGITransport
import asyncio

import os
import sys

# add root and backend to python path for testing
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from backend.main import app
from backend.llm.guardrails import is_on_topic

from fastapi.testclient import TestClient

def test_health_check():
    with TestClient(app) as client:
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["backend"]["ok"] is True
        assert data["database"]["ok"] is True

def test_graph_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/graph")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "links" in data
        assert isinstance(data["nodes"], list)

from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_guardrails_pass():
    # True positives (mock LLM returning 'yes')
    with patch("backend.llm.guardrails.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value.choices[0].message.content = "yes"
        mock_get.return_value = mock_client
        assert await is_on_topic("Which products are mostly delivered?") == True
        assert await is_on_topic("Show me billing docs for company C000") == True

@pytest.mark.asyncio
async def test_guardrails_fail():
    # True negatives (mock LLM returning 'no')
    with patch("backend.llm.guardrails.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value.choices[0].message.content = "no"
        mock_get.return_value = mock_client
        assert await is_on_topic("What is the capital of France?") == False
        assert await is_on_topic("Write a python script to parse xml") == False
