"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to a clean state before each test"""
    # Store original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name in activities:
        activities[name]["participants"] = original_activities[name]["participants"].copy()


class TestRoot:
    """Test root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root path redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    """Test get activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball" in data
    
    def test_get_activities_contains_expected_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_get_activities_contains_participants(self, client):
        """Test that activities have participants"""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have initial participants
        assert len(data["Chess Club"]["participants"]) > 0


class TestSignupForActivity:
    """Test signup endpoint"""
    
    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify participant was added
        response = client.get("/activities")
        activities_data = response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_multiple_students(self, client):
        """Test signing up multiple students to same activity"""
        student1 = "student1@mergington.edu"
        student2 = "student2@mergington.edu"
        
        response1 = client.post(f"/activities/Soccer/signup?email={student1}")
        assert response1.status_code == 200
        
        response2 = client.post(f"/activities/Soccer/signup?email={student2}")
        assert response2.status_code == 200
        
        # Verify both were added
        response = client.get("/activities")
        activities_data = response.json()
        participants = activities_data["Soccer"]["participants"]
        assert student1 in participants
        assert student2 in participants
    
    def test_signup_duplicate_student_fails(self, client):
        """Test that duplicate signup fails"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(f"/activities/Drama%20Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(f"/activities/Drama%20Club/signup?email={email}")
        assert response2.status_code == 400
        
        data = response2.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signup for non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_already_existing_participant(self, client):
        """Test that existing participants can't sign up again"""
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "already signed up" in data["detail"].lower()


class TestUnregisterFromActivity:
    """Test unregister endpoint"""
    
    def test_unregister_participant_success(self, client):
        """Test successful unregistration"""
        # First add a participant
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        # Verify they were added
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Now unregister
        response = client.post(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
        # Verify they were removed
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity_fails(self, client):
        """Test unregister from non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_registered_participant_fails(self, client):
        """Test unregistering someone not in activity fails"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing participant"""
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify they were removed
        response = client.get("/activities")
        assert "michael@mergington.edu" not in response.json()["Chess Club"]["participants"]


class TestActivityParticipantCountUpdates:
    """Test that participant counts update correctly"""
    
    def test_participant_count_increases_on_signup(self, client):
        """Test that participant count increases when someone signs up"""
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Soccer"]["participants"])
        
        # Sign up new participant
        client.post("/activities/Soccer/signup?email=newplayer@mergington.edu")
        
        # Get updated count
        response = client.get("/activities")
        new_count = len(response.json()["Soccer"]["participants"])
        
        assert new_count == initial_count + 1
    
    def test_participant_count_decreases_on_unregister(self, client):
        """Test that participant count decreases when someone unregisters"""
        # First add someone
        email = "temporary@mergington.edu"
        client.post(f"/activities/Soccer/signup?email={email}")
        
        # Get count after signup
        response = client.get("/activities")
        count_after_signup = len(response.json()["Soccer"]["participants"])
        
        # Unregister
        client.post(f"/activities/Soccer/unregister?email={email}")
        
        # Get count after unregister
        response = client.get("/activities")
        count_after_unregister = len(response.json()["Soccer"]["participants"])
        
        assert count_after_unregister == count_after_signup - 1


class TestAvailableSpots:
    """Test available spots calculation"""
    
    def test_available_spots_calculation(self, client):
        """Test that available spots are calculated correctly"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            max_participants = activity_details["max_participants"]
            participant_count = len(activity_details["participants"])
            available_spots = max_participants - participant_count
            
            # Verify spots is non-negative
            assert available_spots >= 0
            # Verify participant count doesn't exceed max
            assert participant_count <= max_participants
