"""Shared in-memory Firestore/Storage test doubles.

The real backend talks to a live Firestore project (see
``job_portal_web.backend.database``), which is not reachable from an
isolated test environment and would make the acceptance/unit tests
non-deterministic (shared state, network flakiness). These fakes provide
just enough of the ``google-cloud-firestore`` client surface -- collection /
document / where / stream / get / set / update / delete / add / batch --
for the routes exercised by the tests in this folder.

Usage in a test file::

    from fakes import FakeFirestore, patch_db_everywhere

    @pytest.fixture
    def fake_db(monkeypatch):
        fake_db = FakeFirestore()
        patch_db_everywhere(monkeypatch, fake_db)
        return fake_db
"""

from __future__ import annotations

import importlib
import itertools

# ======================================================================
# Firestore-like primitives
# ======================================================================


class FakeSnapshot:
    def __init__(self, doc_id, data, exists):
        self.id = doc_id
        self._data = dict(data) if data else {}
        self.exists = exists

    def to_dict(self):
        return dict(self._data) if self._data else {}


class FakeDocumentRef:
    def __init__(self, collection: FakeCollection, doc_id: str):
        self._collection = collection
        self.id = doc_id

    def get(self):
        data = self._collection._docs.get(self.id)
        return FakeSnapshot(self.id, data, data is not None)

    def set(self, data, merge=False):
        if merge and self.id in self._collection._docs:
            self._collection._docs[self.id].update(data)
        else:
            self._collection._docs[self.id] = dict(data)
        return self

    def update(self, data):
        existing = self._collection._docs.setdefault(self.id, {})
        existing.update(data)
        return self

    def delete(self):
        self._collection._docs.pop(self.id, None)


class _FieldFilterLike:
    """Duck-typed stand-in for google.cloud.firestore_v1.base_query.FieldFilter,
    also accepts the (field, op, value) positional legacy form."""

    def __init__(self, field_path, op_string, value):
        self.field_path = field_path
        self.op_string = op_string
        self.value = value


def _matches(data, condition):
    field = getattr(condition, "field_path", None)
    op = getattr(condition, "op_string", "==")
    value = getattr(condition, "value", None)

    actual = data.get(field)

    if op == "==":
        return actual == value
    if op == "!=":
        return actual != value
    if op == "in":
        return actual in value
    if op == "not-in":
        return actual not in value
    if op == ">":
        return actual is not None and actual > value
    if op == ">=":
        return actual is not None and actual >= value
    if op == "<":
        return actual is not None and actual < value
    if op == "<=":
        return actual is not None and actual <= value

    raise NotImplementedError(f"Unsupported fake-Firestore operator: {op}")


class _FakeQuery:
    def __init__(self, collection: FakeCollection, conditions):
        self._collection = collection
        self._conditions = conditions

    def where(self, *args, filter=None, **kwargs):
        condition = filter

        if condition is None and args:
            field, op, value = args
            condition = _FieldFilterLike(field, op, value)

        return _FakeQuery(self._collection, [*self._conditions, condition])

    def stream(self):
        results = []

        for doc_id, data in list(self._collection._docs.items()):
            if all(_matches(data, condition) for condition in self._conditions):
                results.append(FakeSnapshot(doc_id, data, True))

        return results

    def get(self):
        return self.stream()

    def limit(self, _n):
        return self


class FakeCollection:
    def __init__(self, name):
        self.name = name
        self._docs: dict[str, dict] = {}
        self._counter = itertools.count(1)

    def document(self, doc_id: str | None = None):
        if doc_id is None:
            doc_id = f"{self.name}_auto_{next(self._counter)}"

        return FakeDocumentRef(self, doc_id)

    def add(self, data):
        doc_id = f"{self.name}_auto_{next(self._counter)}"
        self._docs[doc_id] = dict(data)

        return (None, FakeDocumentRef(self, doc_id))

    def where(self, *args, filter=None, **kwargs):
        return _FakeQuery(self, []).where(*args, filter=filter, **kwargs)

    def stream(self):
        return [FakeSnapshot(doc_id, data, True) for doc_id, data in list(self._docs.items())]

    def get(self):
        return self.stream()


class FakeBatch:
    def __init__(self):
        self._ops = []

    def update(self, ref, data):
        self._ops.append((ref, data))

    def set(self, ref, data, merge=False):
        self._ops.append((ref, data))

    def delete(self, ref):
        self._ops.append((ref, None))

    def commit(self):
        for ref, data in self._ops:
            if data is None:
                ref.delete()
            else:
                ref.update(data)

        self._ops = []


class FakeFirestore:
    """Stand-in for ``firestore.client()``."""

    def __init__(self):
        self._collections: dict[str, FakeCollection] = {}

    def collection(self, name):
        if name not in self._collections:
            self._collections[name] = FakeCollection(name)

        return self._collections[name]

    def batch(self):
        return FakeBatch()

    # -- test convenience -------------------------------------------------

    def seed(self, collection: str, doc_id: str, data: dict):
        """Directly write a document, bypassing any route logic. Handy for
        Gherkin ``Given`` steps that set up pre-existing state."""

        self.collection(collection).document(doc_id).set(data)
        return doc_id

    def get(self, collection: str, doc_id: str):
        return self.collection(collection).document(doc_id).get().to_dict()

    def exists(self, collection: str, doc_id: str) -> bool:
        return self.collection(collection).document(doc_id).get().exists


# ======================================================================
# Storage fakes (resume uploads / signed URLs)
# ======================================================================


class FakeBlob:
    def __init__(self, name="fake-blob"):
        self.name = name
        self._uploaded = None

    def upload_from_string(self, contents, content_type=None):
        self._uploaded = contents

    def generate_signed_url(self, **kwargs):
        return f"https://example.com/{self.name}"

    def exists(self):
        return True


class FakeBucket:
    def blob(self, path):
        return FakeBlob(path)


# ======================================================================
# Cross-module patching helper
# ======================================================================

# Every backend module that imports `db` (or `bucket`) at module scope.
# Functions look up `db` in the globals of the module where they are
# *defined*, not where they are called from, so a page like /saved-jobs
# that calls into notifications.get_unread_notifications_count() needs
# notifications.db patched too, even though the test is "about" saved_job.py.
_DB_MODULES = [
    "job_portal_web.backend.notifications",
    "job_portal_web.backend.saved_job",
    "job_portal_web.backend.job_information",
    "job_portal_web.backend.job_apply",
    "job_portal_web.backend.job_application",
    "job_portal_web.backend.applicant",
    "job_portal_web.backend.interview",
    "job_portal_web.backend.main",
    "job_portal_web.backend.routes.employerApplication",
]


def patch_db_everywhere(monkeypatch, fake_db, bucket=None):
    """Point every backend module's module-level `db` (and `bucket`, if
    given) at the same fake instance, so a single request that crosses
    module boundaries stays internally consistent."""

    for name in _DB_MODULES:
        module = importlib.import_module(name)

        monkeypatch.setattr(module, "db", fake_db, raising=False)

        if bucket is not None:
            monkeypatch.setattr(module, "bucket", bucket, raising=False)
