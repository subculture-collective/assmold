"""Meaning search over source-linked caption windows; never a contradiction verdict."""

from __future__ import annotations

import hashlib
import math
import os
import uuid

import httpx

MODEL = "openai/text-embedding-3-small"
DIMENSIONS = 512
COLLECTION = "assmold_captions_openai_small_512_v1"


def windows(segments: list[dict]) -> list[dict]:
    if not segments:
        return []
    output = []
    end = max(int(s["end_ms"]) for s in segments)
    for start in range(0, end, 60_000):
        rows = [
            s
            for s in segments
            if int(s["end_ms"]) > start and int(s["start_ms"]) < start + 90_000 and s["text"].strip()
        ]
        if not rows:
            continue
        text = " ".join(s["text"].strip() for s in rows)
        # A pathological caption must not create an unbounded provider request.
        if len(text) > 24000:
            raise ValueError("caption window exceeds embedding input bound")
        output.append({"start_ms": int(rows[0]["start_ms"]), "end_ms": int(rows[-1]["end_ms"]), "text": text})
    return output


def validated_vectors(payload: dict, count: int) -> list[list[float]]:
    data = payload.get("data", [])
    if len(data) != count or sorted(item.get("index", -1) for item in data) != list(range(count)):
        raise ValueError("embedding response count or indexes are invalid")
    vectors = []
    for item in sorted(data, key=lambda x: x["index"]):
        vector = item.get("embedding", [])
        if len(vector) != DIMENSIONS or any(not isinstance(x, (float, int)) or not math.isfinite(x) for x in vector):
            raise ValueError("embedding response dimensions or values are invalid")
        if not any(vector):
            raise ValueError("embedding response contains a zero vector")
        vectors.append(vector)
    return vectors


def embed(texts: list[str]) -> tuple[list[list[float]], int]:
    response = httpx.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]},
        json={"model": MODEL, "dimensions": DIMENSIONS, "input": texts},
        timeout=90,
    )
    # Do not log provider response bodies or authorization headers on failure.
    if response.status_code != 200:
        raise RuntimeError(f"embedding provider HTTP {response.status_code}")
    payload = response.json()
    return validated_vectors(payload, len(texts)), int(payload.get("usage", {}).get("total_tokens", 0))


def qdrant(method: str, path: str, body: dict | None = None):
    r = httpx.request(method, os.environ.get("QDRANT_URL", "http://assmold-vectors:6333") + path, json=body, timeout=45)
    if not r.is_success:
        raise RuntimeError(f"vector store HTTP {r.status_code}")
    return r.json().get("result")


def point_id(video_id: str, generation: str, start_ms: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"assmold:{video_id}:{generation}:{start_ms}"))


def query_key(query: str) -> str:
    return "semantic:query:" + hashlib.sha256((MODEL + query.strip().casefold()).encode()).hexdigest()


def retrieval_filter(date_from: str | None, date_to: str | None) -> dict:
    conditions = [{"key": "visible", "match": {"value": True}}]
    if date_from or date_to:
        bounds = {}
        if date_from:
            bounds["gte"] = date_from + "T00:00:00Z"
        if date_to:
            bounds["lte"] = date_to + "T23:59:59.999999Z"
        conditions.append({"key": "uploaded_at", "range": bounds})
    return {"must": conditions}


def deduplicate(points: list[dict], limit: int = 20) -> list[dict]:
    output = []
    for point in points:
        p = point["payload"]
        if any(x["video_id"] == p["video_id"] and abs(x["start_ms"] - p["start_ms"]) < 60_000 for x in output):
            continue
        output.append(
            {
                **{k: v for k, v in p.items() if k not in {"visible", "generation"}},
                "score": point["score"],
                "id": str(point["id"]),
            }
        )
        if len(output) >= limit:
            break
    return output
