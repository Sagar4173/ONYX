"""Tests for quota ledger, response cache, and invocation tracer."""
from datetime import datetime, timedelta, timezone

import pytest
from pymongo.errors import DuplicateKeyError

from config import settings
from services.ai.stores import QuotaLedger, ResponseCache
from services.ai.trace import InvocationTracer


class FakeCollection:
    """Minimal async Mongo collection double."""

    def __init__(self, doc=None, raise_on_call=False):
        self.doc = doc
        self.raise_on_call = raise_on_call
        self.calls = []

    async def find_one_and_update(self, filter, update, upsert=False, return_document=None):
        self.calls.append(("find_one_and_update", filter, update))
        if self.raise_on_call:
            raise RuntimeError("mongo down")
        count = (self.doc or {}).get("count", 0) + update["$inc"]["count"]
        self.doc = {"_id": filter["_id"], "count": count}
        return dict(self.doc)

    async def update_one(self, filter, update, upsert=False):
        self.calls.append(("update_one", filter, update))
        if self.raise_on_call:
            raise RuntimeError("mongo down")
        self.doc = {"_id": filter["_id"], **update["$set"]}
        return MagicMockResult()

    async def find_one(self, filter):
        self.calls.append(("find_one", filter))
        if self.raise_on_call:
            raise RuntimeError("mongo down")
        return dict(self.doc) if self.doc else None

    async def insert_one(self, doc):
        self.calls.append(("insert_one", doc))
        if self.raise_on_call:
            raise RuntimeError("mongo down")
        return object()


class MagicMockResult:
    pass


class FakeDB:
    def __init__(self, **collections):
        for name, coll in collections.items():
            setattr(self, name, coll)


