from __future__ import annotations

import json
import os
import time
from datetime import date

import redis
from fastapi import FastAPI, HTTPException, Query

from semantic.core import COLLECTION, deduplicate, embed, qdrant, query_key, retrieval_filter

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
