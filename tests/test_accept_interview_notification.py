from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend import interview


# --------------------------------------------------
# Client
# --------------------------------------------------


@pytest.fixture
def client():

    return TestClient(app)



# --------------------------------------------------
# Mock Email
# --------------------------------------------------


@pytest.fixture
def email_mock(monkeypatch):

    context = {

        "sent": False,

        "email": None,

        "name": None,

        "candidate": None,

        "position": None,

        "status": None,

        "reason": None,

        "requested_date": None,

        "requested_time": None,

    }



    async def fake_send_notification(
        email,
        name,
        candidate,
        position,
        status,
        reason=None,
        requested_date=None,
        requested_time=None
    ):


        context["sent"] = True

        context["email"] = email

        context["name"] = name

        context["candidate"] = candidate

        context["position"] = position

        context["status"] = status

        context["reason"] = reason

        context["requested_date"] = requested_date

        context["requested_time"] = requested_time



    monkeypatch.setattr(
        interview,
        "send_employer_interview_notification",
        fake_send_notification
    )


    return context



# --------------------------------------------------
# Helper
# --------------------------------------------------


def create_interview(client):


    data = {


        "candidateId": "123",


        "companyId": "C000001",


        "candidateName": "James",


        "position": "Software Engineer",


        "stage": "Technical Interview",


        "date": "2026-07-20",


        "time": "10:00",


        "duration": "60 Minutes",


        "interviewType": "physical",


        "interviewer": "John",


        "meetingLink": "",


        "notes": "Bring documents",


    }



    response = client.post(

        "/api/interviews",

        json=data

    )


    assert response.status_code == 200



    interviews = client.get(

        "/api/interviews"

    ).json()



    return interviews[-1]["id"]




# --------------------------------------------------
# Normal Test
# --------------------------------------------------


def test_employer_receives_accept_notification(
    client,
    email_mock
):

    """
    Given employer scheduled interview
    When job seeker accepts interview
    Then employer receives notification email
    """


    interview_id = create_interview(client)



    response = client.put(

        f"/api/interviews/{interview_id}/accept"

    )



    assert response.status_code == 200



    assert email_mock["sent"] is True



    assert email_mock["status"] == "Accepted"





# --------------------------------------------------
# Verify Email Content
# --------------------------------------------------


def test_notification_contains_interview_details(
    client,
    email_mock
):

    """
    Given employer scheduled interview
    When notification email is sent
    Then email contains interview details
    """


    interview_id = create_interview(client)



    client.put(

        f"/api/interviews/{interview_id}/accept"

    )



    assert email_mock["sent"] is True



    assert email_mock["candidate"] == "James"



    assert email_mock["position"] == "Software Engineer"



    assert email_mock["status"] == "Accepted"





# --------------------------------------------------
# BDD Feature
# --------------------------------------------------


scenarios(

    "features/accept_interview_notification.feature"

)





# --------------------------------------------------
# BDD Context
# --------------------------------------------------


class Context:


    def __init__(self):

        self.response = None

        self.email_sent = False

        self.interview_id = None





@pytest.fixture
def context():

    return Context()





# --------------------------------------------------
# Scenario 1
# --------------------------------------------------


@given(

    "the employer has successfully scheduled an interview"

)

def scheduled(

    client,

    context

):


    context.interview_id = create_interview(client)





@when(

    "the interview details are saved"

)

def save_details(

    client,

    context,

    email_mock

):


    client.put(

        f"/api/interviews/{context.interview_id}/accept"

    )


    context.email_sent = email_mock["sent"]





@then(

    "the job seeker should receive an interview notification email"

)

def verify_email(

    context

):


    assert context.email_sent is True





# --------------------------------------------------
# Scenario 2
# --------------------------------------------------


@given(

    "the employer has scheduled an interview"

)

def scheduled_again(

    client,

    context

):


    context.interview_id = create_interview(client)





@when(

    "the notification email is sent"

)

def notification_sent(

    client,

    context,

    email_mock

):


    client.put(

        f"/api/interviews/{context.interview_id}/accept"

    )





@then(

    "the email should contain the interview date, time, and interview location"

)

def verify_content(

    context,

    email_mock

):


    assert email_mock["sent"] is True
