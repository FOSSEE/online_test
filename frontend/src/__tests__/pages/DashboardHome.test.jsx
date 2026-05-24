import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import DashboardHome from '../../pages/DashboardHome';
import * as authStore from '../../store/authStore';
import * as api from '../../api/api';

// Mock components to prevent deep rendering
vi.mock('../../pages/student/Dashboard', () => ({
  default: () => <div data-testid="student-dashboard">Student Dashboard</div>,
}));

// Mock react-router-dom Navigate
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    Navigate: ({ to }) => <div data-testid={`navigate-to-${to.replace(/\//g, '')}`}>Redirecting to {to}</div>,
  };
});

// Mock api
vi.mock('../../api/api', () => ({
  getModeratorStatus: vi.fn(),
}));

describe('DashboardHome Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderComponent = () => {
    render(
      <BrowserRouter>
        <DashboardHome />
      </BrowserRouter>
    );
  };

  it('renders student dashboard for regular users', async () => {
    vi.spyOn(authStore, 'useAuthStore').mockReturnValue({
      user: { id: 1, is_moderator: false },
    });

    renderComponent();

    // Since is_moderator is false, getModeratorStatus is not called
    expect(api.getModeratorStatus).not.toHaveBeenCalled();
    
    await waitFor(() => {
      expect(screen.getByTestId('student-dashboard')).toBeInTheDocument();
    });
  });

  it('redirects to teacher dashboard if user is active moderator', async () => {
    vi.spyOn(authStore, 'useAuthStore').mockReturnValue({
      user: { id: 2, is_moderator: true },
    });

    api.getModeratorStatus.mockResolvedValueOnce({ is_moderator_active: true });

    renderComponent();

    expect(screen.getByText('Loading...')).toBeInTheDocument();

    await waitFor(() => {
      expect(api.getModeratorStatus).toHaveBeenCalled();
      expect(screen.getByTestId('navigate-to-teacherdashboard')).toBeInTheDocument();
    });
  });

  it('renders student dashboard if moderator is inactive', async () => {
    vi.spyOn(authStore, 'useAuthStore').mockReturnValue({
      user: { id: 2, is_moderator: true },
    });

    api.getModeratorStatus.mockResolvedValueOnce({ is_moderator_active: false });

    // Mock window location
    delete window.location;
    window.location = { pathname: '/dashboard', href: '' };

    renderComponent();

    await waitFor(() => {
      expect(api.getModeratorStatus).toHaveBeenCalled();
      expect(screen.getByTestId('student-dashboard')).toBeInTheDocument();
    });
  });
});
