import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTheme } from '../services';

const colors = [
  ['Basement tar', 'canvas', '#15130F'],
  ['Old shirt', 'surface', '#211E17'],
  ['Nicotine teeth', 'ink', '#E6D6AD'],
  ['Mold bloom', 'accent', '#C8D66A'],
  ['Raw gums', 'danger', '#F18B72'],
  ['Stale grease', 'warning', '#E8B35D'],
];

export default function DesignSystemPage() {
  const { theme, toggleTheme } = useTheme();
  const [query, setQuery] = useState('');
  const [tab, setTab] = useState('Surfaces');
  const [saved, setSaved] = useState(false);
  const navigate = useNavigate();
  return (
    <div className="rot-system">
      <header className="rot-system-cover rot-paper">
        <div className="archive-eyebrow">ASSMOLD / DESIGN SYSTEM / VOL. 01</div>
        <img src="/icon.svg" alt="" className="rot-system-teeth" />
        <h1>
          THE ROT
          <br />
          <span>IS THE BRAND.</span>
        </h1>
        <p>
          Basement filth. Bootleg zine. A search engine that looks like it lives under the desk.
        </p>
        <div className="rot-system-actions">
          <button className="btn" onClick={toggleTheme}>
            Switch to {theme === 'dark' ? 'light' : 'dark'} mode
          </button>
          <Link className="action-link" to="/">
            Enter the basement ↗
          </Link>
        </div>
        <span className="rot-stamp">
          DO NOT
          <br />
          SANITIZE
        </span>
      </header>

      <section className="rot-system-section" aria-labelledby="palette-title">
        <div className="rot-section-heading">
          <span>01 / THE DISCOLORATION</span>
          <h2 id="palette-title">Nothing here is a clean color.</h2>
        </div>
        <div className="rot-palette">
          {colors.map(([name, token, hex]) => (
            <div key={token} className="rot-swatch">
              <div style={{ background: `var(--color-${token})` }} />
              <h3>{name}</h3>
              <code>--color-{token}</code>
              <small>{theme === 'dark' ? hex : 'Light mode variant'}</small>
            </div>
          ))}
        </div>
      </section>

      <section className="rot-system-section rot-type" aria-labelledby="type-title">
        <div className="rot-section-heading">
          <span>02 / READ THE ROOM</span>
          <h2 id="type-title">Loud headlines. Legible evidence.</h2>
        </div>
        <div className="rot-type-sample">
          <span className="rot-wordmark">ASSMOLD</span>
          <p>Rubik Dirt · identity only · chipped, clotted, unmistakable.</p>
        </div>
        <div className="rot-type-sample">
          <h3>
            NOTHING WASHED.
            <br />
            EVERYTHING INDEXED.
          </h3>
          <p>Barlow Condensed · heavy headlines · tight and impatient.</p>
        </div>
        <div className="rot-type-sample">
          <p className="rot-body-sample">
            Every rabbit hole leaves a trail. Search the words, read the context, and jump to the
            exact moment.
          </p>
          <p>Barlow · body copy · comfortable even three hours into a transcript.</p>
        </div>
        <div className="rot-type-sample">
          <code>00:42:17 / ASMONTV / TRANSCRIPT MATCH</code>
          <p>IBM Plex Mono · timestamps, labels, receipts.</p>
        </div>
      </section>

      <section className="rot-system-section" aria-labelledby="materials-title">
        <div className="rot-section-heading">
          <span>03 / TOUCH AT YOUR OWN RISK</span>
          <h2 id="materials-title">The surface treatment.</h2>
        </div>
        <div className="rot-materials">
          <article className="rot-paper">
            <span className="archive-eyebrow">Grease-stained paper</span>
            <h3>DIG SOMETHING UP.</h3>
            <p>
              Nicotine stock, tape tabs, ring stains and torn edges. For the most useful thing in
              the room.
            </p>
          </article>
          <article className="rot-encrusted">
            <span className="archive-eyebrow">Mold in the corners</span>
            <h3>LEFT HERE TO FESTER.</h3>
            <p>
              Tar surfaces, rusty seams, spotted grime. Texture gathers around the edges of content.
            </p>
            <img src="/roach.svg" alt="" className="rot-material-roach" />
          </article>
          <article className="rot-receipt">
            <span className="archive-eyebrow">A receipt for every claim</span>
            <h3>CHECK THE TIMESTAMP.</h3>
            <p>
              Perforated dividers. Mono metadata. Straight reading lines through a crooked
              interface.
            </p>
            <span className="timestamp-pill">00:42:17</span>
          </article>
        </div>
      </section>

      <section className="rot-system-section" aria-labelledby="components-title">
        <div className="rot-section-heading">
          <span>04 / WORKING PARTS</span>
          <h2 id="components-title">Filthy shell. Working controls.</h2>
        </div>
        <div className="rot-component-grid">
          <div className="archive-section space-y-5">
            <h3 className="text-2xl">Buttons & inputs</h3>
            <form
              onSubmit={(event) => {
                event.preventDefault();
                if (query.trim()) navigate(`/search?q=${encodeURIComponent(query.trim())}`);
              }}
              className="space-y-3"
            >
              <label htmlFor="specimen-query" className="block font-mono text-xs">
                Search the archive
              </label>
              <input
                id="specimen-query"
                className="input w-full"
                placeholder="Dig for a phrase…"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
              <div className="rot-system-actions">
                <button className="btn" type="submit">
                  Search archive ↗
                </button>
                <button
                  className="btn-secondary"
                  type="button"
                  aria-pressed={saved}
                  onClick={() => setSaved(!saved)}
                >
                  {saved ? 'Saved ✓' : 'Save moment'}
                </button>
                <button className="btn" type="button" disabled>
                  Unavailable
                </button>
              </div>
            </form>
            <p className="text-sm text-muted" aria-live="polite">
              {saved
                ? 'Example moment saved for this preview.'
                : 'Try the controls. Search opens real archive results.'}
            </p>
          </div>
          <div className="archive-section space-y-5">
            <h3 className="text-2xl">Selection & feedback</h3>
            <div className="rot-system-actions" aria-label="Specimen views">
              {['Surfaces', 'Motion', 'Voice'].map((item) => (
                <button
                  className={tab === item ? 'btn' : 'btn-secondary'}
                  aria-pressed={tab === item}
                  key={item}
                  onClick={() => setTab(item)}
                >
                  {item}
                </button>
              ))}
            </div>
            <p className="text-muted">
              {tab === 'Surfaces'
                ? 'Square edges. Hard offset shadows. A little tape, a little tilt, and a lot of accumulated grease.'
                : tab === 'Motion'
                  ? 'A roach skitters at the edge after a long pause. Controls respond immediately. Reduced-motion preferences stop the decorative movement.'
                  : 'Gross in the headings. Precise in the instructions. Errors explain what happened and how to recover.'}
            </p>
            <div className="alert-warning">
              Example warning: the archive could not load. Try again.
            </div>
            <div className="rot-empty">
              <img src="/roach.svg" alt="" />
              <h3>Nothing in this corner.</h3>
              <p>Try a shorter phrase or clear your filters.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="rot-system-section" aria-labelledby="art-title">
        <div className="rot-section-heading">
          <span>05 / THE SOURCE OF THE SMELL</span>
          <h2 id="art-title">One room. An entire identity.</h2>
        </div>
        <img
          className="rot-artwork"
          src="/basement.webp"
          alt="Fictional gaunt adult gamer in a stained shirt, seated in a decaying basement surrounded by empty food containers, crumpled tissues, a stained sock and cockroaches."
          loading="lazy"
        />
        <p className="mt-4 text-sm text-muted">
          Original fictional mascot artwork. Crop around the seated character; leave the dark wall
          for type. Food containers, stained fabric and roaches supply the visual vocabulary.
        </p>
      </section>
    </div>
  );
}
