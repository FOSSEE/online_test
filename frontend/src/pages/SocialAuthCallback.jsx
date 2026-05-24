import React, { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import api from '../api/api';

const SocialAuthCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState(null);
  const { isAuthenticated } = useAuthStore();
  const hasStarted = useRef(false);

  useEffect(() => {
    // If already authenticated (e.g. user navigates back here), redirect
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
      return;
    }

    // Prevent double execution in React StrictMode (dev mode mounts twice)
    // OAuth codes are single-use, so the second call would always fail
    if (hasStarted.current) return;
    hasStarted.current = true;

    const code = searchParams.get('code');
    const state = searchParams.get('state'); // 'google-oauth2' or 'github'

    if (!code || !state) {
      setError('Missing authorization code. Please try logging in again.');
      return;
    }

    const handleCallback = async () => {
      try {
        const response = await api.post('api/auth/social-login/', {
          provider: state,
          code: code,
          redirect_uri: `${window.location.origin}/auth/callback`,
        });

        const { user, token } = response.data;

        // Store token and user data (same as regular login)
        localStorage.setItem('authToken', token);
        localStorage.setItem('user', JSON.stringify(user));

        // Update Zustand store
        useAuthStore.setState({
          user,
          token,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });

        navigate('/dashboard', { replace: true });
      } catch (err) {
        // If auth succeeded from a prior call (StrictMode race), just redirect
        if (useAuthStore.getState().isAuthenticated) {
          navigate('/dashboard', { replace: true });
          return;
        }
        const message =
          err.response?.data?.error || 'Social login failed. Please try again.';
        setError(message);
      }
    };

    handleCallback();
  }, [searchParams, navigate, isAuthenticated]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-[var(--bg-1)] to-[var(--bg-2)]">
        <div className="max-w-md w-full mx-4 p-6 rounded-xl bg-[var(--input-bg)] border border-[var(--border-color)]">
          <h2 className="text-xl font-bold text-red-500 mb-3">Login Failed</h2>
          <p className="text-[var(--text-secondary)] text-sm mb-5">{error}</p>
          <button
            onClick={() => navigate('/signin')}
            className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition"
          >
            Back to Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-[var(--bg-1)] to-[var(--bg-2)]">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-[var(--text-secondary)] text-sm">Completing sign in...</p>
      </div>
    </div>
  );
};

export default SocialAuthCallback;

