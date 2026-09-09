from __future__ import annotations

import json
import logging
import os
import time
from datetime import date
from uuid import UUID, uuid4

import redis
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from semantic.core import COLLECTION, deduplicate, embed, qdrant, query_key, retrieval_filter
from semantic.investigate import VERSION, investigate

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
cache = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


@app.get("/healthz")
def health():
    cache.ping()
    qdrant("GET", "/collections/" + COLLECTION)
    return {"status": "ok"}


@app.get("/semantic/status")
def status():
    try:
        info = qdrant("GET", "/collections/" + COLLECTION)
        return {
            "windows": info.get("points_count", 0),
            "videos": cache.scard("semantic:indexed-videos"),
            "state": cache.get("semantic:worker-state") or "starting",
        }
    except Exception:
        raise HTTPException(503, "Meaning search is warming up.") from None


@app.get("/semantic/search")
def search(q: str = Query(min_length=2, max_length=500), date_from: date | None = None, date_to: date | None = None):
    q = q.strip()
    if len(q) < 2:
        raise HTTPException(422, "Enter at least two characters.")
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "From must be before To.")
    try:
        # Global limit bounds public provider concurrency even behind a shared proxy.
        rate = "semantic:requests:" + str(int(time.time()) // 60)
        count = cache.incr(rate)
        if count == 1:
            cache.expire(rate, 120)
        if count > 120:
            raise HTTPException(429, "Meaning search is busy. Try again shortly.")
        key = query_key(q)
        raw = cache.get(key)
        if raw:
            vector = json.loads(raw)
        else:
            with cache.lock("semantic:query-lock:" + key, timeout=100, blocking_timeout=2):
                raw = cache.get(key)
                if raw:
                    vector = json.loads(raw)
                else:
                    vectors, tokens = embed([q])
                    vector = vectors[0]
                    cache.setex(key, 604800, json.dumps(vector))
                    cache.incrby("semantic:query-tokens", tokens)
        result = qdrant(
            "POST",
            "/collections/" + COLLECTION + "/points/query",
            {
                "query": vector,
                "limit": 60,
                "with_payload": True,
                "filter": retrieval_filter(str(date_from) if date_from else None, str(date_to) if date_to else None),
            },
        )
        return {
            "query": q,
            "items": deduplicate(result["points"]),
            "indexed_videos": cache.scard("semantic:indexed-videos"),
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            503, "Meaning search is temporarily unavailable. Try keyword search or retry shortly."
        ) from None


class InvestigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    anchor_id: UUID


def counterstatements(request: InvestigationRequest):
    try:
        # Clients submit a source ID only: no invented captions enter the assessment.
        points = qdrant(
            "POST",
            "/collections/" + COLLECTION + "/points",
            {"ids": [str(request.anchor_id)], "with_payload": True, "with_vector": False},
        )
        if not points or not points[0].get("payload", {}).get("visible"):
            raise HTTPException(404, "This passage is no longer indexed. Search again to select a current passage.")
        anchor = deduplicate([{**points[0], "score": 1.0}])[0]
        revision = cache.scard("semantic:indexed-videos")
        key = f"semantic:investigation:{VERSION}:{request.anchor_id}:{revision // 25}"
        saved = cache.get(key)
        if saved:
            return {**json.loads(saved), "cached": True}
        # A single global lane bounds paid work; an uncertain call is never auto-retried.
        with cache.lock("semantic:investigation-lane", timeout=900, blocking_timeout=1):
            saved = cache.get(key)
            if saved:
                return {**json.loads(saved), "cached": True}
            rate = "semantic:investigation-rate:" + str(int(time.time()) // 3600)
            calls = cache.incr(rate)
            if calls == 1:
                cache.expire(rate, 7200)
            if calls > 30:
                raise HTTPException(429, "Counterstatement search is busy. Try again later.")
            result = {**investigate(anchor, cache), "indexed_videos": revision, "version": VERSION}
            cache.setex(key, 21600, json.dumps(result))
            return {**result, "cached": False}
    except HTTPException:
        raise
    except redis.exceptions.LockError:
        raise HTTPException(429, "Another investigation is running. Try again in a few minutes.") from None
    except Exception as error:
        logging.getLogger(__name__).warning("investigation_failed error_type=%s", type(error).__name__)
        raise HTTPException(
            503, "The investigation could not finish. Your source passage is unchanged. You can try again."
        ) from None


def finish_investigation(job_id: str, request: InvestigationRequest):
    try:
        result = {"state": "complete", "result": counterstatements(request)}
    except HTTPException as error:
        result = {"state": "failed", "detail": error.detail}
    except Exception:
        result = {"state": "failed", "detail": "Investigation could not finish. Try again later."}
    cache.setex("semantic:job:" + job_id, 3600, json.dumps(result))


@app.post("/semantic/investigate", status_code=202)
def start_investigation(request: InvestigationRequest, background: BackgroundTasks):
    try:
        key = "semantic:job-requests:" + str(int(time.time()) // 60)
        count = cache.incr(key)
        if count == 1:
            cache.expire(key, 120)
        if count > 30:
            raise HTTPException(429, "Counterstatement search is busy. Try again shortly.")
        job_id = str(uuid4())
        cache.setex("semantic:job:" + job_id, 3600, json.dumps({"state": "running", "started_at": time.time()}))
        background.add_task(finish_investigation, job_id, request)
        return {"job_id": job_id}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, "Investigation could not start. Try again later.") from None


@app.get("/semantic/investigate/{job_id}")
def investigation_result(job_id: UUID):
    try:
        raw = cache.get("semantic:job:" + str(job_id))
        if not raw:
            raise HTTPException(404, "This investigation expired. Select the passage to start again.")
        result = json.loads(raw)
        if result["state"] == "running" and time.time() - result["started_at"] > 900:
            return {
                "state": "failed",
                "detail": "The investigation was interrupted or timed out. It has not been automatically retried.",
            }
        return result
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, "Investigation status is temporarily unavailable.") from None
