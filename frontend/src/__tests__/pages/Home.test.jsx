import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Home from '../../pages/Home';

describe('Home Component', () => {
  const renderComponent = () => {
    return render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    );
  };

  it('renders hero section correctly', () => {
    renderComponent();
    expect(screen.getByText('Learn Smarter,')).toBeInTheDocument();
    expect(screen.getByText('Grow Faster')).toBeInTheDocument();
    expect(screen.getByText('Welcome to Interactive Learning')).toBeInTheDocument();
  });

  it('renders call to action buttons', () => {
    renderComponent();
    const exploreButtons = screen.getAllByRole('link', { name: /Explore Courses/i });
    expect(exploreButtons.length).toBeGreaterThan(0);
    
    // Check signup CTA
    expect(screen.getByRole('link', { name: /Start Learning Now/i })).toBeInTheDocument();
  });

  it('renders features section', () => {
    renderComponent();
    expect(screen.getByText('Interactive Coding')).toBeInTheDocument();
    expect(screen.getByText('Gamified Learning')).toBeInTheDocument();
    expect(screen.getByText('Progress Tracking')).toBeInTheDocument();
  });

  it('renders footer', () => {
    renderComponent();
    expect(screen.getAllByText('Yaksh').length).toBeGreaterThan(0);
    expect(screen.getByText(/Developed by FOSSEE group, IIT Bombay/i)).toBeInTheDocument();
  });
});
