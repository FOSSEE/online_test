import React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Logo from '../../../components/ui/Logo';

describe('Logo Component', () => {
  it('matches the snapshot', () => {
    const { container } = render(
      <BrowserRouter>
        <Logo />
      </BrowserRouter>
    );
    expect(container).toMatchSnapshot();
  });
});
