import pytest

from semantic.core import DIMENSIONS, deduplicate, point_id, retrieval_filter, validated_vectors, windows


def test_windows_preserve_source_timestamps_and_overlap():
    chunks = windows(
        [{"start_ms": i * 10000, "end_ms": i * 10000 + 10000, "text": f"statement {i}"} for i in range(18)]
    )
    assert len(chunks) == 3
    assert chunks[0]["start_ms"] == 0 and chunks[0]["end_ms"] == 90000
    assert "statement 6" in chunks[0]["text"] and "statement 6" in chunks[1]["text"]
    assert chunks[-1]["end_ms"] == 180000


def test_empty_and_pathological_source():
    assert windows([]) == []
    with pytest.raises(ValueError):
        windows([{"start_ms": 0, "end_ms": 2000, "text": "x" * 25000}])


def test_provider_vectors_validate_order_dimensions_and_finite_numbers():
    assert (
        validated_vectors(
            {"data": [{"index": 1, "embedding": [2.0] * DIMENSIONS}, {"index": 0, "embedding": [1.0] * DIMENSIONS}]}, 2
        )[0][0]
        == 1
    )
    for data in [
        [{"index": 0, "embedding": [0.0] * DIMENSIONS}],
        [{"index": 0, "embedding": [float("nan")] * DIMENSIONS}],
        [{"index": 0, "embedding": [1.0]}],
        [{"index": 9, "embedding": [1.0] * DIMENSIONS}],
    ]:
        with pytest.raises(ValueError):
            validated_vectors({"data": data}, 1)


def test_date_filters_and_stable_revision_ids():
    result = retrieval_filter("2025-01-01", "2025-01-31")
    assert result["must"][0]["match"]["value"] is True
    assert result["must"][1]["range"]["gte"] == "2025-01-01T00:00:00Z"
    assert point_id("video", "revision1", 0) == point_id("video", "revision1", 0)
    assert point_id("video", "revision1", 0) != point_id("video", "revision2", 0)


def test_overlap_dedup_keeps_different_videos_and_distant_statements():
    points = [
        {
            "id": i,
            "score": 0.9,
            "payload": {
                "video_id": video,
                "start_ms": start,
                "text": "quote",
                "visible": True,
                "generation": "private",
            },
        }
        for i, (video, start) in enumerate([("a", 0), ("a", 20000), ("b", 20000), ("a", 180000)])
    ]
    items = deduplicate(points)
    assert len(items) == 3
    assert all("visible" not in x and "generation" not in x for x in items)


def test_service_dates_and_public_error_contract(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    from fastapi.testclient import TestClient

    from semantic import service

    client = TestClient(service.app)
    assert client.get("/semantic/search", params={"q": "x"}).status_code == 422
    assert (
        client.get(
            "/semantic/search", params={"q": "meaning", "date_from": "2026-01-02", "date_to": "2026-01-01"}
        ).status_code
        == 422
    )

    class Down:
        def incr(self, key):
            raise RuntimeError("private error must not leak")

    monkeypatch.setattr(service, "cache", Down())
    response = client.get("/semantic/search", params={"q": "meaning"})
    assert response.status_code == 503
    assert "private" not in response.text


def test_service_uses_cached_vector_without_paid_call(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    import json

    from fastapi.testclient import TestClient

    from semantic import service

    class Cache:
        def incr(self, key):
            return 2

        def get(self, key):
            return json.dumps([1.0] * DIMENSIONS)

        def scard(self, key):
            return 10

    monkeypatch.setattr(service, "cache", Cache())
    monkeypatch.setattr(service, "embed", lambda _: pytest.fail("cached query must not call provider"))
    captured = []
    monkeypatch.setattr(service, "qdrant", lambda method, path, body: captured.append(body) or {"points": []})
    result = TestClient(service.app).get("/semantic/search", params={"q": "meaning", "date_from": "2026-01-01"})
    assert result.status_code == 200 and result.json()["indexed_videos"] == 10
    assert captured[0]["filter"]["must"][1]["range"]["gte"] == "2026-01-01T00:00:00Z"
