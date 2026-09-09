from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path

import httpx
import psycopg
import redis
from psycopg.rows import dict_row

from semantic.core import COLLECTION, DIMENSIONS, embed, point_id, qdrant, windows


def run():
    directory = Path(os.environ.get("SEMANTIC_STATE_DIR", "/data"))
    directory.mkdir(exist_ok=True)
    state = sqlite3.connect(directory / "indexed.sqlite")
    state.execute("CREATE TABLE IF NOT EXISTS indexed (transcript_id text primary key, video_id text not null)")
    cache = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
    db = psycopg.connect(
        os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://"),
        autocommit=True,
        row_factory=dict_row,
    )
    if not db.execute("SELECT pg_try_advisory_lock(736219408) AS locked").fetchone()["locked"]:
        raise RuntimeError("semantic indexer already owns the source lock")
    existing = httpx.get(
        os.environ.get("QDRANT_URL", "http://assmold-vectors:6333") + "/collections/" + COLLECTION, timeout=30
    )
    if existing.status_code == 404:
        qdrant(
            "PUT",
            "/collections/" + COLLECTION,
            {"vectors": {"size": DIMENSIONS, "distance": "Cosine", "on_disk": True}, "on_disk_payload": True},
        )
        for key, kind in [
            ("video_id", "keyword"),
            ("generation", "keyword"),
            ("visible", "bool"),
            ("uploaded_at", "datetime"),
        ]:
            qdrant("PUT", "/collections/" + COLLECTION + "/index", {"field_name": key, "field_schema": kind})
    elif existing.status_code != 200:
        raise RuntimeError("vector store unavailable")
    for (video_id,) in state.execute("SELECT DISTINCT video_id FROM indexed"):
        cache.sadd("semantic:indexed-videos", video_id)
    while True:
        if (directory / "paused").exists():
            cache.set("semantic:worker-state", "paused")
            time.sleep(30)
            continue
        cache.set("semantic:worker-state", "indexing")
        rows = db.execute(
            """SELECT DISTINCT ON (v.id) v.id::text AS video_id,v.youtube_id,v.title,v.channel_name,v.uploaded_at,t.id::text AS transcript_id
            FROM videos v JOIN youtube_transcripts t ON t.video_id=v.id
            WHERE t.language LIKE 'en%%' AND EXISTS (SELECT 1 FROM youtube_segments s WHERE s.youtube_transcript_id=t.id)
            ORDER BY v.id,CASE WHEN t.kind='manual' THEN 0 ELSE 1 END,t.created_at DESC,t.id DESC"""
        ).fetchall()
        rows.sort(key=lambda x: str(x["uploaded_at"] or ""), reverse=True)
        pending = [
            r
            for r in rows
            if not state.execute("SELECT 1 FROM indexed WHERE transcript_id=?", (r["transcript_id"],)).fetchone()
        ]
        if not pending:
            cache.set("semantic:worker-state", "caught_up")
            time.sleep(60)
            continue
        r = pending[0]
        try:
            segments = db.execute(
                "SELECT start_ms,end_ms,text FROM youtube_segments WHERE youtube_transcript_id=%s ORDER BY start_ms,id",
                (r["transcript_id"],),
            ).fetchall()
            chunks = windows(segments)
            if not chunks:
                raise ValueError("empty caption windows")
            generation = hashlib.sha256((r["transcript_id"] + json.dumps(chunks, sort_keys=True)).encode()).hexdigest()[
                :24
            ]
            base = {k: r[k] or "" for k in ["video_id", "youtube_id", "title", "channel_name"]}
            base["uploaded_at"] = r["uploaded_at"].isoformat() if r["uploaded_at"] else "1970-01-01T00:00:00+00:00"
            token_total = 0
            for offset in range(0, len(chunks), 16):
                batch = chunks[offset : offset + 16]
                vectors, tokens = embed([base["title"] + "\n" + x["text"] for x in batch])
                token_total += tokens
                cache.incrby("semantic:index-tokens", tokens)
                points = [
                    {
                        "id": point_id(r["video_id"], generation, x["start_ms"]),
                        "vector": vector,
                        "payload": {**base, **x, "generation": generation, "visible": False},
                    }
                    for x, vector in zip(batch, vectors, strict=False)
                ]
                qdrant("PUT", "/collections/" + COLLECTION + "/points?wait=true", {"points": points})
            generation_filter = {
                "must": [
                    {"key": "video_id", "match": {"value": r["video_id"]}},
                    {"key": "generation", "match": {"value": generation}},
                ]
            }
            qdrant(
                "POST",
                "/collections/" + COLLECTION + "/points/payload?wait=true",
                {"payload": {"visible": True}, "filter": generation_filter},
            )
            qdrant(
                "POST",
                "/collections/" + COLLECTION + "/points/delete?wait=true",
                {
                    "filter": {
                        "must": [{"key": "video_id", "match": {"value": r["video_id"]}}],
                        "must_not": [{"key": "generation", "match": {"value": generation}}],
                    }
                },
            )
            state.execute("INSERT OR REPLACE INTO indexed VALUES (?,?)", (r["transcript_id"], r["video_id"]))
            state.commit()
            cache.sadd("semantic:indexed-videos", r["video_id"])
            print(
                json.dumps(
                    {"status": "indexed", "video_id": r["video_id"], "windows": len(chunks), "tokens": token_total}
                ),
                flush=True,
            )
            time.sleep(2)
        except Exception as exc:
            # Persist the pause: restart must not blindly replay uncertain paid calls.
            (directory / "paused").write_text(type(exc).__name__ + "\n")
            cache.set("semantic:worker-state", "paused")
            print(
                json.dumps(
                    {
                        "status": "paused",
                        "video_id": r["video_id"],
                        "error_type": type(exc).__name__,
                        "error": str(exc) if isinstance(exc, (RuntimeError, ValueError)) else "index operation failed",
                    }
                ),
                flush=True,
            )


if __name__ == "__main__":
    run()
