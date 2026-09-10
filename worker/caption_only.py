"""Caption acquisition only: never import the native/audio pipeline."""

from __future__ import annotations

import argparse
import json
import signal
import threading
import time
from dataclasses import asdict

from sqlalchemy import text

from app.db import engine
from app.settings import settings
from worker.caption_ingest import ingest_available_captions
from worker.channel_sync import parse_channel_urls, sync_configured_channels

OWNER_LOCK = "assmold-caption-only-v1"


def complete_captioned_videos(db) -> int:
    """Finish caption-only work without manufacturing native transcript rows."""
    changed = db.execute(text("""
        UPDATE videos v SET state='completed', error=NULL, updated_at=now()
        WHERE v.state IN ('pending','downloading','transcoding','transcribing')
          AND v.caption_ingest_state='completed'
          AND (v.diarization_error IS NULL OR v.diarization_error NOT LIKE 'canary-%')
          AND EXISTS (SELECT 1 FROM jobs j WHERE j.id=v.job_id
                      AND j.meta->>'created_by'='channel_sync')
          AND EXISTS (SELECT 1 FROM youtube_transcripts t JOIN youtube_segments s
                      ON s.youtube_transcript_id=t.id WHERE t.video_id=v.id
                      AND length(trim(s.text))>0 AND s.start_ms>=0 AND s.end_ms>s.start_ms)
    """))
    db.execute(text("""
        UPDATE jobs j SET state='completed', stage='completed', error=NULL,
            completed_units=(SELECT count(*) FROM videos v WHERE v.job_id=j.id),
            total_units=(SELECT count(*) FROM videos v WHERE v.job_id=j.id), updated_at=now()
        WHERE j.meta->>'created_by'='channel_sync' AND j.state<>'completed'
          AND EXISTS (SELECT 1 FROM videos v WHERE v.job_id=j.id)
          AND NOT EXISTS (SELECT 1 FROM videos v WHERE v.job_id=j.id AND v.state<>'completed')
    """))
    return int(changed.rowcount)


def schedule_retry(connection) -> str | None:
    """At most three retries per video; counters/history survive worker restarts."""
    row = connection.execute(text("""
        SELECT v.id, j.id AS job_id, v.caption_ingest_state AS previous_state,
               v.caption_ingest_error AS previous_error,
               COALESCE((j.meta->>'caption_retry_count')::integer,0) AS attempts
        FROM videos v JOIN jobs j ON j.id=v.job_id
        WHERE j.meta->>'created_by'='channel_sync'
          AND j.state NOT IN ('completed','failed')
          AND v.state IN ('pending','downloading','transcoding','transcribing')
          AND v.caption_ingest_state IN ('failed','unavailable')
          AND NOT EXISTS (SELECT 1 FROM youtube_transcripts t WHERE t.video_id=v.id)
          AND (SELECT count(*) FROM videos sibling WHERE sibling.job_id=j.id)=1
          AND COALESCE((j.meta->>'caption_retry_count')::integer,0)<3
          AND v.updated_at <= now() - CASE COALESCE((j.meta->>'caption_retry_count')::integer,0)
              WHEN 0 THEN interval '15 minutes' WHEN 1 THEN interval '1 hour'
              ELSE interval '6 hours' END
        ORDER BY v.updated_at, v.id FOR UPDATE OF v,j SKIP LOCKED LIMIT 1
    """)).mappings().first()
    if row is None:
        return None
    connection.execute(
        text("""
        UPDATE jobs SET meta=meta || jsonb_build_object(
            'caption_retry_count', :attempts + 1,
            'caption_retry_history', COALESCE(meta->'caption_retry_history','[]'::jsonb)
              || jsonb_build_array(jsonb_build_object('at',now(),'state',CAST(:state AS text),
                                                     'error',CAST(:error AS text)))), updated_at=now()
        WHERE id=:job_id
    """),
        {
            "attempts": row["attempts"],
            "state": row["previous_state"],
            "error": row["previous_error"],
            "job_id": row["job_id"],
        },
    )
    connection.execute(
        text("""
        UPDATE videos SET caption_ingest_state='pending', updated_at=now() WHERE id=:id
    """),
        {"id": row["id"]},
    )
    return str(row["job_id"])


def run_once(connection, *, retry: bool = False):
    # The existing fetcher records rate limits and terminal missing/invalid captions.
    # A single video per transaction preserves all earlier progress on interruption.
    batch_id = None
    if retry:
        with connection.begin():
            batch_id = schedule_retry(connection)
    with connection.begin():
        if batch_id:
            result = ingest_available_captions(connection, limit=1, batch_id=batch_id)
        else:
            result = ingest_available_captions(connection, limit=1)
        completed = complete_captioned_videos(connection)
    return result, completed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    cycle = 0
    stopping = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stopping.set())
    next_discovery = time.monotonic() + 300  # Existing inventory is ready; ingest first.
    with engine.connect() as connection:
        owned = connection.execute(
            text("SELECT pg_try_advisory_lock(hashtext(:owner))"), {"owner": OWNER_LOCK}
        ).scalar_one()
        connection.commit()
        if not owned:
            raise RuntimeError("another caption-only worker owns this database")
        try:
            with connection.begin():
                completed = complete_captioned_videos(connection)
            print(json.dumps({"event": "caption_only_started", "completed_existing": completed}), flush=True)
            while not stopping.is_set():
                try:
                    if not args.once and time.monotonic() >= next_discovery:
                        with connection.begin():
                            discovery = sync_configured_channels(
                                connection, parse_channel_urls(settings.CHANNEL_SYNC_URLS)
                            )
                        print(json.dumps({"event": "discovery", **asdict(discovery)}), flush=True)
                        next_discovery = time.monotonic() + settings.CHANNEL_SYNC_INTERVAL_SECONDS
                    result, completed = run_once(connection, retry=cycle % 10 == 0)
                    cycle += 1
                    print(
                        json.dumps({"event": "caption_batch", **asdict(result), "videos_completed": completed}),
                        flush=True,
                    )
                    if args.once:
                        return 1 if result.failed or result.rate_limited else 0
                    delay = (
                        max(60, result.cooldown_seconds or 3600)
                        if result.rate_limited
                        else 2 if result.attempted else 60
                    )
                except Exception as exc:
                    connection.rollback()
                    # No raw provider response, signed caption URL or credentials in logs.
                    print(json.dumps({"event": "caption_worker_error", "type": type(exc).__name__}), flush=True)
                    if args.once:
                        raise
                    delay = 300
                stopping.wait(delay)
        finally:
            connection.rollback()
            connection.execute(text("SELECT pg_advisory_unlock(hashtext(:owner))"), {"owner": OWNER_LOCK})
            connection.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
