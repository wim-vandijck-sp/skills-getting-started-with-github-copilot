"""
Tests for the Mergington High School FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to a known state after each test"""
    original_activities = {
        "Tennis Club": {
            "description": "Learn tennis skills and participate in friendly matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 16,
            "participants": ["alex@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball training and games",
            "schedule": "Mondays and Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu", "marcus@mergington.edu"]
        },
    }
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    def test_get_activities_returns_list(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Tennis Club" in data
        assert "Basketball Team" in data

    def test_activity_has_required_fields(self, client, reset_activities):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Tennis Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


class TestSignup:
    def test_signup_for_activity(self, client, reset_activities):
        """Test successfully signing up for an activity"""
        response = client.post(
            "/activities/Tennis%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        
        # Verify participant was added
        activity_response = client.get("/activities")
        activity = activity_response.json()["Tennis Club"]
        assert "newstudent@mergington.edu" in activity["participants"]

    def test_signup_duplicate_email(self, client, reset_activities):
        """Test that signing up twice with same email fails"""
        # First signup
        response1 = client.post(
            "/activities/Tennis%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Second signup with same email
        response2 = client.post(
            "/activities/Tennis%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestRemove:
    def test_remove_participant(self, client, reset_activities):
        """Test successfully removing a participant"""
        # Add a participant first
        client.post(
            "/activities/Tennis%20Club/signup?email=toremove@mergington.edu"
        )
        
        # Remove the participant
        response = client.delete(
            "/activities/Tennis%20Club/remove?email=toremove@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
        
        # Verify participant was removed
        activity_response = client.get("/activities")
        activity = activity_response.json()["Tennis Club"]
        assert "toremove@mergington.edu" not in activity["participants"]

    def test_remove_nonexistent_participant(self, client, reset_activities):
        """Test removing a participant who isn't signed up"""
        response = client.delete(
            "/activities/Tennis%20Club/remove?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_remove_from_nonexistent_activity(self, client, reset_activities):
        """Test removing from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/remove?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestRootRedirect:
    def test_root_redirects_to_static(self, client):
        """Test that GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
