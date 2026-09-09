import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
const sourceDate = (value: string | null) =>
  value
    ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeZone: 'UTC' }).format(
        new Date(value)
      )
    : 'Date unavailable';

type Statement = {
  id: string;
  video_id: string;
  youtube_id: string;
  title: string;
  channel_name: string;
  uploaded_at: string | null;
  start_ms: number;
  end_ms: number;
  text: string;
  score: number;
};
const time = (ms: number) =>
  `${Math.floor(ms / 60000)}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}`;

export default function SemanticSearchPage() {
  const [params, setParams] = useSearchParams();
  const q = params.get('q') || '';
  const [draft, setDraft] = useState(q);
  const [from, setFrom] = useState(params.get('from') || '');
  const [to, setTo] = useState(params.get('to') || '');
  const [items, setItems] = useState<Statement[]>([]);
  const [selected, setSelected] = useState<Statement[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [coverage, setCoverage] = useState<number | null>(null);
  const [attempt, setAttempt] = useState(0);
  const fromParam = params.get('from') || '';
  const toParam = params.get('to') || '';
  useEffect(() => {
    setDraft(q);
    setFrom(fromParam);
    setTo(toParam);
  }, [q, fromParam, toParam]);
  useEffect(() => {
    if (q.trim().length < 2) {
      setItems([]);
      setError('');
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError('');
    setItems([]);
    const query = new URLSearchParams({ q });
    if (fromParam) query.set('date_from', fromParam);
    if (toParam) query.set('date_to', toParam);
    fetch(`/api/semantic/search?${query}`, { signal: controller.signal })
      .then(async (response) => {
        const body = await response.json();
        if (!response.ok)
          throw new Error(
            typeof body.detail === 'string' ? body.detail : 'Meaning search could not load.'
          );
        return body;
      })
      .then((body) => {
        setItems(body.items);
        setCoverage(body.indexed_videos);
      })
      .catch((e) => {
        if (!controller.signal.aborted)
          setError(e instanceof Error ? e.message : 'Meaning search could not load.');
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [q, fromParam, toParam, attempt]);
  const choose = (item: Statement) =>
    setSelected((current) =>
      current.some((x) => x.id === item.id)
        ? current.filter((x) => x.id !== item.id)
        : current.length < 2
          ? [...current, item]
          : [current[0], item]
    );
  const source = (item: Statement) =>
    `/v/${item.video_id}?t=${Math.floor(item.start_ms / 1000)}#moment-${item.start_ms}`;
  return (
    <div className="space-y-6">
      <section className="archive-masthead p-5 sm:p-8">
        <div className="archive-eyebrow">Search meaning</div>
        <h1 className="mt-3 text-4xl sm:text-6xl">Same subject. Different story?</h1>
        <p className="mt-4 max-w-3xl text-muted">
          Describe a position or claim. Find related statements even when the wording changes, then
          choose two to compare their dates and context.
        </p>
        <nav className="mt-5 flex gap-4" aria-label="Search method">
          <Link className="btn-secondary" to={`/search?q=${encodeURIComponent(q)}`}>
            Search words
          </Link>
          <span className="btn" aria-current="page">
            Search meaning
          </span>
        </nav>
        <form
          className="mt-6 space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            const next = new URLSearchParams({ q: draft.trim() });
            if (from) next.set('from', from);
            if (to) next.set('to', to);
            setParams(next);
            setAttempt((x) => x + 1);
          }}
        >
          <label className="block" htmlFor="meaning-query">
            Position, claim, or idea
          </label>
          <div className="flex flex-wrap gap-3">
            <input
              id="meaning-query"
              className="input w-full min-w-0 sm:w-auto sm:flex-1"
              minLength={2}
              maxLength={500}
              required
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="What has he said about free speech and banning people?"
            />
            <button className="btn" type="submit">
              Find statements
            </button>
          </div>
          <div className="grid max-w-md grid-cols-2 gap-3">
            <label className="text-sm">
              From
              <input
                className="input mt-1 w-full"
                type="date"
                value={from}
                onChange={(e) => setFrom(e.target.value)}
              />
            </label>
            <label className="text-sm">
              To
              <input
                className="input mt-1 w-full"
                type="date"
                value={to}
                min={from || undefined}
                onChange={(e) => setTo(e.target.value)}
              />
            </label>
          </div>
        </form>
      </section>
      {selected.length > 0 && (
        <section className="archive-section" aria-label="Compare statements">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-3xl">Then. Now. Compare.</h2>
            <button className="btn-secondary" onClick={() => setSelected([])}>
              Clear comparison
            </button>
          </div>
          <p className="mt-2 text-sm text-muted">
            Check who is speaking: captions can include guests and reacted-to videos. Read both
            passages and watch the context. Similarity alone does not establish a contradiction.
          </p>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {selected.map((item, i) => (
              <article key={item.id} className="rot-receipt p-5">
                <span className="meta-label">
                  Statement {i + 1} · {sourceDate(item.uploaded_at)}
                </span>
                <h3 className="mt-3 text-xl">{item.title}</h3>
                <blockquote className="my-4 max-h-80 overflow-y-auto whitespace-pre-wrap leading-7">
                  {item.text}
                </blockquote>
                <Link className="btn-secondary" to={source(item)}>
                  Watch at {time(item.start_ms)}
                </Link>
                <button
                  className="btn-ghost ml-2"
                  onClick={() => choose(item)}
                  aria-label={`Remove statement ${i + 1}`}
                >
                  Remove
                </button>
              </article>
            ))}
            {selected.length === 1 && (
              <p className="p-5 text-muted">
                Choose another statement from these results, or search for a different position or
                date.
              </p>
            )}
          </div>
        </section>
      )}
      {loading && <p role="status">Finding related statements…</p>}
      {error && (
        <div className="alert-warning" role="alert">
          {error}
          <button className="btn-secondary ml-3" onClick={() => setAttempt((x) => x + 1)}>
            Retry
          </button>
        </div>
      )}
      {!loading && !error && q && (
        <p className="text-sm text-muted">
          {items.length
            ? `${items.length} closest passages`
            : 'No matching passages in this date range.'}
          {coverage !== null &&
            ` · ${coverage.toLocaleString()} captioned videos available in meaning search. Coverage reflects the captions indexed so far.`}
        </p>
      )}
      <div className="space-y-4">
        {items.map((item) => (
          <article className="archive-section" key={item.id}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span className="meta-label">
                {item.channel_name} · {sourceDate(item.uploaded_at)} · {time(item.start_ms)}
              </span>
              <button
                className="btn-secondary"
                aria-pressed={selected.some((x) => x.id === item.id)}
                onClick={() => choose(item)}
              >
                {selected.some((x) => x.id === item.id)
                  ? 'Selected for comparison'
                  : 'Compare statement'}
              </button>
            </div>
            <h2 className="mt-3 text-2xl">
              <Link to={source(item)}>{item.title}</Link>
            </h2>
            <blockquote className="my-4 whitespace-pre-wrap leading-7 text-muted">
              {item.text}
            </blockquote>
            <Link className="action-link" to={source(item)}>
              Read and watch in context ↗
            </Link>
          </article>
        ))}
      </div>
    </div>
  );
}
