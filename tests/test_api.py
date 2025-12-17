"""
Tests for the High School Management System API.

This module includes tests for:
- Root endpoint behavior
- Activity retrieval endpoints
- Signup to activities
- Unregistration from activities
- Integration scenarios combining multiple operations
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Save original state
    original_activities = copy.deepcopy(activities)
    
    # Reset to known state before test
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        }
    })
    
    yield
    
    # Restore original state after test
    activities.clear()
    activities.update(original_activities)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static_html(self, client):
        """Test that root path redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        
    def test_activities_have_required_fields(self, client):
        """Test that each activity has the required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant_succeeds(self, client):
        """Test successful signup of a new participant"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant_fails(self, client):
        """Test that signing up the same participant twice fails"""
        # Sign up first time
        response1 = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Try to sign up again
        response2 = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_with_url_encoded_activity_name(self, client):
        """Test signup with URL-encoded activity name"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=newcoder@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newcoder@mergington.edu" in activities_data["Programming Class"]["participants"]
    
    def test_signup_at_max_capacity_fails(self, client):
        """Test that signup fails when activity is at maximum capacity"""
        # Fill Chess Club to capacity (max 12, currently has 2)
        for i in range(10):
            response = client.post(
                f"/activities/Chess Club/signup?email=student{i}@mergington.edu"
            )
            assert response.status_code == 200
        
        # Try to add one more (should fail)
        response = client.post(
            "/activities/Chess Club/signup?email=overflow@mergington.edu"
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower() or "capacity" in response.json()["detail"].lower()


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant_succeeds(self, client):
        """Test successful unregistration of an existing participant"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant_fails(self, client):
        """Test that unregistering a non-existent participant fails"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_from_nonexistent_activity_fails(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_with_url_encoded_activity_name(self, client):
        """Test unregister with URL-encoded activity name"""
        response = client.delete(
            "/activities/Programming%20Class/unregister?email=emma@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "emma@mergington.edu" not in activities_data["Programming Class"]["participants"]


class TestIntegrationScenarios:
    """Integration tests for common user workflows"""
    
    def test_complete_signup_unregister_workflow(self, client):
        """Test complete workflow: signup then unregister with participant count verification"""
        email = "workflow@mergington.edu"
        activity = "Chess Club"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup
        after_signup = client.get("/activities")
        assert len(after_signup.json()[activity]["participants"]) == initial_count + 1
        assert email in after_signup.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregister
        after_unregister = client.get("/activities")
        assert len(after_unregister.json()[activity]["participants"]) == initial_count
        assert email not in after_unregister.json()[activity]["participants"]
    
    def test_multiple_signups_different_activities(self, client):
        """Test signing up same student for multiple activities"""
        email = "multitasker@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify student is in both activities
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Programming Class"]["participants"]