class TestQuotaLedger:
    async def test_memory_mode_exhausts_at_limit(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_rate_limit_rpd", 2)
        ledger = QuotaLedger(db=None)
        ledger._db_disabled = True  # force memory path even if a real DB is connected
        assert await ledger.try_consume("gemini") is True
        assert await ledger.try_consume("gemini") is True
        assert await ledger.try_consume("gemini") is False
        assert ledger.remaining("gemini") == 0

    async def test_memory_mode_isolates_providers_and_days(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_rate_limit_rpd", 1)
        ledger = QuotaLedger(db=None)
        ledger._db_disabled = True
        assert await ledger.try_consume("gemini") is True
        assert await ledger.try_consume("groq") is True  # different provider
        assert await ledger.try_consume("groq") is False

    async def test_mongo_mode_uses_counter(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_rate_limit_rpd", 5)
        coll = FakeCollection()
        ledger = QuotaLedger(db=FakeDB(ai_quota_ledgers=coll))
        assert await ledger.try_consume("gemini") is True
        assert await ledger.try_consume("gemini") is True
        assert coll.doc["count"] == 2
        assert ledger.remaining("gemini") == 3

    async def test_mongo_failure_falls_back_to_memory(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_rate_limit_rpd", 5)
        coll = FakeCollection(raise_on_call=True)
        ledger = QuotaLedger(db=FakeDB(ai_quota_ledgers=coll))
        assert await ledger.try_consume("gemini") is True
        assert ledger.remaining("gemini") == 4


class TestResponseCache:
    async def test_roundtrip_in_memory(self):
        cache = ResponseCache(db=None)
        cache._db_disabled = True
        key = ResponseCache.make_key(
            purpose="analysis", messages=[{"role": "user", "content": "hi"}],
            temperature=0.3, schema_name="AnalysisNarrative", chain="gemini",
        )
        await cache.set(key, {"text": "value", "provider": "gemini"})
        hit = await cache.get(key)
        assert hit == {"text": "value", "provider": "gemini"}

    async def test_key_changes_with_content(self):
        a = ResponseCache.make_key(
            purpose="analysis", messages=[{"role": "user", "content": "hi"}],
            temperature=0.3, schema_name="", chain="gemini",
        )
        b = ResponseCache.make_key(
            purpose="analysis", messages=[{"role": "user", "content": "ho"}],
            temperature=0.3, schema_name="", chain="gemini",
        )
        assert a != b
        assert len(a) == 64

    async def test_ttl_zero_expires_immediately(self):
        cache = ResponseCache(db=None)
        cache._db_disabled = True
        key = ResponseCache.make_key(
            purpose="p", messages=[], temperature=0.0, schema_name="", chain="c",
        )
        await cache.set(key, {"text": "v"}, ttl_days=0)
        assert await cache.get(key) is None

    async def test_mongo_set_and_get(self):
        coll = FakeCollection()
        cache = ResponseCache(db=FakeDB(ai_response_cache=coll))
        key = ResponseCache.make_key(
            purpose="p", messages=[], temperature=0.0, schema_name="", chain="c",
        )
        await cache.set(key, {"text": "v", "provider": "groq"})
        assert coll.doc["value"] == {"text": "v", "provider": "groq"}
        # Memory already holds it; clear to force DB path
        cache._mem.clear()
        hit = await cache.get(key)
        assert hit == {"text": "v", "provider": "groq"}

    async def test_mongo_failure_degrades_to_memory(self):
        coll = FakeCollection(raise_on_call=True)
        cache = ResponseCache(db=FakeDB(ai_response_cache=coll))
        key = "k" * 64
        await cache.set(key, {"text": "v"})  # must not raise
        cache._db_disabled = True
        assert await cache.get(key) == {"text": "v"}


class TestInvocationTracer:
    async def test_record_appends_to_ring(self):
        tracer = InvocationTracer(db=None, maxlen=3)
        tracer._db_disabled = True
        for i in range(4):
            await tracer.record(purpose="analysis", provider="gemini", ok=True, i=i)
        recent = tracer.recent()
        assert len(recent) == 3
        assert recent[0]["i"] == 1  # oldest evicted

    async def test_record_persists_best_effort(self):
        coll = FakeCollection()
        tracer = InvocationTracer(db=FakeDB(ai_invocations=coll))
        await tracer.record(purpose="chat", provider="groq", ok=True)
        assert len(coll.calls) == 1
        assert coll.calls[0][1]["purpose"] == "chat"

    async def test_record_swallows_db_errors(self):
        coll = FakeCollection(raise_on_call=True)
        tracer = InvocationTracer(db=FakeDB(ai_invocations=coll))
        await tracer.record(purpose="chat", provider="groq", ok=False)  # must not raise
        assert len(tracer.recent()) == 1


class AtLimitCollection(FakeCollection):
    """Simulates the conditional-update filter: find_one_and_update returns
    None when the counter is already at the limit, and insert_one raises
    DuplicateKeyError when the _id already exists."""

    async def find_one_and_update(self, filter, update, upsert=False, return_document=None):
        self.calls.append(("find_one_and_update", filter, update))
        if self.raise_on_call:
            raise RuntimeError("mongo down")
        current = (self.doc or {}).get("count", 0)
        if current >= filter["count"]["$lt"]:
            return None
        count = current + update["$inc"]["count"]
        self.doc = {"_id": filter["_id"], "count": count}
        return dict(self.doc)

    async def insert_one(self, doc):
        self.calls.append(("insert_one", doc))
        if self.raise_on_call:
            raise RuntimeError("mongo down")
        if self.doc is not None:
            raise DuplicateKeyError("duplicate key")
        self.doc = dict(doc)
        return object()


async def test_mongo_at_limit_denies_without_overshooting(monkeypatch):
    monkeypatch.setattr(settings, "ai_rate_limit_rpd", 5)
    coll = AtLimitCollection(doc={"_id": "gemini:" + datetime.now(timezone.utc).strftime("%Y-%m-%d"), "count": 5})
    ledger = QuotaLedger(db=FakeDB(ai_quota_ledgers=coll))
    assert await ledger.try_consume("gemini") is False
    assert coll.doc["count"] == 5  # denied call must NOT increment the counter
    assert ledger.remaining("gemini") == 0


async def test_mongo_missing_doc_is_created_with_count_one(monkeypatch):
    monkeypatch.setattr(settings, "ai_rate_limit_rpd", 5)
    coll = AtLimitCollection(doc=None)
    ledger = QuotaLedger(db=FakeDB(ai_quota_ledgers=coll))
    assert await ledger.try_consume("gemini") is True
    assert coll.doc["count"] == 1
    assert ledger.remaining("gemini") == 4


async def test_cache_read_normalizes_naive_datetimes():
    import time as time_mod

    naive_past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
    key = "n" * 64
    coll = FakeCollection(doc={"_id": key, "value": {"text": "v"}, "expires_at": naive_past})
    cache = ResponseCache(db=FakeDB(ai_response_cache=coll))
    await cache.get(key)  # must not raise; fake ignores the expiry filter
    # The memory entry must interpret the naive timestamp as UTC, so it is
    # already expired for a UTC timestamp 1 hour in the past.
    expected = naive_past.replace(tzinfo=timezone.utc).timestamp()
    assert abs(cache._mem[key]["expires_at"] - expected) < 60
    assert cache._mem[key]["expires_at"] <= time_mod.time()
