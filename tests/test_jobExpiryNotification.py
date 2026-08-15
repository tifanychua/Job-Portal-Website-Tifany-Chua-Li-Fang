import importlib
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from pathlib import Path

import pytest
from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)

# ============================================================
# LOAD NOTIFICATION MODULE
# ============================================================


def load_notification_module():

    backend_dir = Path("src/job_portal_web/backend")

    for path in backend_dir.rglob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if "def check_job_expiry_notifications(" in text:
            module_path = path.relative_to("src").with_suffix("")

            module_name = ".".join(module_path.parts)

            return importlib.import_module(module_name)

    raise ImportError("Could not find check_job_expiry_notifications().")


notification_module = load_notification_module()


scenarios("features/jobExpiryNotification.feature")


# ============================================================
# CONSTANTS
# ============================================================

COMPANY_ID = "COMPANY001"

JOB_ID = "JOB001"

MYT = timezone(timedelta(hours=8))


# ============================================================
# FAKE FIRESTORE
# ============================================================


class FakeSnapshot:
    def __init__(
        self,
        document_id,
        data,
        reference,
    ):

        self.id = document_id
        self._data = data
        self.reference = reference

        self.exists = data is not None

    def to_dict(self):

        return dict(self._data or {})


class FakeDocumentReference:
    def __init__(
        self,
        collection,
        document_id,
    ):

        self.collection = collection

        self.document_id = document_id

    def get(self):

        data = self.collection.documents.get(self.document_id)

        return FakeSnapshot(
            self.document_id,
            data,
            self,
        )

    def update(
        self,
        values,
    ):

        self.collection.documents.setdefault(
            self.document_id,
            {},
        ).update(values)


class FakeQuery:
    def __init__(
        self,
        collection,
        filters=None,
    ):

        self.collection = collection

        self.filters = filters or []

    def where(
        self,
        *args,
        **kwargs,
    ):

        if "filter" in kwargs:
            field_filter = kwargs["filter"]

            field = field_filter.field_path

            operator = field_filter.op_string

            value = field_filter.value

        else:
            field = args[0]

            operator = args[1]

            value = args[2]

        return FakeQuery(
            self.collection,
            self.filters
            + [
                (
                    field,
                    operator,
                    value,
                )
            ],
        )

    def stream(self):

        results = []

        for (
            document_id,
            data,
        ) in self.collection.documents.items():
            matched = True

            for (
                field,
                operator,
                expected,
            ) in self.filters:
                if operator == "==" and data.get(field) != expected:
                    matched = False

                    break

            if matched:
                reference = FakeDocumentReference(
                    self.collection,
                    document_id,
                )

                results.append(
                    FakeSnapshot(
                        document_id,
                        data,
                        reference,
                    )
                )

        return iter(results)


class FakeCollection:
    def __init__(
        self,
        documents=None,
    ):

        self.documents = dict(documents or {})

        self.added = []

    def stream(self):

        result = []

        for (
            document_id,
            data,
        ) in self.documents.items():
            reference = FakeDocumentReference(
                self,
                document_id,
            )

            result.append(
                FakeSnapshot(
                    document_id,
                    data,
                    reference,
                )
            )

        return iter(result)

    def where(
        self,
        *args,
        **kwargs,
    ):

        return FakeQuery(self).where(
            *args,
            **kwargs,
        )

    def document(
        self,
        document_id,
    ):

        return FakeDocumentReference(
            self,
            document_id,
        )

    def add(
        self,
        data,
    ):

        self.added.append(dict(data))

        notification_id = f"NOTIF{len(self.added):03d}"

        self.documents[notification_id] = dict(data)

        return (
            FakeDocumentReference(
                self,
                notification_id,
            ),
            None,
        )


class FakeDB:
    def __init__(
        self,
        jobs=None,
        notifications=None,
    ):

        self.collections = {
            "job_list": FakeCollection(jobs or {}),
            "notification": FakeCollection(notifications or {}),
        }

    def collection(
        self,
        name,
    ):

        return self.collections[name]


# ============================================================
# CONTEXT
# ============================================================


class Context:
    def __init__(self):

        self.db = None

        self.notification = None

        self.redirect_url = None


@pytest.fixture
def context():

    return Context()


# ============================================================
# HELPERS
# ============================================================


def expiry_in_three_days():

    today = datetime.now(MYT).date()

    expiry_date = today + timedelta(days=3)

    return datetime(
        expiry_date.year,
        expiry_date.month,
        expiry_date.day,
        23,
        59,
        tzinfo=MYT,
    )


def install_db(
    monkeypatch,
    context,
):

    jobs = {
        JOB_ID: {
            "company_id": COMPANY_ID,
            "job_title": "Software Engineer",
            "status": "Active",
            "expiry_date": expiry_in_three_days(),
        }
    }

    context.db = FakeDB(
        jobs=jobs,
        notifications={},
    )

    monkeypatch.setattr(
        notification_module,
        "db",
        context.db,
    )


def generated_notification(
    context,
):

    notifications = context.db.collection("notification").added

    assert len(notifications) == 1

    return notifications[0]


# ============================================================
# GIVEN
# ============================================================


@given("the employer has an active job posting with an upcoming expiry date")
def active_job_upcoming_expiry(
    monkeypatch,
    context,
):

    install_db(
        monkeypatch,
        context,
    )


@given("the employer has received a job posting expiry notification")
def employer_received_notification(
    monkeypatch,
    context,
):

    install_db(
        monkeypatch,
        context,
    )

    notification_module.check_job_expiry_notifications()

    context.notification = generated_notification(context)


# ============================================================
# WHEN
# ============================================================


@when("the expiry date is approaching")
def expiry_approaching(
    context,
):

    notification_module.check_job_expiry_notifications()


@when("the employer clicks on the notification")
def click_notification(
    context,
):

    assert context.notification is not None

    context.redirect_url = context.notification["link"]


# ============================================================
# THEN
# ============================================================


@then(
    "the system should display a notification to the employer reminding them that the job posting will expire soon"
)
def expiry_notification_displayed(
    context,
):

    notification = generated_notification(context)

    assert notification["user_id"] == COMPANY_ID

    assert notification["job_id"] == JOB_ID

    assert notification["event"] == "expire_3_days"

    assert notification["title"] == "Job Posting Expiring Soon"

    assert "Software Engineer" in notification["message"]

    assert "expire in 3 days" in notification["message"]

    assert notification["is_read"] is False


@then("the system should redirect the employer to the job posting management page")
def redirect_to_manage_jobs(
    context,
):

    assert context.redirect_url == "/manage-jobs"
