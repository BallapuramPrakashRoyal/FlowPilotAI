"""API tests using httpx.AsyncClient with in-process FastAPI app."""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "FlowPilot AI" in data["service"]


@pytest.mark.asyncio
async def test_auth_registration_and_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        unique_email = f"architect_{pytest.importorskip('uuid').uuid4().hex[:6]}@flowpilot.ai"

        # Register
        reg_res = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "StrongPassword2026!",
                "full_name": "Chief Architect",
            },
        )
        assert reg_res.status_code == 201
        reg_data = reg_res.json()
        assert "access_token" in reg_data
        assert reg_data["user"]["email"] == unique_email

        token = reg_data["access_token"]

        # Get Me
        me_res = await ac.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        assert me_res.json()["email"] == unique_email

        # Login
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={
                "email": unique_email,
                "password": "StrongPassword2026!",
            },
        )
        assert login_res.status_code == 200
        assert "access_token" in login_res.json()


@pytest.mark.asyncio
async def test_ai_workflow_planner():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register a user to get token
        unique_email = f"planner_{pytest.importorskip('uuid').uuid4().hex[:6]}@flowpilot.ai"
        reg = await ac.post(
            "/api/v1/auth/register",
            json={"email": unique_email, "password": "Password123!", "full_name": "Planner User"},
        )
        token = reg.json()["access_token"]

        prompt = "Analyze my unread emails, classify urgent messages, summarize important emails, and prepare responses for my approval."
        res = await ac.post(
            "/api/v1/workflows/generate",
            json={"workspace_id": "ws-test", "prompt": prompt},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "Autonomous" in data["name"] or "Gmail" in data["name"]
        assert len(data["graph"]["nodes"]) >= 3
        assert len(data["graph"]["edges"]) >= 2


@pytest.mark.asyncio
async def test_workflow_execution_dispatch():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        unique_email = f"executor_{pytest.importorskip('uuid').uuid4().hex[:6]}@flowpilot.ai"
        reg = await ac.post(
            "/api/v1/auth/register",
            json={"email": unique_email, "password": "Password123!", "full_name": "Executor User"},
        )
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        workspace = await ac.get("/api/v1/workspaces/", headers=headers)
        assert workspace.status_code == 200

        workflow = await ac.post(
            "/api/v1/workflows/",
            json={
                "name": "Execution Regression Workflow",
                "description": "Verifies workflow dispatch.",
                "workspace_id": workspace.json()[0]["id"],
                "graph": {
                    "nodes": [
                        {
                            "id": "trigger",
                            "type": "manualTrigger",
                            "label": "Manual Trigger",
                            "position": {"x": 0, "y": 0},
                            "config": {},
                        }
                    ],
                    "edges": [],
                },
            },
            headers=headers,
        )
        assert workflow.status_code == 201

        with patch("app.api.v1.workflows.WorkflowExecutionRunner.start_execution") as start_execution:
            start_execution.return_value = None
            response = await ac.post(
                f"/api/v1/workflows/{workflow.json()['id']}/execute",
                headers=headers,
            )
        assert response.status_code == 202
        assert response.json()["status"] == "QUEUED"
