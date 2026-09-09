import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

export function LightRoaches({ theme }: { theme: 'light' | 'dark' }) {
  const previousTheme = useRef(theme);
  const [scattering, setScattering] = useState(false);
  useEffect(() => {
    const lightsOn = previousTheme.current === 'dark' && theme === 'light';
    previousTheme.current = theme;
    setScattering(lightsOn && !window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    if (!lightsOn) return;
    const timer = window.setTimeout(() => setScattering(false), 1600);
    return () => window.clearTimeout(timer);
  }, [theme]);
  return scattering ? (
    <div className="roach-scatter" aria-hidden="true" data-testid="roach-scatter">
      {Array.from({ length: 6 }, (_, i) => (
        <img key={i} className={`scatter-roach scatter-roach-${i}`} src="/roach.svg" alt="" />
      ))}
    </div>
  ) : null;
}

export function CigaretteSurprise() {
  const [lit, setLit] = useState(false);
  useEffect(() => {
    if (!lit) return;
    const timer = window.setTimeout(() => setLit(false), 3200);
    return () => window.clearTimeout(timer);
  }, [lit]);
  return (
    <div className="cigarette-surprise">
      <button
        className="forgotten-cigarette"
        type="button"
        aria-label="Light the abandoned cigarette"
        title="Someone left this here…"
        disabled={lit}
        onClick={() => setLit(true)}
      >
        <span className="cigarette-filter" />
        <span className="cigarette-paper" />
        <span className={lit ? 'cigarette-ash lit' : 'cigarette-ash'} />
      </button>
      {lit &&
        createPortal(
          <div className="basement-blast" role="status">
            <span className="sr-only">
              Easter egg: the cigarette sets off a cartoon oxygen-tank explosion. The basement
              survives.
            </span>
            <div className="blast-scene" aria-hidden="true">
              <div className="cartoon-tank">
                <span>O₂</span>
              </div>
              <div className="blast-cloud">
                <b>BOOM.</b>
                <span>WELL. THAT CLEARED THE AIR.</span>
              </div>
            </div>
          </div>,
          document.body
        )}
    </div>
  );
}
