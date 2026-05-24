import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Signup from '../../pages/Signup';
import * as authStore from '../../store/authStore';

// Mock module for navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Signup Component', () => {
  const mockRegister = vi.fn();
  const mockInitializeAuth = vi.fn();
  const mockClearError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    vi.spyOn(authStore, 'useAuthStore').mockReturnValue({
      register: mockRegister,
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
        <Signup />
      </BrowserRouter>
    );
  };

  it('renders sign up form correctly', () => {
    renderComponent();
    expect(screen.getByText('Registration ✨')).toBeInTheDocument();
    
    // Check key fields
    expect(screen.getByPlaceholderText('Username')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('First Name')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Last Name')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign Up/i })).toBeInTheDocument();
  });

  it('validates empty required fields on submit', async () => {
    renderComponent();
    const submitButton = screen.getByRole('button', { name: /Sign Up/i });
    
    fireEvent.submit(submitButton.closest('form'));

    expect(await screen.findByText('Username is required')).toBeInTheDocument();
    expect(await screen.findByText('Email is required')).toBeInTheDocument();
    expect(await screen.findByText('Password is required')).toBeInTheDocument();
    expect(await screen.findByText('Please confirm password')).toBeInTheDocument();
    expect(await screen.findByText('First name is required')).toBeInTheDocument();
    expect(await screen.findByText('Last name is required')).toBeInTheDocument();
    
    expect(mockRegister).not.toHaveBeenCalled();
  });

  it('validates password mismatch', async () => {
    renderComponent();
    
    const passwordInputs = screen.getAllByPlaceholderText('•••••••');
    const pwdInput = passwordInputs[0];
    const confirmPwdInput = passwordInputs[1];
    
    fireEvent.change(pwdInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPwdInput, { target: { value: 'different123' } });
    
    const submitButton = screen.getByRole('button', { name: /Sign Up/i });
    fireEvent.submit(submitButton.closest('form'));

    expect(await screen.findByText('Passwords do not match')).toBeInTheDocument();
    expect(mockRegister).not.toHaveBeenCalled();
  });

  it('calls register on successful validation and navigates', async () => {
    mockRegister.mockResolvedValueOnce({ success: true });
    
    renderComponent();
    
    fireEvent.change(screen.getByPlaceholderText('Username'), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'test@example.com' } });
    
    const passwordInputs = screen.getAllByPlaceholderText('•••••••');
    fireEvent.change(passwordInputs[0], { target: { value: 'password123' } });
    fireEvent.change(passwordInputs[1], { target: { value: 'password123' } });
    
    fireEvent.change(screen.getByPlaceholderText('First Name'), { target: { value: 'First' } });
    fireEvent.change(screen.getByPlaceholderText('Last Name'), { target: { value: 'Last' } });
    
    const submitButton = screen.getByRole('button', { name: /Sign Up/i });
    fireEvent.submit(submitButton.closest('form'));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith(expect.objectContaining({
        username: 'testuser',
        email: 'test@example.com',
        first_name: 'First',
        last_name: 'Last',
        password: 'password123'
      }));
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });
});
