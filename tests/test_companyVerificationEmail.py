import asyncio
import importlib
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

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

scenarios("features/companyVerificationEmail.feature")


EMAIL = "hr@abctech.com"
COMPANY_NAME = "ABC Technology Sdn. Bhd."


# ============================================================
# TEST CONTEXT
# ============================================================


class Context:

    def __init__(self):
        self.sent_messages = []
        self.error = None
        self.fail_send = False


@pytest.fixture
def context():
    return Context()


# ============================================================
# FAKE FASTMAIL
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
            if context.fail_send:
                raise RuntimeError("Email service unavailable")

            context.sent_messages.append(message)

    monkeypatch.setattr(
        email_module,
        "FastMail",
        FakeFastMail,
    )


# ============================================================
# HELPERS
# ============================================================


def send_email(
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


def message_recipients(message):
    recipients = []

    for recipient in message.recipients:

        # FastAPI-Mail converts recipient strings
        # into NameEmail objects.
        if hasattr(recipient, "email"):
            recipients.append(str(recipient.email))
        else:
            recipients.append(str(recipient))

    return recipients


# ============================================================
# DIRECT PYTEST TESTS
# ============================================================


def test_approved_verification_email(
    context,
):
    send_email("Approved")

    message = latest_message(context)

    assert message.subject == "Company Verification Approved - JobConnect"

    assert COMPANY_NAME in message.body

    assert "Your company verification has been approved." in message.body

    assert EMAIL in message_recipients(message)


def test_rejected_verification_email_with_reason(
    context,
):
    send_email(
        "Rejected",
        reason="Invalid SSM document",
    )

    message = latest_message(context)

    assert message.subject == "Company Verification Rejected - JobConnect"

    assert "Invalid SSM document" in message.body


def test_rejected_without_reason(
    context,
):
    send_email("Rejected")

    message = latest_message(context)

    assert "Reason:" not in message.body


def test_other_status_email(
    context,
):
    send_email("Pending Review")

    message = latest_message(context)

    assert message.subject == "Company Verification Status Updated - JobConnect"

    assert "Pending Review" in message.body


def test_email_failure_is_raised(
    context,
):
    context.fail_send = True

    with pytest.raises(
        RuntimeError,
        match="Email service unavailable",
    ):
        send_email("Approved")


# ============================================================
# BDD GIVEN
# ============================================================


@given("a company verification email recipient exists")
def recipient_exists(
    context,
):
    context.fail_send = False


@given("the email service fails")
def email_service_fails(
    context,
):
    context.fail_send = True


# ============================================================
# BDD WHEN
# ============================================================


@when("the company verification status is Approved")
def status_approved(
    context,
):
    send_email("Approved")


@when("the company verification status is Rejected with a reason")
def status_rejected_reason(
    context,
):
    send_email(
        "Rejected",
        reason="Invalid SSM document",
    )


@when("the company verification status is Rejected without a reason")
def status_rejected_no_reason(
    context,
):
    send_email("Rejected")


@when("the company verification status is Pending Review")
def status_pending_review(
    context,
):
    send_email("Pending Review")


@when("the company verification status is Approved expecting an error")
def approved_error(
    context,
):
    try:
        send_email("Approved")

    except Exception as exc:
        context.error = exc


# ============================================================
# BDD THEN
# ============================================================


@then("an approval email should be sent")
def approval_sent(
    context,
):
    assert len(context.sent_messages) == 1


@then("the approval email subject should be correct")
def approval_subject(
    context,
):
    message = latest_message(context)

    assert message.subject == "Company Verification Approved - JobConnect"


@then("the approval email should contain the company name")
def approval_company_name(
    context,
):
    message = latest_message(context)

    assert COMPANY_NAME in message.body


@then("the approval email should explain that the company was approved")
def approval_content(
    context,
):
    message = latest_message(context)

    assert "Your company verification has been approved." in message.body


@then("a rejection email should be sent")
def rejection_sent(
    context,
):
    assert len(context.sent_messages) == 1


@then("the rejection email subject should be correct")
def rejection_subject(
    context,
):
    message = latest_message(context)

    assert message.subject == "Company Verification Rejected - JobConnect"


@then("the rejection email should contain the rejection reason")
def rejection_reason(
    context,
):
    message = latest_message(context)

    assert "Reason:" in message.body

    assert "Invalid SSM document" in message.body


@then("a rejection email should still be sent")
def rejection_without_reason_sent(
    context,
):
    assert len(context.sent_messages) == 1


@then("the rejection email should not contain a reason section")
def no_reason_section(
    context,
):
    message = latest_message(context)

    assert "Reason:" not in message.body


@then("a status update email should be sent")
def status_email_sent(
    context,
):
    assert len(context.sent_messages) == 1

    message = latest_message(context)

    assert message.subject == "Company Verification Status Updated - JobConnect"


@then("the email should contain the current verification status")
def current_status_in_email(
    context,
):
    message = latest_message(context)

    assert "Pending Review" in message.body


@then("the verification email should be sent to the correct email address")
def correct_email_address(
    context,
):
    message = latest_message(context)

    assert EMAIL in message_recipients(message)


@then("the email sending error should be raised")
def sending_error_raised(
    context,
):
    assert context.error is not None

    assert isinstance(
        context.error,
        RuntimeError,
    )

    assert str(context.error) == "Email service unavailable"
