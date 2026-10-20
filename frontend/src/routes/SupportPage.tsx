import { Link } from 'react-router-dom';
import { SUPPORT_URL } from '../services/support';

const fundingLines = [
  {
    number: '01',
    title: 'Keep the archive online',
    copy: 'Storage, backups, bandwidth, and the systems that keep thousands of broadcasts available.',
  },
  {
    number: '02',
    title: 'Turn broadcasts into a record',
    copy: 'Transcription, search indexing, chapter generation, and the ongoing work of citing every result.',
  },
  {
    number: '03',
    title: 'Keep access public',
    copy: 'No paywall around search, transcripts, timelines, or the source links behind a claim.',
  },
];

export default function SupportPage() {
  return (
    <div className="space-y-5 lg:space-y-7">
      <section className="archive-masthead overflow-hidden">
        <div className="relative z-10 grid min-h-[31rem] gap-10 px-5 py-9 sm:px-8 lg:grid-cols-[minmax(0,1.15fr)_minmax(20rem,0.7fr)] lg:items-end lg:px-12 lg:py-14">
          <div className="max-w-4xl space-y-7">
            <div className="flex flex-wrap items-center gap-2">
              <span className="archive-eyebrow">Support assmold</span>
              <span className="source-pill">public infrastructure</span>
            </div>
            <h1 className="archive-display">Keep the public record searchable.</h1>
            <p className="max-w-2xl text-lg leading-8 text-muted sm:text-xl">
              SUBCULT maintains the tools behind this unofficial archive. Support the studio’s work
              on searchable archives and independent software.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <a href={SUPPORT_URL} className="btn min-h-12 px-6">
                Support SUBCULT
              </a>
              <Link to="/about" className="action-link text-sm font-semibold">
                How the archive works →
              </Link>
            </div>
          </div>

          <aside className="archive-section border-accent/25" aria-label="Project independence">
            <div className="archive-eyebrow">Independent project</div>
            <p className="mt-4 text-xl font-semibold leading-8 tracking-[-0.025em] text-ink">
              Built by Subcult. Not operated by or affiliated with Asmongold, Twitch, or YouTube.
            </p>
            <p className="mt-4 text-sm leading-6 text-muted">
              Contributions go to SUBCULT, not Asmongold. They support the studio across its
              projects and do not buy editorial influence, special access or content from the
              creators whose broadcasts are indexed here.
            </p>
          </aside>
        </div>
      </section>

      <section className="archive-section">
        <div className="grid gap-8 lg:grid-cols-[minmax(14rem,0.45fr)_minmax(0,1fr)]">
          <div>
            <div className="archive-eyebrow">Where support goes</div>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.045em] text-ink">
              A small public utility with real operating costs.
            </h2>
          </div>
          <ol className="divide-y divide-border border-y border-border">
            {fundingLines.map((line) => (
              <li key={line.number} className="grid gap-3 py-6 sm:grid-cols-[3rem_14rem_1fr]">
                <span className="font-mono text-xs text-accent">{line.number}</span>
                <h3 className="font-semibold text-ink">{line.title}</h3>
                <p className="text-sm leading-6 text-muted">{line.copy}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="grid gap-5 md:grid-cols-2">
        <div className="archive-section">
          <div className="archive-eyebrow">Payment boundary</div>
          <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-ink">
            Support goes to the studio.
          </h2>
          <p className="mt-3 text-sm leading-6 text-muted">
            The central Support page explains SUBCULT’s offer and links to Patreon. Support is
            voluntary and separate from archive access. No payment details are collected here.
          </p>
        </div>
        <div className="archive-section">
          <div className="archive-eyebrow">No access tier</div>
          <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-ink">
            The archive stays public whether you contribute or not.
          </h2>
          <p className="mt-3 text-sm leading-6 text-muted">
            Search, transcripts, episode pages, and cited source links remain available without a
            contribution. Support is voluntary.
          </p>
        </div>
      </section>
    </div>
  );
}
