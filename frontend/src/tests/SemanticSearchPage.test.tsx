import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import SemanticSearchPage from '../routes/SemanticSearchPage';

const items = [0, 1].map((i) => ({
  id: `p${i}`,
  video_id: `v${i}`,
  youtube_id: `y${i}`,
  title: `Statement video ${i}`,
  channel_name: 'AsmonTV',
  uploaded_at: i === 1 ? null : `202${i + 4}-01-01T00:00:00Z`,
  start_ms: 12000,
  end_ms: 42000,
  text: `Source statement ${i}`,
  score: 0.7,
}));
afterEach(() => vi.unstubAllGlobals());
describe('meaning search', () => {
  it('keeps dated source passages available for a two-statement comparison', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ items, indexed_videos: 20 }) })
    );
    render(
      <MemoryRouter initialEntries={['/semantic?q=free+speech&from=2024-01-01']}>
        <SemanticSearchPage />
      </MemoryRouter>
    );
    const buttons = await screen.findAllByRole('button', { name: 'Compare statement' });
    fireEvent.click(buttons[0]);
    fireEvent.click(buttons[1]);
    expect(screen.getByRole('region', { name: 'Compare statements' })).toHaveTextContent(
      'Source statement 0'
    );
    expect(screen.getAllByRole('link', { name: 'Watch at 0:12' })).toHaveLength(2);
    expect(screen.getByRole('region', { name: 'Compare statements' })).toHaveTextContent(
      'Date unavailable'
    );
    expect(vi.mocked(fetch).mock.calls[0][0]).toContain('date_from=2024-01-01');
    fireEvent.click(screen.getByRole('button', { name: 'Clear comparison' }));
    expect(screen.queryByRole('region', { name: 'Compare statements' })).toBeNull();
  });
  it('shows a retryable service failure instead of implying no matches', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue({ ok: false, json: async () => ({ detail: 'Meaning search is busy.' }) })
    );
    render(
      <MemoryRouter initialEntries={['/semantic?q=gaming']}>
        <SemanticSearchPage />
      </MemoryRouter>
    );
    expect(await screen.findByRole('alert')).toHaveTextContent('Meaning search is busy.');
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect(screen.queryByText(/No matching passages/)).toBeNull();
  });
});
