import pytest

from semantic.investigate import candidate_pool, validated_assessments

ANCHOR = {
    "id": "a",
    "video_id": "a",
    "start_ms": 0,
    "end_ms": 90000,
    "text": "I think all peaceful protest should always be allowed.",
}
OTHER = {
    "id": "b",
    "video_id": "b",
    "start_ms": 0,
    "end_ms": 90000,
    "text": "I believe peaceful protest should be banned in every case.",
}


def assessment(**kwargs):
    return {
        "id": "b",
        "relation": "possible_contradiction",
        "anchor_quote": ANCHOR["text"],
        "counter_quote": OTHER["text"],
        "explanation": "The two captions contain incompatible rules.",
        "alternative": "Different speakers may be responsible for these statements.",
        "verification": "Watch both passages to establish speaker identity and scope.",
        **kwargs,
    }


def test_quotes_and_ids_must_come_from_retrieved_evidence():
    assert len(validated_assessments({"assessments": [assessment()]}, ANCHOR, [OTHER])) == 1
    for invalid in [
        assessment(id="invented"),
        assessment(counter_quote="This quotation was never spoken."),
        assessment(relation="proven_contradiction"),
        assessment(alternative=""),
        assessment(anchor_quote="peaceful protest … be allowed"),
    ]:
        assert validated_assessments({"assessments": [invalid]}, ANCHOR, [OTHER]) == []


def test_keep_disconfirming_findings_and_deduplicate_assessments():
    row = assessment(relation="different_context")
    result = validated_assessments({"assessments": [row, row]}, ANCHOR, [OTHER])
    assert len(result) == 1 and result[0]["relation"] == "different_context"


def test_retrieval_removes_anchor_overlap_and_reuploaded_duplicate():
    points = [
        {"id": "overlap", "score": 0.9, "payload": {**ANCHOR, "start_ms": 60000}},
        {"id": "reupload", "score": 0.9, "payload": {**ANCHOR, "video_id": "other"}},
        {"id": "b", "score": 0.8, "payload": OTHER},
    ]
    result = candidate_pool(ANCHOR, [points, points])
    assert [p["id"] for p in result] == ["b"]


def test_endpoint_rejects_client_text_and_invisible_source(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    from fastapi.testclient import TestClient

    from semantic import service

    monkeypatch.setattr(service, "qdrant", lambda *args: [])
    monkeypatch.setattr(service, "investigate", lambda *args: pytest.fail("must not spend on missing source"))
    client = TestClient(service.app)
    assert client.post("/semantic/investigate", json={"text": "invented"}).status_code == 422
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as missing:
        service.counterstatements(service.InvestigationRequest(anchor_id="00000000-0000-0000-0000-000000000000"))
    assert missing.value.status_code == 404


def test_investigation_cache_avoids_provider_calls(monkeypatch):
    import json

    from semantic import service

    anchor_id = "00000000-0000-0000-0000-000000000000"

    class Cache:
        def scard(self, key):
            return 100

        def get(self, key):
            return json.dumps({"assessments": [], "candidates_checked": 12})

    monkeypatch.setattr(service, "cache", Cache())
    monkeypatch.setattr(service, "qdrant", lambda *args: [{"id": anchor_id, "payload": {**ANCHOR, "visible": True}}])
    monkeypatch.setattr(service, "investigate", lambda *args: pytest.fail("cached assessment must not call provider"))
    result = service.counterstatements(service.InvestigationRequest(anchor_id=anchor_id))
    assert result["cached"] is True


def test_no_claim_does_not_embed_or_manufacture_a_pair(monkeypatch):
    from semantic import investigate as module

    monkeypatch.setattr(module, "chat", lambda *args: {"claim": None, "queries": []})
    monkeypatch.setattr(module, "embed", lambda *args: pytest.fail("no claim must not search"))
    result = module.investigate(ANCHOR, None)
    assert result["assessments"] == [] and result["candidates_checked"] == 0


def test_skeptical_review_can_remove_an_exception_based_false_positive(monkeypatch):
    from semantic import investigate as module

    answers = iter(
        [
            {
                "claim": "A claim about peaceful protest",
                "queries": [
                    "peaceful protest rights",
                    "peaceful protest restrictions",
                    "exceptions for peaceful protest",
                ],
            },
            {"assessments": [assessment()]},
            {
                "reviews": [
                    {
                        "id": "b",
                        "relation": "consistent",
                        "explanation": "The second example falls inside the first stated exception.",
                        "alternative": "Both passages endorse the same exception to the general rule.",
                        "verification": "Check speaker attribution and the exception in the full source.",
                    }
                ]
            },
        ]
    )
    monkeypatch.setattr(module, "chat", lambda *args: next(answers))
    monkeypatch.setattr(module, "embed", lambda *args: ([[1], [1], [1]], 1))
    monkeypatch.setattr(module, "qdrant", lambda *args: {"points": []})
    monkeypatch.setattr(module, "candidate_pool", lambda *args: [OTHER])

    class Cache:
        def incrby(self, *args):
            pass

    assert module.investigate(ANCHOR, Cache())["assessments"][0]["relation"] == "consistent"


def test_async_job_returns_validated_result_and_expired_running_job_fails(monkeypatch):
    import json
    import time

    from fastapi.testclient import TestClient

    from semantic import service

    class Cache:
        values = {}

        def incr(self, key):
            return 2

        def setex(self, key, ttl, value):
            self.values[key] = value

        def get(self, key):
            return self.values.get(key)

    store = Cache()
    monkeypatch.setattr(service, "cache", store)
    monkeypatch.setattr(service, "counterstatements", lambda *args: {"assessments": []})
    client = TestClient(service.app)
    response = client.post("/semantic/investigate", json={"anchor_id": "00000000-0000-0000-0000-000000000000"})
    assert response.status_code == 202
    jid = response.json()["job_id"]
    assert client.get("/semantic/investigate/" + jid).json()["state"] == "complete"
    store.values["semantic:job:" + jid] = json.dumps({"state": "running", "started_at": time.time() - 1000})
    assert client.get("/semantic/investigate/" + jid).json()["state"] == "failed"
