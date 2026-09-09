import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CigaretteSurprise, LightRoaches } from '../components/BasementEffects';

describe('basement easter eggs', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(window, 'matchMedia').mockReturnValue({ matches: false } as MediaQueryList);
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });
  it('scatters only when dark becomes light, then cleans up', () => {
    const { rerender } = render(<LightRoaches theme="light" />);
    expect(screen.queryByTestId('roach-scatter')).toBeNull();
    rerender(<LightRoaches theme="dark" />);
    expect(screen.queryByTestId('roach-scatter')).toBeNull();
    rerender(<LightRoaches theme="light" />);
    expect(screen.getByTestId('roach-scatter')).toHaveAttribute('aria-hidden', 'true');
    act(() => vi.advanceTimersByTime(1600));
    expect(screen.queryByTestId('roach-scatter')).toBeNull();
  });
  it('does not scatter with reduced motion enabled', () => {
    vi.mocked(window.matchMedia).mockReturnValue({ matches: true } as MediaQueryList);
    const { rerender } = render(<LightRoaches theme="dark" />);
    rerender(<LightRoaches theme="light" />);
    expect(screen.queryByTestId('roach-scatter')).toBeNull();
  });
  it('clears an interrupted scatter when switching back to dark', () => {
    const { rerender } = render(<LightRoaches theme="dark" />);
    rerender(<LightRoaches theme="light" />);
    rerender(<LightRoaches theme="dark" />);
    expect(screen.queryByTestId('roach-scatter')).toBeNull();
  });
  it('requires a click for the explosion and resets for another visit', () => {
    render(<CigaretteSurprise />);
    const button = screen.getByRole('button', { name: 'Light the abandoned cigarette' });
    expect(screen.queryByRole('status')).toBeNull();
    fireEvent.click(button);
    expect(screen.getByRole('status')).toHaveTextContent('cartoon oxygen-tank explosion');
    expect(button).toBeDisabled();
    act(() => vi.advanceTimersByTime(3200));
    expect(screen.queryByRole('status')).toBeNull();
    expect(button).toBeEnabled();
  });
});
