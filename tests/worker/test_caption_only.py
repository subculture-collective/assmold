import subprocess
import sys
import uuid
from unittest.mock import MagicMock

from sqlalchemy import text

from worker.caption_ingest import CaptionIngestionResult
from worker.caption_only import complete_captioned_videos, run_once, schedule_retry


def test_entrypoint_does_not_import_native_or_audio_pipeline():
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import worker.caption_only; "
            "assert not set(sys.modules).intersection({'torch','faster_whisper','worker.pipeline',"
            "'worker.loop','worker.audio','worker.native_pipeline','worker.whisper_runner'})",
        ],
        check=True,
    )


def test_completion_requires_real_captions_and_owned_job():
    db = MagicMock()
    db.execute.return_value.rowcount = 2
    assert complete_captioned_videos(db) == 2
    statement = str(db.execute.call_args_list[0].args[0])
    assert "caption_ingest_state='completed'" in statement
    assert "s.end_ms>s.start_ms" in statement
    assert "created_by'='channel_sync'" in statement
    assert "INSERT INTO transcripts" not in statement


def test_one_video_transaction_preserves_rate_limit(monkeypatch):
    db = MagicMock()
    result = CaptionIngestionResult(1, 0, 0, 0, True, 3600)
    fetch = MagicMock(return_value=result)
    monkeypatch.setattr("worker.caption_only.ingest_available_captions", fetch)
    assert run_once(db)[0] == result
    fetch.assert_called_once_with(db, limit=1)
    db.begin.assert_called_once()


def test_caption_completion_is_idempotent_and_preserves_native_rows(db_session):
    from worker.channel_sync import ChannelVideo, SqlChannelSyncRepository

    identifier = str(uuid.uuid4())
    SqlChannelSyncRepository(db_session.connection()).enqueue_missing(
        ChannelVideo(identifier, "caption-only fixture", 60, "fixture")
    )
    video = db_session.execute(text("SELECT id FROM videos WHERE youtube_id=:id"), {"id": identifier}).scalar_one()
    db_session.execute(text("UPDATE videos SET caption_ingest_state='completed' WHERE id=:id"), {"id": video})
    assert complete_captioned_videos(db_session) == 0
    transcript = db_session.execute(
        text("""
        INSERT INTO youtube_transcripts (video_id,language,kind,full_text)
        VALUES (:id,'en','auto','real fixture text') RETURNING id
    """),
        {"id": video},
    ).scalar_one()
    db_session.execute(
        text("""
        INSERT INTO youtube_segments(youtube_transcript_id,start_ms,end_ms,text)
        VALUES (:id,0,1000,'real fixture text')
    """),
        {"id": transcript},
    )
    assert complete_captioned_videos(db_session) == 1
    assert complete_captioned_videos(db_session) == 0
    assert db_session.execute(text("SELECT state FROM videos WHERE id=:id"), {"id": video}).scalar_one() == "completed"
    assert (
        db_session.execute(text("SELECT count(*) FROM transcripts WHERE video_id=:id"), {"id": video}).scalar_one() == 0
    )


def test_retry_backoff_limit_and_history(db_session):
    from worker.channel_sync import ChannelVideo, SqlChannelSyncRepository

    identifier = str(uuid.uuid4())
    SqlChannelSyncRepository(db_session.connection()).enqueue_missing(
        ChannelVideo(identifier, "retry fixture", 60, "fixture")
    )
    video, job = db_session.execute(text("SELECT id,job_id FROM videos WHERE youtube_id=:id"), {"id": identifier}).one()
    for attempt in range(3):
        db_session.execute(
            text(
                "UPDATE videos SET caption_ingest_state='failed',"
                " caption_ingest_error='retained failure',updated_at=now() WHERE id=:id"
            ),
            {"id": video},
        )
        assert schedule_retry(db_session) is None
        db_session.execute(text("UPDATE videos SET updated_at=now()-interval '7 hours' WHERE id=:id"), {"id": video})
        assert schedule_retry(db_session) == str(job)
        assert schedule_retry(db_session) is None
        meta = db_session.execute(text("SELECT meta FROM jobs WHERE id=:id"), {"id": job}).scalar_one()
        assert meta["caption_retry_count"] == attempt + 1
        assert len(meta["caption_retry_history"]) == attempt + 1
        assert meta["caption_retry_history"][-1]["error"] == "retained failure"
    db_session.execute(
        text("UPDATE videos SET caption_ingest_state='unavailable'," " updated_at=now()-interval '1 day' WHERE id=:id"),
        {"id": video},
    )
    assert schedule_retry(db_session) is None
