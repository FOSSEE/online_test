import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Signin from '../../pages/Signin';
import * as authStore from '../../store/authStore';
import api from '../../api/api';

// Mock module for navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    Link: ({ children, to }) => <a href={to}>{children}</a>,
  };
});

// Mock api
vi.mock('../../api/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Signin Component', () => {
  const mockLogin = vi.fn();
  const mockInitializeAuth = vi.fn();
  const mockClearError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Spy on the hook
    vi.spyOn(authStore, 'useAuthStore').mockReturnValue({
      login: mockLogin,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      initializeAuth: mockInitializeAuth,
      clearError: mockClearError,
    });
  });

  const renderComponent = () => {
    render(
      <BrowserRouter>
        <Signin />
      </BrowserRouter>
    );
  };

  it('renders sign in form correctly', () => {
    renderComponent();
    expect(screen.getByText('Welcome Back 👋')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your username')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
  });

  it('validates empty fields on submit', async () => {
    renderComponent();
    const submitButton = screen.getByRole('button', { name: /Sign In/i });
    
    fireEvent.submit(submitButton.closest('form'));

    expect(await screen.findByText('Username is required')).toBeInTheDocument();
    expect(await screen.findByText('Password is required')).toBeInTheDocument();
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('validates password length', async () => {
    renderComponent();
    
    const usernameInput = screen.getByPlaceholderText('Enter your username');
    const passwordInput = screen.getByPlaceholderText('Enter your password');
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: '123' } }); // < 6 chars
    
    const submitButton = screen.getByRole('button', { name: /Sign In/i });
    fireEvent.click(submitButton);

    expect(await screen.findByText('Password must be at least 6 characters')).toBeInTheDocument();
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('calls login on successful validation and navigates', async () => {
    mockLogin.mockResolvedValueOnce({ success: true });
    
    renderComponent();
    
    const usernameInput = screen.getByPlaceholderText('Enter your username');
    const passwordInput = screen.getByPlaceholderText('Enter your password');
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    
    const submitButton = screen.getByRole('button', { name: /Sign In/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123'
      });
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('redirects if already authenticated', () => {
    vi.spyOn(authStore, 'useAuthStore').mockReturnValue({
      login: mockLogin,
      user: { username: 'testuser' },
      isAuthenticated: true,
      isLoading: false,
      error: null,
      initializeAuth: mockInitializeAuth,
      clearError: mockClearError,
    });

    renderComponent();
    
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  it('calls social api when social login clicked', async () => {
    api.get.mockResolvedValueOnce({ data: { url: 'http://social-login.com' } });
    
    // Polyfill window.location mapping since we cannot easily reassign it in jsdom directly without Object.defineProperty
    delete window.location;
    window.location = { href: '', origin: 'http://localhost' };
    
    renderComponent();

    // social btns are typically identified by svg or icons, we can find them by parent container or mock roles.
    // they don't have aria-labels, so we grab the first button in the social section
    const socialButtons = screen.getAllByRole('button').filter(btn => btn.className.includes('social-btn'));
    fireEvent.click(socialButtons[0]); // Google btn

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('api/auth/social-urls/', {
        params: { provider: 'google-oauth2', redirect_uri: 'http://localhost/auth/callback' }
      });
      expect(window.location.href).toBe('http://social-login.com');
    });
  });
});
