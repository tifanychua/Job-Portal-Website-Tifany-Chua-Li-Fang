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

    def get(self, retry=None, timeout=None, **kwargs):
        """Return a document snapshot.

        ``retry`` and ``timeout`` are accepted for compatibility with the
        real Firestore DocumentReference.get() method. They are not needed
        by the in-memory fake.
        """
        data = self._collection._docs.get(self.id)
        return FakeSnapshot(self.id, data, data is not None)

    def set(self, data, merge=False, retry=None, timeout=None, **kwargs):
        if merge and self.id in self._collection._docs:
            self._collection._docs[self.id].update(data)
        else:
            self._collection._docs[self.id] = dict(data)

        return self

    def update(self, data, retry=None, timeout=None, **kwargs):
        existing = self._collection._docs.setdefault(self.id, {})
        existing.update(data)
        return self

    def delete(self, retry=None, timeout=None, **kwargs):
        self._collection._docs.pop(self.id, None)


class _FieldFilterLike:
    """Duck-typed stand-in for Firestore's FieldFilter.

    It also supports the legacy positional form:

        where("field", "==", value)
    """

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
    def __init__(self, collection: FakeCollection, conditions, limit_count=None):
        self._collection = collection
        self._conditions = conditions
        self._limit_count = limit_count

    def where(self, *args, filter=None, **kwargs):
        condition = filter

        if condition is None and args:
            if len(args) != 3:
                raise TypeError("where() expects field, operator, and value")

            field, op, value = args
            condition = _FieldFilterLike(field, op, value)

        if condition is None:
            raise TypeError("where() requires either positional arguments or filter=")

        return _FakeQuery(
            self._collection,
            [*self._conditions, condition],
            self._limit_count,
        )

    def stream(self, retry=None, timeout=None, **kwargs):
        """Return matching snapshots.

        ``retry`` and ``timeout`` are accepted for compatibility with the
        real Firestore Query.stream() method.
        """
        results = []

        for doc_id, data in list(self._collection._docs.items()):
            if all(_matches(data, condition) for condition in self._conditions):
                results.append(FakeSnapshot(doc_id, data, True))

        if self._limit_count is not None:
            results = results[: self._limit_count]

        return results

    def get(self, retry=None, timeout=None, **kwargs):
        """Return matching snapshots.

        The real Firestore Query.get() accepts ``retry`` and ``timeout``.
        This fake accepts and ignores them.
        """
        return self.stream(
            retry=retry,
            timeout=timeout,
            **kwargs,
        )

    def limit(self, number):
        return _FakeQuery(
            self._collection,
            list(self._conditions),
            number,
        )


class FakeCollection:
    def __init__(self, name):
        self.name = name
        self._docs: dict[str, dict] = {}
        self._counter = itertools.count(1)

    def document(self, doc_id: str | None = None):
        if doc_id is None:
            doc_id = f"{self.name}_auto_{next(self._counter)}"

        return FakeDocumentRef(self, doc_id)

    def add(self, data, retry=None, timeout=None, **kwargs):
        doc_id = f"{self.name}_auto_{next(self._counter)}"
        self._docs[doc_id] = dict(data)

        return None, FakeDocumentRef(self, doc_id)

    def where(self, *args, filter=None, **kwargs):
        return _FakeQuery(self, []).where(
            *args,
            filter=filter,
            **kwargs,
        )

    def stream(self, retry=None, timeout=None, **kwargs):
        """Return every document in the collection."""
        return [FakeSnapshot(doc_id, data, True) for doc_id, data in list(self._docs.items())]

    def get(self, retry=None, timeout=None, **kwargs):
        """Return every document in the collection."""
        return self.stream(
            retry=retry,
            timeout=timeout,
            **kwargs,
        )

    def limit(self, number):
        return _FakeQuery(self, [], number)


class FakeBatch:
    def __init__(self):
        self._ops = []

    def update(self, ref, data):
        self._ops.append(("update", ref, data, False))
        return self

    def set(self, ref, data, merge=False):
        self._ops.append(("set", ref, data, merge))
        return self

    def delete(self, ref):
        self._ops.append(("delete", ref, None, False))
        return self

    def commit(self, retry=None, timeout=None, **kwargs):
        results = []

        for operation, ref, data, merge in self._ops:
            if operation == "delete":
                results.append(ref.delete())
            elif operation == "set":
                results.append(ref.set(data, merge=merge))
            elif operation == "update":
                results.append(ref.update(data))

        self._ops = []
        return results


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
        """Directly write a document, bypassing route logic.

        This is useful for Gherkin ``Given`` steps that set up
        pre-existing state.
        """
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

    def upload_from_string(
        self,
        contents,
        content_type=None,
        retry=None,
        timeout=None,
        **kwargs,
    ):
        self._uploaded = contents

    def generate_signed_url(self, **kwargs):
        return f"https://example.com/{self.name}"

    def exists(self, **kwargs):
        return True


class FakeBucket:
    def blob(self, path):
        return FakeBlob(path)


# ======================================================================
# Cross-module patching helper
# ======================================================================

# Every backend module that imports `db` or `bucket` at module scope.
#
# Functions look up `db` in the globals of the module where they are
# defined, not where they are called from. Therefore, a page such as
# /saved-jobs that calls notifications.get_unread_notifications_count()
# also requires notifications.db to be patched.
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
    """Patch backend modules to use the same fake database instance.

    Using one shared instance ensures that a request crossing multiple
    backend modules sees consistent in-memory data.
    """
    for name in _DB_MODULES:
        module = importlib.import_module(name)

        monkeypatch.setattr(
            module,
            "db",
            fake_db,
            raising=False,
        )

        if bucket is not None:
            monkeypatch.setattr(
                module,
                "bucket",
                bucket,
                raising=False,
            )
