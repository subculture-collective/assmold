import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, it, vi } from 'vitest';
import axe from 'axe-core';
import SupportPage from '../routes/SupportPage';
import { api } from '../services';

it('identifies the studio recipient and works without donation configuration', async () => {
  const config = vi.spyOn(api, 'getSupportConfig');
  const { container } = render(
    <MemoryRouter>
      <SupportPage />
    </MemoryRouter>
  );
  expect(screen.getByRole('link', { name: 'Support SUBCULT' })).toHaveAttribute(
    'href',
    'https://subcult.tv/support'
  );
  expect(screen.getByText(/Contributions go to SUBCULT, not Asmongold/)).toBeInTheDocument();
  expect(screen.queryByText(/Stripe|donations are not open/)).not.toBeInTheDocument();
  expect(config).not.toHaveBeenCalled();
  expect((await axe.run(container)).violations).toEqual([]);
  config.mockRestore();
});
