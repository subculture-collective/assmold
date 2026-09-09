import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, useAuth } from '../services';
import type { ArchiveSummary } from '../types/api';
import {
  buildTimestampLink,
  formatDate,
  formatDuration,
  formatNumber,
} from '../features/archive/format';
import { VideoCard } from '../components/archive';
import { AsyncError } from '../components/async/AsyncFeedback';

const searchExamples = ['World of Warcraft', 'gaming', 'streaming', 'reactions'];

export default function HomePage() {
  const navigate = useNavigate();
  const { user, loading: authLoading, login, loginTwitch } = useAuth();
  const [summary, setSummary] = useState<ArchiveSummary | null>(null);
  const [query, setQuery] = useState('');
  const [summaryState, setSummaryState] = useState<'loading' | 'success' | 'error'>('loading');
  const summaryController = useRef<AbortController | null>(null);

  const loadSummary = useCallback(() => {
    summaryController.current?.abort();
    const controller = new AbortController();
    summaryController.current = controller;
    setSummaryState('loading');
    api
      .getArchiveSummary(controller.signal)
      .then((next) => {
        if (!controller.signal.aborted) {
          setSummary(next);
          setSummaryState('success');
        }
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          console.error('Failed to load archive summary', err);
          setSummaryState('error');
        }
      });
  }, []);

  useEffect(() => {
    loadSummary();
    return () => summaryController.current?.abort();
  }, [loadSummary]);

  function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    navigate(`/search?q=${encodeURIComponent(trimmed)}`);
  }

  const recentVideos = summary?.recent_videos ?? [];
  const suggested = summary?.popular_searches ?? [];
  const newestVideo = recentVideos[0];

  return (
    <div className="basement-home">
      <section className="basement-hero" aria-labelledby="basement-title">
        <div className="basement-scene" aria-hidden="true" />
        <div className="basement-hero-content">
          <div className="basement-kicker">
            <span className="live-speck" /> THE UNOFFICIAL ASMON ARCHIVE{' '}
            <span>EST. IN THE ROT</span>
          </div>
          <h1 id="basement-title" aria-label="ASSMOLD" className="basement-wordmark">
            ASS<span>MOLD</span>
            <i aria-hidden="true">™</i>
          </h1>
          <p className="basement-tagline">
            Nothing washed.
            <br />
            <em>Everything indexed.</em>
          </p>
          <p className="basement-intro">
            AsmonTV. Asmongold Clips. Every rabbit hole, bad take, and three-hour detour. Search the
            transcripts. Find the exact moment.
          </p>
          <div className="basement-hero-links">
            <Link to="/episodes">
              Browse videos and clips <span aria-hidden="true">↗</span>
            </Link>
            <Link to="/explore">
              Explore the archive <span aria-hidden="true">↗</span>
            </Link>
            <Link to="/support">
              Support the archive <span aria-hidden="true">↗</span>
            </Link>
          </div>
        </div>
        <div className="basement-sticker" aria-hidden="true">
          <img src="/icon.svg" alt="" />
          <span>
            UNBRUSHED.
            <br />
            UNOFFICIAL.
          </span>
        </div>
        <span className="basement-scene-note" aria-hidden="true">
          FIG. 01 / DO NOT TOUCH THE SHIRT
        </span>
        <img className="basement-roach hero-roach" src="/roach.svg" alt="" aria-hidden="true" />
        <form onSubmit={onSubmit} className="basement-search">
          <label htmlFor="home-search">DIG SOMETHING UP.</label>
          <div className="basement-search-row">
            <span className="basement-search-symbol" aria-hidden="true">
              ⌕
            </span>
            <input
              id="home-search"
              aria-label="Search the Asmongold archive"
              name="q"
              type="search"
              autoComplete="off"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="A topic, quote, guest, or phrase…"
            />
            <button type="submit" className="btn">
              Search archive <span aria-hidden="true">↗</span>
            </button>
          </div>
          <div className="basement-search-examples">
            <span>POKE AROUND:</span>
            {searchExamples.map((term) => (
              <Link key={term} to={`/search?q=${encodeURIComponent(term)}`}>
                {term}
              </Link>
            ))}
          </div>
        </form>
      </section>
      <div className="basement-ticker" aria-hidden="true">
        <span>NO AIR FRESHENER</span>
        <b>×</b>
        <span>JUST TIMESTAMPS</span>
        <b>×</b>
        <span>ENTER AT YOUR OWN DISGUST</span>
        <b>×</b>
        <span>NO AIR FRESHENER</span>
        <b>×</b>
        <span>JUST TIMESTAMPS</span>
      </div>
      <section className="basement-ledger" aria-label="Archive statistics">
        <div>
          <span>Searchable VODs</span>
          <strong>{summary ? formatNumber(summary.video_count) : '—'}</strong>
          <small>pulled out of the pile</small>
        </div>
        <div>
          <span>Recorded runtime</span>
          <strong>{summary ? formatDuration(summary.total_duration_seconds) : '—'}</strong>
          <small>time you’re not getting back</small>
        </div>
        <div>
          <span>Transcript words</span>
          <strong>{summary ? formatNumber(summary.transcript_word_count) : '—'}</strong>
          <small>every last word of it</small>
        </div>
        <div>
          <span>Index refreshed</span>
          <strong className="ledger-date">
            {summaryState === 'loading' && !summary
              ? 'Checking…'
              : formatDate(summary?.updated_at ?? null)}
          </strong>
          <small>the pile keeps growing</small>
        </div>
      </section>

      {summaryState === 'error' && (
        <AsyncError onRetry={loadSummary} retryLabel="Retry archive summary">
          Archive summary is unavailable.{' '}
          {summary
            ? 'The last successful archive snapshot is still shown.'
            : 'Try again to load archive totals and recent VODs.'}
        </AsyncError>
      )}

      {import.meta.env.VITE_AUTH_ENABLED !== 'false' && (
        <section className="archive-section">
          {!authLoading && !user ? (
            <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
              <div>
                <div className="archive-eyebrow">Save your archive trail</div>
                <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-ink">
                  Sign in to synchronize saved moments and searches.
                </h2>
              </div>
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={login} className="btn min-h-11 px-4 text-sm">
                  Continue with Google
                </button>
                <button
                  type="button"
                  onClick={loginTwitch}
                  className="btn-secondary min-h-11 px-4 text-sm"
                >
                  Continue with Twitch
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <div className="archive-eyebrow">Archive trail</div>
                <p className="mt-2 font-semibold text-ink">
                  {authLoading ? 'Checking your account…' : 'Your saves are synchronized.'}
                </p>
              </div>
              {!authLoading && (
                <Link to="/saved" className="btn-secondary min-h-11 px-4 text-sm">
                  Open my saves
                </Link>
              )}
            </div>
          )}
        </section>
      )}

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="archive-section space-y-5">
          <div className="flex items-end justify-between gap-4">
            <div>
              <div className="archive-eyebrow">Fresh out of the pile</div>
              <h2 className="mt-3 text-3xl font-semibold tracking-[-0.045em] text-ink">
                THE LATEST FILTH.
              </h2>
            </div>
            <Link to="/episodes" className="action-link text-sm">
              All VODs →
            </Link>
          </div>

          {recentVideos.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {recentVideos.slice(0, 6).map((video) => (
                <VideoCard key={video.id} video={video} />
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-border p-8 text-center text-sm text-muted">
              {summaryState === 'loading' && !summary
                ? 'Loading recent VODs…'
                : summaryState === 'error'
                  ? 'Recent VODs could not be loaded. Retry the archive summary.'
                  : 'No recent VODs are available yet.'}
            </div>
          )}
        </div>

        <section aria-label="Archive highlights" className="archive-section flex flex-col gap-6">
          <div>
            <div className="archive-eyebrow">Something festering</div>
            <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-ink">
              Popular searches
            </h2>
            <p className="mt-2 text-sm leading-6 text-muted">
              The subjects people keep digging through. Pick one and follow the smell.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {suggested.length > 0 ? (
              suggested.slice(0, 12).map((item, index) => (
                <Link
                  key={item.term}
                  to={`/search?q=${encodeURIComponent(item.term)}`}
                  className="group inline-flex items-center gap-2 rounded-lg border border-border bg-surface-muted px-3 py-2 text-sm text-ink transition-colors hover:border-accent/60"
                >
                  <span className="translate-y-px font-mono text-[10px] text-subtle">
                    {String(index + 1).padStart(2, '0')}
                  </span>
                  <span className="group-hover:text-accent">{item.term}</span>
                </Link>
              ))
            ) : (
              <p className="text-sm text-muted">
                {summaryState === 'error'
                  ? 'Popular searches could not be loaded. Retry the archive summary.'
                  : 'Search activity will surface useful starting points here.'}
              </p>
            )}
          </div>

          {newestVideo && (
            <Link
              to={buildTimestampLink(newestVideo.id, 0)}
              className="mt-auto rounded-xl border border-accent/20 bg-accent-soft/55 p-4 transition-colors hover:border-accent/50"
            >
              <div className="meta-label text-accent">Newest transcript</div>
              <div className="mt-2 line-clamp-2 font-semibold text-ink">
                {newestVideo.title || 'Open the newest VOD'}
              </div>
              <div className="mt-3 text-sm text-accent">Start reading →</div>
            </Link>
          )}
        </section>
      </section>

      <section className="archive-section grid gap-6 lg:grid-cols-[minmax(0,0.75fr)_minmax(0,1.25fr)] lg:items-center">
        <div>
          <div className="archive-eyebrow">How it works</div>
          <h2 className="mt-3 text-3xl font-semibold tracking-[-0.045em] text-ink">
            GET YOUR HANDS DIRTY.
          </h2>
        </div>
        <ol className="grid gap-3 sm:grid-cols-3">
          {[
            ['01', 'Dig', 'A name. A topic. That one thing he said.'],
            ['02', 'Find', 'Get the quote with the receipts attached.'],
            ['03', 'Watch', 'Jump to the exact second. In context.'],
          ].map(([number, title, copy]) => (
            <li key={number} className="border-l border-border pl-4">
              <div className="font-mono text-xs text-accent">{number}</div>
              <div className="mt-2 font-semibold text-ink">{title}</div>
              <p className="mt-1 text-sm leading-6 text-muted">{copy}</p>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
