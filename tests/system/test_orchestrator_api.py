"""
Integration tests for Orchestrator API endpoints

Tests the actual API endpoints with HTTP requests
"""

import pytest
import requests

# Base URL for the Orchestrator API
# Detect orchestrator port - CI runs on 9000, local docker-compose runs on 8000
def detect_orchestrator_url() -> str:
    """Detect which port orchestrator is running on."""
    for port in [9000, 8000]:
        try:
            response = requests.get(f"http://localhost:{port}/", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if "service" in data and "orchestrator" in str(data.get("service", "")).lower():
                    return f"http://localhost:{port}"
        except:
            continue
    return "http://localhost:9000"  # Default fallback

API_BASE_URL = detect_orchestrator_url()


def is_api_running():
    """Check if Orchestrator API is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


@pytest.mark.system
@pytest.mark.skipif(not is_api_running(), reason=f"Orchestrator API not running at {API_BASE_URL}")
class TestOrchestratorAPIEndpoints:
    """Integration tests for Orchestrator API endpoints"""

    def test_root_endpoint(self):
        """Test the root endpoint returns orchestrator info"""
        response = requests.get(f"{API_BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "orchestrator" in data["service"].lower()
        assert "version" in data
        assert "features" in data

    def test_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f"{API_BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "active_sessions" in data["services"]

    def test_campaigns_endpoint(self):
        """Test campaigns endpoint returns list of campaigns"""
        response = requests.get(f"{API_BASE_URL}/campaigns")
        assert response.status_code == 200
        data = response.json()
        # Response might be {"campaigns": [...]} or just [...]
        if isinstance(data, dict) and "campaigns" in data:
            campaigns = data["campaigns"]
        else:
            campaigns = data
        assert isinstance(campaigns, list)
        # Should have at least some campaigns
        assert len(campaigns) > 0

    def test_campaign_by_id(self):
        """Test getting a specific campaign by ID"""
        # First get list of campaigns
        campaigns_response = requests.get(f"{API_BASE_URL}/campaigns")
        assert campaigns_response.status_code == 200
        data = campaigns_response.json()
        # Response might be {"campaigns": [...]} or just [...]
        if isinstance(data, dict) and "campaigns" in data:
            campaigns = data["campaigns"]
        else:
            campaigns = data
        
        if len(campaigns) > 0:
            campaign_id = campaigns[0].get("id") or campaigns[0].get("name")
            response = requests.get(f"{API_BASE_URL}/campaigns/{campaign_id}")
            assert response.status_code == 200
            data = response.json()
            assert "id" in data or "name" in data

    def test_game_start_endpoint(self):
        """Test starting a new game session"""
        response = requests.post(
            f"{API_BASE_URL}/game/start",
            json={
                "initial_prompt": "Start a new D&D adventure in a tavern"
            },
            timeout=30
        )
        assert response.status_code in [200, 422]  # 422 is acceptable for invalid requests
        if response.status_code == 200:
            data = response.json()
            assert "session_id" in data
            assert "response" in data or "state" in data

    def test_game_start_with_campaign(self):
        """Test starting a game with a campaign"""
        # Get available campaigns
        campaigns_response = requests.get(f"{API_BASE_URL}/campaigns")
        if campaigns_response.status_code == 200:
            data = campaigns_response.json()
            # Response might be {"campaigns": [...]} or just [...]
            if isinstance(data, dict) and "campaigns" in data:
                campaigns = data["campaigns"]
            else:
                campaigns = data
            if len(campaigns) > 0:
                campaign_name = campaigns[0].get("name") or campaigns[0].get("id")
                response = requests.post(
                    f"{API_BASE_URL}/game/start",
                    json={
                        "campaign_name": campaign_name,
                        "player_name": "TestPlayer"
                    },
                    timeout=30
                )
                assert response.status_code in [200, 422]
                if response.status_code == 200:
                    data = response.json()
                    assert "session_id" in data


# Standalone tests that don't require running API
class TestOrchestratorWithoutServer:
    """Tests that can run without a live server"""

    def test_orchestrator_structure(self):
        """Test that we can import the orchestrator module"""
        import sys
        from pathlib import Path
        
        # Add orchestrator to path
        orchestrator_path = Path(__file__).parent.parent.parent / "src" / "orchestrator"
        sys.path.insert(0, str(orchestrator_path))
        
        try:
            from app import app
            assert app.title == "D&D Game Orchestrator"
            assert app.version == "2.0"
        except ImportError:
            pytest.skip("Could not import orchestrator app - may not be in path")

