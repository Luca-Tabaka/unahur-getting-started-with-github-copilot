from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    with TestClient(app) as test_client:
        yield test_client
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index(client):
    # Arrange
    path = "/"

    # Act
    response = client.get(path, follow_redirects=False)

    # Assert
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_catalog(client):
    # Arrange
    path = "/activities"

    # Act
    response = client.get(path)

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert "Chess Club" in body
    assert "participants" in body["Chess Club"]


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    path = f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"

    # Act
    response = client.post(path)

    # Assert
    assert response.status_code == 200
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    existing_email = activities["Chess Club"]["participants"][0]
    path = f"/activities/{activity_name.replace(' ', '%20')}/signup?email={existing_email}"

    # Act
    response = client.post(path)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_unknown_activity(client):
    # Arrange
    path = "/activities/Unknown%20Club/signup?email=test@mergington.edu"

    # Act
    response = client.post(path)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_success(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    path = f"/activities/{activity_name.replace(' ', '%20')}/participants?email={email}"

    # Act
    response = client.delete(path)

    # Assert
    assert response.status_code == 200
    assert email not in activities[activity_name]["participants"]


def test_remove_participant_rejects_missing_email(client):
    # Arrange
    path = "/activities/Chess%20Club/participants?email=missing@mergington.edu"

    # Act
    response = client.delete(path)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"


def test_remove_participant_rejects_unknown_activity(client):
    # Arrange
    path = "/activities/Unknown%20Club/participants?email=test@mergington.edu"

    # Act
    response = client.delete(path)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"