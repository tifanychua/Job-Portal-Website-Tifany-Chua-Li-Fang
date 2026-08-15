import asyncio
import importlib
from pathlib import Path

import pytest
from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)

# ============================================================
# LOAD EMAIL MODULE
# ============================================================


def load_email_module():

    backend_dir = Path("src/job_portal_web/backend")

    for path in backend_dir.rglob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if "def send_company_verification_email(" in text:
            module_path = path.relative_to("src").with_suffix("")

            module_name = ".".join(module_path.parts)

            return importlib.import_module(module_name)

    raise ImportError("Could not find send_company_verification_email().")


email_module = load_email_module()


# ============================================================
# LOAD FEATURE
# ============================================================

scenarios("features/companyVerificationEmail.feature")


# ============================================================
# CONSTANTS
# ============================================================

EMAIL = "hr@abctech.com"

COMPANY_NAME = "ABC Technology Sdn. Bhd."


# ============================================================
# CONTEXT
# ============================================================


class Context:
    def __init__(self):

        self.sent_messages = []

        self.status = None

        self.reason = None


@pytest.fixture
def context():

    return Context()


# ============================================================
# MOCK FASTMAIL
# ============================================================


@pytest.fixture(autouse=True)
def mock_fastmail(
    monkeypatch,
    context,
):

    class FakeFastMail:
        def __init__(
            self,
            conf,
        ):

            self.conf = conf

        async def send_message(
            self,
            message,
        ):

            context.sent_messages.append(message)

    monkeypatch.setattr(
        email_module,
        "FastMail",
        FakeFastMail,
    )


# ============================================================
# HELPERS
# ============================================================


def send_verification_email(
    status,
    reason=None,
):

    return asyncio.run(
        email_module.send_company_verification_email(
            email=EMAIL,
            company_name=COMPANY_NAME,
            status=status,
            reason=reason,
        )
    )


def latest_message(
    context,
):

    assert len(context.sent_messages) == 1

    return context.sent_messages[0]


def recipient_emails(
    message,
):

    emails = []

    for recipient in message.recipients:
        if hasattr(
            recipient,
            "email",
        ):
            emails.append(str(recipient.email))

        else:
            emails.append(str(recipient))

    return emails


# ============================================================
# GIVEN
# ============================================================


@given("the employer has submitted a company registration request")
def registration_submitted(
    context,
):

    context.status = "Pending"


@given("the employer has received a company verification status email")
def verification_email_received(
    context,
):

    context.status = "Rejected"

    context.reason = "Invalid SSM document"

    send_verification_email(
        status=context.status,
        reason=context.reason,
    )


@given("the employer company registration request is still pending review")
def registration_pending(
    context,
):

    context.status = "Pending"


# ============================================================
# WHEN
# ============================================================


@when("the admin approves the company verification request")
def admin_approves(
    context,
):

    context.status = "Approved"

    send_verification_email(status="Approved")


@when("the admin rejects the company verification request")
def admin_rejects(
    context,
):

    context.status = "Rejected"

    context.reason = "Invalid SSM document"

    send_verification_email(
        status="Rejected",
        reason=context.reason,
    )


@when("the employer opens the email notification")
def employer_opens_email(
    context,
):

    assert len(context.sent_messages) == 1


@when("the verification status has not been updated")
def status_not_updated(
    context,
):

    # No email function should be called
    # while the verification is still pending.
    assert context.status == "Pending"


# ============================================================
# THEN
# ============================================================


@then(
    "the system should send an email notification to the employer informing them that the registration request has been approved"
)
def approval_email_sent(
    context,
):

    message = latest_message(context)

    # Email sent
    assert len(context.sent_messages) == 1

    # Correct recipient
    assert EMAIL in recipient_emails(message)

    # Correct subject
    assert message.subject == "Company Verification Approved - JobConnect"

    # Company information
    assert COMPANY_NAME in message.body

    # Approval information
    assert "approved" in message.body.lower()


@then(
    "the system should send an email notification to the employer informing them that the registration request has been rejected"
)
def rejection_email_sent(
    context,
):

    message = latest_message(context)

    # Email sent
    assert len(context.sent_messages) == 1

    # Correct recipient
    assert EMAIL in recipient_emails(message)

    # Correct subject
    assert message.subject == "Company Verification Rejected - JobConnect"

    # Company information
    assert COMPANY_NAME in message.body

    # Rejected status
    assert "rejected" in message.body.lower()


@then(
    "the email should display the verification status company information and relevant remarks if provided"
)
def verification_details_displayed(
    context,
):

    message = latest_message(context)

    # Verification status
    assert "rejected" in message.body.lower()

    # Company information
    assert COMPANY_NAME in message.body

    # Relevant remarks
    assert "Reason:" in message.body

    assert context.reason in message.body


@then("the system should not send any approval or rejection email notification")
def no_email_before_update(
    context,
):

    assert context.status == "Pending"

    assert context.sent_messages == []
