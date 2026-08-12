from datetime import datetime, timedelta, timezone
import importlib
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

# ============================================================
# LOAD ACTUAL NOTIFICATION MODULE
# ============================================================


def load_notification_module():
    routes_dir = Path("src/job_portal_web/backend")

    for path in routes_dir.rglob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if "def check_job_expiry_notifications(" in text:
            # The uploaded source imports:
            # from .database import db
            module_path = path.relative_to("src").with_suffix("")

            module_name = ".".join(module_path.parts)

            return importlib.import_module(module_name)

    raise ImportError(
        "Could not find the notification module " "containing check_job_expiry_notifications()."
    )


notification_module = load_notification_module()

scenarios("features/jobExpiryNotification.feature")


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

    def update(self, values):
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
            field, operator, value = args

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

        for document_id, data in self.collection.documents.items():
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

        for document_id, data in self.documents.items():
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

        new_id = f"NOTIF{len(self.added):03d}"

        self.documents[new_id] = dict(data)

        return (
            FakeDocumentReference(
                self,
                new_id,
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


@pytest.fixture
def context():
    return Context()


# ============================================================
# HELPERS
# ============================================================


def expiry_datetime(
    days_from_today,
):
    today = datetime.now(MYT).date()

    expiry_date = today + timedelta(days=days_from_today)

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
    jobs,
    notifications=None,
):
    context.db = FakeDB(
        jobs=jobs,
        notifications=notifications,
    )

    monkeypatch.setattr(
        notification_module,
        "db",
        context.db,
    )


def current_notifications(
    context,
):
    return context.db.collection("notification").documents


def new_notifications(
    context,
):
    return context.db.collection("notification").added


# ============================================================
# BDD GIVEN
# ============================================================


@given("an active job will expire in three days")
def active_job_three_days(
    monkeypatch,
    context,
):
    install_db(
        monkeypatch,
        context,
        {
            JOB_ID: {
                "company_id": COMPANY_ID,
                "job_title": "Software Engineer",
                "status": "Active",
                "expiry_date": expiry_datetime(3),
            }
        },
    )


@given("an active job expires today")
def active_job_today(
    monkeypatch,
    context,
):
    install_db(
        monkeypatch,
        context,
        {
            JOB_ID: {
                "company_id": COMPANY_ID,
                "job_title": "Software Engineer",
                "status": "Active",
                "expiry_date": expiry_datetime(0),
            }
        },
    )


@given("the three day expiry notification already exists")
def duplicate_exists(
    context,
):
    context.db.collection("notification").documents["EXISTING001"] = {
        "user_id": COMPANY_ID,
        "job_id": JOB_ID,
        "event": "expire_3_days",
        "type": "job_alert",
        "title": "Job Posting Expiring Soon",
        "message": ("Your job posting " '"Software Engineer" ' "will expire in 3 days."),
        "link": "/manage-jobs",
        "is_read": False,
    }


@given("an inactive job will expire in three days")
def inactive_job(
    monkeypatch,
    context,
):
    install_db(
        monkeypatch,
        context,
        {
            JOB_ID: {
                "company_id": COMPANY_ID,
                "job_title": "Software Engineer",
                "status": "Closed",
                "expiry_date": expiry_datetime(3),
            }
        },
    )


@given("an active job does not have an expiry date")
def no_expiry_date(
    monkeypatch,
    context,
):
    install_db(
        monkeypatch,
        context,
        {
            JOB_ID: {
                "company_id": COMPANY_ID,
                "job_title": "Software Engineer",
                "status": "Active",
            }
        },
    )


@given("an active job will expire in five days")
def active_job_five_days(
    monkeypatch,
    context,
):
    install_db(
        monkeypatch,
        context,
        {
            JOB_ID: {
                "company_id": COMPANY_ID,
                "job_title": "Software Engineer",
                "status": "Active",
                "expiry_date": expiry_datetime(5),
            }
        },
    )


# ============================================================
# BDD WHEN
# ============================================================


@when("the system checks job expiry notifications")
def check_expiry_notifications(
    context,
):
    notification_module.check_job_expiry_notifications()


# ============================================================
# BDD THEN
# ============================================================


@then("a three day expiry notification should be created")
def verify_three_day_notification(
    context,
):
    added = new_notifications(context)

    assert len(added) == 1

    notification = added[0]

    assert notification["event"] == "expire_3_days"

    assert notification["title"] == "Job Posting Expiring Soon"

    assert (
        notification["message"] == "Your job posting "
        '"Software Engineer" '
        "will expire in 3 days."
    )


@then("the notification should link to manage jobs")
def verify_manage_jobs_link(
    context,
):
    notification = new_notifications(context)[0]

    assert notification["link"] == "/manage-jobs"

    assert notification["type"] == "job_alert"


@then("the notification should be unread")
def verify_unread(
    context,
):
    assert new_notifications(context)[0]["is_read"] is False


@then("an expiry today notification should be created")
def verify_today_notification(
    context,
):
    added = new_notifications(context)

    assert len(added) == 1

    notification = added[0]

    assert notification["event"] == "expire_today"

    assert notification["title"] == "Job Posting Expires Today"

    assert notification["message"] == "Your job posting " '"Software Engineer" ' "expires today."


@then("the expiry notification message should contain the job title")
def verify_job_title(
    context,
):
    notification = new_notifications(context)[0]

    assert "Software Engineer" in notification["message"]


@then("another three day expiry notification should not be created")
def verify_no_duplicate(
    context,
):
    assert len(new_notifications(context)) == 0

    matching = [
        data
        for data in current_notifications(context).values()
        if (data.get("job_id") == JOB_ID and data.get("event") == "expire_3_days")
    ]

    assert len(matching) == 1


@then("no expiry notification should be created")
def verify_no_notification(
    context,
):
    assert new_notifications(context) == []


@then("the expiry notification should belong to the job company")
def verify_company(
    context,
):
    notification = new_notifications(context)[0]

    assert notification["user_id"] == COMPANY_ID

    assert notification["job_id"] == JOB_ID
