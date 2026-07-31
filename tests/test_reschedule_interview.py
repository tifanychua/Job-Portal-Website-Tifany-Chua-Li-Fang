from fastapi.testclient import TestClient

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

client = TestClient(app)


# Existing Firebase interview ID
INTERVIEW_ID = "WGHcFQI8s6URdhusEbGW"


# ==================================================
# TEST 1
# Employer updates interview schedule successfully
# ==================================================


def test_reschedule_interview_success():
    """
    Scenario:
    Given the employer has a scheduled interview
    When the employer changes the interview date and time
    And confirms the reschedule request
    Then the interview schedule should be updated successfully
    """

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

    response = client.put(f"/api/interviews/{INTERVIEW_ID}", json=updated_interview)

    print("UPDATE RESPONSE:", response.status_code, response.text)

    assert response.status_code == 200

    # Your API returns this message
    assert response.json()["message"] == ("Interview updated successfully")


# ==================================================
# TEST 2
# Verify updated interview saved in database
# ==================================================


def test_updated_interview_saved():
    """
    Scenario:
    Given the employer has rescheduled an interview
    When update process is completed
    Then new interview details should be saved in database
    """

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

    response = client.put(f"/api/interviews/{INTERVIEW_ID}", json=updated_data)

    print("UPDATE:", response.status_code, response.text)

    assert response.status_code == 200

    # ------------------------------------------
    # Check Firebase directly
    # ------------------------------------------

    document = db.collection("interviews").document(INTERVIEW_ID).get()

    assert document.exists

    interview = document.to_dict()

    print("DATABASE:", interview)

    assert interview["date"] == ("2026-08-01")

    assert interview["time"] == ("10:00")

    assert interview["status"] == ("Rescheduled")


# ==================================================
# TEST 3
# Invalid update data
# ==================================================


def test_reschedule_interview_invalid_data():
    """
    Scenario:
    Given the employer is updating an interview
    When required information is missing
    Then the system should reject the request
    """

    invalid_data = {"date": "", "time": ""}

    response = client.put(f"/api/interviews/{INTERVIEW_ID}", json=invalid_data)

    print("INVALID RESPONSE:", response.status_code, response.text)

    assert response.status_code == 422
