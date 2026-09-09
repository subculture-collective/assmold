# Assmold search and enrichment

Purpose: find potentially contradictory positions and statements, preserving the
quotes, dates, speaker context and source-video timestamps needed to assess them.
Similarity is not a contradiction verdict. Reacted-to videos and guests appear
in captions; speaker attribution must be checked against the video.

## Search paths

- `/search`: existing PostgreSQL indexed word, phrase and stemmed-topic search.
- `/semantic`: embedding-based meaning search with From/To dates. Select two
  passages to compare text, dates and source links; selections survive a new query
  on the same page. They are a temporary local comparison, not a published claim.
- `/api/semantic/search?q=...&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD` and
  `/api/semantic/status`: separate sidecar routes; original API remains unchanged.

The semantic index uses `openai/text-embedding-3-small`, 512 dimensions, through
[OpenRouter's embeddings endpoint](https://openrouter.ai/docs/api/api-reference/embeddings/create-embeddings).
Qdrant 1.18.1 stores cosine vectors and source payloads privately, without host
ports. [Qdrant's point API](https://qdrant.tech/documentation/manage-data/points/)
provides deterministic upserts. Ninety-second caption windows overlap by thirty
seconds. A video generation becomes searchable only after all its batches finish;
old generations are removed afterward. Source captions are never changed.

Indexing follows available English captions, newest first. Coverage is displayed
in the results, so partial indexing is not mistaken for the entire archive.
This supplements the original indexed search; it does not replace it or claim
that the original search already used query-time vectors. No automated
contradiction classification or verified speaker diarization is claimed.

Provider vectors are validated for order, count, dimensions and finite values.
Query vectors are cached for seven days. A global 120-request/minute limit and
per-query locks protect public provider calls. Provider errors become retryable
503 responses rather than false empty results. Indexing failures write a durable
pause file; restarts do not replay uncertain paid requests. Inspect the error
before explicitly clearing that pause. Token counts are retained in Redis;
OpenRouter billing remains the authority for embedding costs.

## Categories and chapters

The inherited DeepSeek V4 Pro/OpenRouter pipeline remains intact, including
chapter evidence validation, category evidence requirements, review provenance,
quality-gated automatic approval, bounded retries and failure/credit breakers.
Assmold prompt version `assmold-episode-enrichment-v1` replaces Hasan-specific
Chadvice/OKBuddy categories with Commentary/Technology. Existing Gaming, News,
Politics, React, Guests, Debate, Interview and IRL categories remain.

User authorized ongoing paid processing without an additional trial cap.
Existing HasanAra operational safeguards were retained ($1/video, $250/rolling
24h, 10,000 attempts/24h); these are circuit breakers, not a new trial budget.
No unvalidated candidate is published. One initial inherited-prompt run failed
for no sustained category and remains recorded; later verified runs succeeded.

## Operations

Almaz root: `/mnt/spektr/server/projects/assmold`.
Use base `docker-compose.assmold.yml` plus `docker-compose.assmold-intelligence.yml`.
The `enrichment` service requires `--profile enrichment`. All services belong to
Assmold; HasanAra's containers/database are not modified.

- `vectors`: Qdrant, volume `assmold_semantic-vectors`.
- `semantic`: public read/search sidecar, private vector-store access.
- `semantic-indexer`: one advisory-locked writer, persistent SQLite completion
  manifest and pause file in volume `assmold_semantic-state`.
- `enrichment`: continuous quality-gated category/chapter creation.
- Private environment: `releases/enrichment-20260909/.env.enrichment` (0600).
  Keys were transferred on Almaz without printing their values.

Caddy adds only `/api/semantic/*`, routed to `assmold-semantic:8001`. Backup:
`/opt/server/management/config/caddy/sites/assmold.Caddyfile.before-semantic-20260909`.
Stop intelligence services by their names; never use whole-project `down`.
Keep both vector and completion-state volumes together when backing up/restoring.

Pre-enrichment PostgreSQL dump:
`releases/enrichment-20260909/before-enrichment.dump`, archive listing verified,
SHA256 `bf8d4376f82a9c76f9b9ca3c9bdde3985b74073032c67e2ac40d21c1803a520d`.
Initial profile canary `6a3e88e5-d48e-43a5-bba9-a02dbe46c35b` published six chapters
and six assignments after a successful rollback rehearsal and committed approval.

## Validation

88 enrichment tests pass against a fresh, fully migrated disposable PostgreSQL
instance. Seven semantic unit/API tests cover window provenance, response
validation, date bounds, deduplication, caching and failure responses. Frontend
273 passed/one skipped, with tests for comparison and retries. Real provider
indexing/query retrieval and mobile two-source comparison were also exercised.
This is an initial retrieval implementation, not a measured corpus-wide
contradiction-detection benchmark. Indexing and enrichment continue in background.
