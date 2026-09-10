# Caption-only acquisition

The Assmold worker uses `worker.caption_only`, not `worker.loop`. Its dedicated
`Dockerfile.assmold-captions` starts from the CPU-only API dependency image and
contains no Whisper, torch or CUDA packages. Do not enable native transcription
as a fallback for missing captions.

The existing database includes both AsmonTV and Asmongold Clips. It is isolated
from HasanAra. Keep this database as the authoritative inventory rather than
starting a second competing local backfill.

The importer retains existing native transcripts but never creates new ones.
Captioned videos with at least one nonempty positive-duration segment complete
without native transcription. Existing channel-sync jobs finish only when all
their videos complete. No transcript or historical row is deleted by this mode.

Each acquisition commits independently. The worker honors YouTube rate-limit
cooldowns, records missing/failed captions separately, and sleeps between requests.
Failed/unavailable captions are not falsely completed or sent to Whisper. Each
video gets at most three additional retries after 15 minutes, one hour and six
hours. Every tenth worker cycle considers an eligible retry; retry counts and
prior errors are persisted in channel-sync job metadata. Exhausted records stay
failed/unavailable without blocking the remaining inventory. Successful requests
have a two-second pause; provider rate-limit cooldowns still take precedence.
Startup uses existing jobs
immediately; recurring discovery begins after five minutes and repeats every six
hours. A database advisory lock prevents two caption-only owners.

Runtime: `/mnt/spektr/server/projects/assmold` on Almaz. Use the existing private
`.env.assmold`; never copy credentials into logs. The worker can be stopped with
`docker stop -t 60 assmold-worker-1`. Its normal command is
`python3 -m worker.caption_only`; `--once` performs one acquisition transaction.
The Compose worker service uses `assmold-captions:retry-v1` and can be rebuilt from
this checkout. Frontend/API images are unchanged by the caption-only switch.

Pre-switch backup: `assmold-before-caption-only-20260908.dump` in the runtime root,
SHA256 `0a10209cc1310c5ed1c7cb995fc7dc8ef012c8b7742a60eaea1e3e8a024d1673`.
It is a PostgreSQL custom-format dump; its archive listing was verified. Preserve
it and the existing daily backups. Before future transfer, stop just the caption
worker, take a fresh custom-format dump, copy it with a checksum, restore into a
new empty isolated PostgreSQL instance, and compare channel/transcript/segment
counts before changing ownership. Never restore over HasanAra.

The previous mixed-mode Compose file is saved as
`docker-compose.assmold.before-caption-only-20260908.yml` for configuration
reference only; restoring its worker would re-enable unwanted Whisper work.
This caption worker never invokes paid enrichment. The separate Assmold enrichment
and semantic-indexer services were subsequently authorized and enabled; see
`docs/assmold-intelligence.md`. Do not infer deployment-wide paid-processing state
from the caption worker's configuration.
