from fastapi.testclient import TestClient

from job_portal_web.backend.main import app

client = TestClient(app)


def test_reschedule_interview_success():
    """
    Scenario: Employer updates interview schedule

    Given the employer has a scheduled interview
    When the employer changes the interview date and time
    And confirms the reschedule request
    Then the interview schedule should be updated successfully
    """

    interview_id = "WGHcFQI8s6URdhusEbGW"

    updated_interview = {
        "stage": "Technical Interview",
        "date": "2026-07-25",
        "time": "14:00",
        "duration": "60 Minutes",
        "interviewType": "online",
        "interviewer": "John",
        "meetingLink": "https://meet.google.com/test",
        "notes": "Updated interview schedule",
        "status": "Rescheduled",
    }

    response = client.put(f"/api/interviews/{interview_id}", json=updated_interview)

    assert response.status_code == 200

    assert response.json()["message"] == ("Interview rescheduled successfully!")


# ==========================================
# Test 2: Verify updated details are saved
# ==========================================


def test_updated_interview_saved():
    """
    Scenario: Save updated interview schedule

    Given the employer has rescheduled an interview
    When the update process is completed
    Then the new interview details should be saved in the database
    """

    interview_id = "WGHcFQI8s6URdhusEbGW"

    updated_data = {
        "stage": "Final Interview",
        "date": "2026-08-01",
        "time": "10:00",
        "duration": "30 Minutes",
        "interviewType": "physical",
        "interviewer": "Sarah",
        "meetingLink": "",
        "notes": "Face-to-face interview",
        "status": "Rescheduled",
    }

    # Update interview

    response = client.put(f"/api/interviews/{interview_id}", json=updated_data)

    assert response.status_code == 200

    # Retrieve updated interview

    get_response = client.get(f"/api/interviews/{interview_id}")

    assert get_response.status_code == 200

    interview = get_response.json()

    assert interview["date"] == "2026-08-01"

    assert interview["time"] == "10:00"

    assert interview["status"] == "Rescheduled"


# ==========================================
# Test 3: Invalid update data
# ==========================================


def test_reschedule_interview_invalid_data():
    """
    Scenario: Employer submits incomplete reschedule information

    Given the employer is updating an interview
    When required information is missing
    Then the system should reject the request
    """

    interview_id = "WGHcFQI8s6URdhusEbGW"

    invalid_data = {"date": "", "time": ""}

    response = client.put(f"/api/interviews/{interview_id}", json=invalid_data)

    assert response.status_code == 422
