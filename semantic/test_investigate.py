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
    assert (
        client.post("/semantic/investigate", json={"anchor_id": "00000000-0000-0000-0000-000000000000"}).status_code
        == 404
    )


def test_investigation_cache_avoids_provider_calls(monkeypatch):
    import json

    from fastapi.testclient import TestClient

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
    result = TestClient(service.app).post("/semantic/investigate", json={"anchor_id": anchor_id})
    assert result.status_code == 200 and result.json()["cached"] is True


def test_no_claim_does_not_embed_or_manufacture_a_pair(monkeypatch):
    from semantic import investigate as module

    monkeypatch.setattr(module, "chat", lambda *args: {"claim": None, "queries": []})
    monkeypatch.setattr(module, "embed", lambda *args: pytest.fail("no claim must not search"))
    result = module.investigate(ANCHOR, None)
    assert result["assessments"] == [] and result["candidates_checked"] == 0
