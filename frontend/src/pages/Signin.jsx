import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FaBook, FaStar, FaCheckCircle, FaGoogle, FaGithub } from 'react-icons/fa';
import { FaEye, FaEyeSlash } from 'react-icons/fa';
import Logo from '../components/ui/Logo';
import { useAuthStore } from '../store/authStore';
import api from '../api/api';

const Signin = () => {
  const navigate = useNavigate();
  const { login, user, isAuthenticated, isLoading, error, initializeAuth, clearError } = useAuthStore();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [formErrors, setFormErrors] = useState({});

  // Initialize auth state on mount
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, user, navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // Clear field-specific error when user starts typing
    if (formErrors[name]) {
      setFormErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const validateForm = () => {
    const errors = {};

    if (!formData.username.trim()) {
      errors.username = 'Username is required';
    }

    if (!formData.password.trim()) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    clearError();

    try {
      const result = await login({
        username: formData.username,
        password: formData.password
      });

      if (result.success) {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  const handleSocialLogin = async (provider) => {
    const providerMap = {
      'Google': 'google-oauth2',
      'GitHub': 'github',
    };
    const backend = providerMap[provider];
    if (!backend) return;

    try {
      const redirectUri = `${window.location.origin}/auth/callback`;
      const response = await api.get('api/auth/social-urls/', {
        params: { provider: backend, redirect_uri: redirectUri },
      });
      window.location.href = response.data.url;
    } catch (err) {
      console.error('Failed to get social auth URL:', err);
    }
  };

  return (
    <div className="min-h-screen h-screen flex overflow-hidden">
      {/* Left side (Brand / Illustration) */}
      <div className="hidden lg:flex flex-col justify-center items-center w-1/2 h-screen bg-gradient-to-br from-[#0e0e14] to-[#1a1a2e] text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-radial from-purple-500/15 via-transparent to-transparent"></div>

        <div className="relative z-10 max-w-md px-6 md:px-10 text-center">
          <div className="w-16 h-16 md:w-20 md:h-20 mx-auto mb-4 md:mb-6 logo-badge rounded-xl md:rounded-2xl flex items-center justify-center">
            <span className="text-2xl md:text-3xl font-bold">Y</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold mb-3 md:mb-4 tracking-tight">
            Welcome to <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">Yaksh</span>
          </h1>
          <p className="soft text-base md:text-lg leading-relaxed">
            Learn, grow, and achieve milestones — all in one platform.
            Unlock badges, complete courses, and showcase your learning journey.
          </p>

          {/* Icons */}
          <div className="mt-8 md:mt-12 flex justify-center gap-4 md:gap-6">
            <div className="w-12 h-12 md:w-16 md:h-16 rounded-lg md:rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 flex items-center justify-center">
              <FaBook className="w-6 h-6 md:w-8 md:h-8 text-indigo-400" />
            </div>
            <div className="w-12 h-12 md:w-16 md:h-16 rounded-lg md:rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 flex items-center justify-center">
              <FaStar className="w-6 h-6 md:w-8 md:h-8 text-purple-400" />
            </div>
            <div className="w-12 h-12 md:w-16 md:h-16 rounded-lg md:rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 flex items-center justify-center">
              <FaCheckCircle className="w-6 h-6 md:w-8 md:h-8 text-pink-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Right side (Login Form) */}
      <div className="flex flex-col w-full lg:w-1/2 bg-gradient-to-b from-[var(--bg-primary)] to-[var(--bg-secondary)] px-4 sm:px-6 md:px-8 lg:px-16 overflow-y-auto h-screen relative grid-texture">
        <div className="w-full max-w-md mx-auto space-y-4 sm:space-y-6 py-6 sm:py-8 md:py-10">
          {/* Mobile Logo */}
          <div className="lg:hidden flex justify-center mb-4">
            <div className="w-14 h-14 logo-badge rounded-xl flex items-center justify-center">
              <span className="text-2xl font-bold">Y</span>
            </div>
          </div>

          {/* Header */}
          <div className="text-center lg:text-left">
            <h2 className="text-2xl sm:text-3xl font-bold text-[var(--text-primary)] mb-1 sm:mb-2">Welcome Back 👋</h2>
            <p className="text-[var(--text-muted)] text-xs sm:text-sm">Sign in to continue your learning journey</p>
          </div>

          {/* Alert */}
          {error && (
            <div className="bg-red-500/20 border border-red-500/50 text-red-600 dark:text-red-200 px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg">
              <p className="text-xs sm:text-sm">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5">
            {/* Username Field */}
            <div>
              <label htmlFor="username" className="block text-xs sm:text-sm font-medium text-[var(--text-secondary)] mb-1.5 sm:mb-2">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-2.5 sm:pl-3 flex items-center pointer-events-none">
                  <FaBook className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400 dark:text-gray-500" />
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  value={formData.username}
                  onChange={handleChange}
                  className={`w-full pl-9 sm:pl-10 pr-3 sm:pr-4 py-2.5 sm:py-3 bg-[var(--input-bg)] border ${formErrors.username ? 'border-red-500' : 'border-[var(--border-color)]'
                    } text-[var(--text-primary)] rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-gray-400 dark:placeholder-gray-500 text-sm sm:text-base`}
                  placeholder="Enter your username"
                  required
                  disabled={isLoading}
                />
              </div>
              {formErrors.username && (
                <p className="text-red-500 text-xs mt-1">{formErrors.username}</p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-xs sm:text-sm font-medium text-[var(--text-secondary)] mb-1.5 sm:mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-2.5 sm:pl-3 flex items-center pointer-events-none">
                  <FaEye className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400 dark:text-gray-500" />
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={handleChange}
                  className={`w-full pl-9 sm:pl-10 pr-10 sm:pr-12 py-2.5 sm:py-3 bg-[var(--input-bg)] border ${formErrors.password ? 'border-red-500' : 'border-[var(--border-color)]'
                    } text-[var(--text-primary)] rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-gray-400 dark:placeholder-gray-500 text-sm sm:text-base`}
                  placeholder="Enter your password"
                  required
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-2.5 sm:pr-3 flex items-center"
                  disabled={isLoading}
                >
                  {showPassword ? (
                    <FaEyeSlash className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300" />
                  ) : (
                    <FaEye className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300" />
                  )}
                </button>
              </div>
              {formErrors.password && (
                <p className="text-red-500 text-xs mt-1">{formErrors.password}</p>
              )}
              <div className="text-right mt-1.5 sm:mt-2">
                <Link to="/forgot-password" className="text-xs sm:text-sm text-indigo-500 hover:text-indigo-600 dark:text-indigo-400 dark:hover:text-indigo-300 transition">
                  Forgot password?
                </Link>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 sm:py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm sm:text-base"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center my-4 sm:my-6">
            <div className="flex-grow h-px bg-[var(--border-color)]"></div>
            <span className="mx-3 sm:mx-4 text-xs sm:text-sm text-[var(--text-muted)]">or continue with</span>
            <div className="flex-grow h-px bg-[var(--border-color)]"></div>
          </div>

          {/* Social Buttons */}
          <div className="flex justify-center gap-2 sm:gap-3">
            <button
              type="button"
              onClick={() => handleSocialLogin('Google')}
              className="social-btn flex items-center justify-center rounded-lg sm:rounded-xl p-2.5 sm:p-3 w-12 h-12 sm:w-14 sm:h-14 bg-[var(--input-bg)] hover:bg-[var(--surface-2)] border border-[var(--border-color)] transition"
              disabled={isLoading}
            >
              <FaGoogle className="w-5 h-5 sm:w-6 sm:h-6 text-red-500" />
            </button>
            <button
              type="button"
              onClick={() => handleSocialLogin('GitHub')}
              className="social-btn flex items-center justify-center rounded-lg sm:rounded-xl p-2.5 sm:p-3 w-12 h-12 sm:w-14 sm:h-14 bg-[var(--input-bg)] hover:bg-[var(--surface-2)] border border-[var(--border-color)] transition"
              disabled={isLoading}
            >
              <FaGithub className="w-5 h-5 sm:w-6 sm:h-6 text-[var(--text-primary)]" />
            </button>
          </div>

          {/* Sign Up Link */}
          <p className="text-center text-xs sm:text-sm text-[var(--text-muted)] mt-4 sm:mt-6">
            Don't have an account?{' '}
            <Link to="/signup" className="text-indigo-500 hover:text-indigo-600 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium transition">
              Sign Up
            </Link>
          </p>

          {/* Footer */}
          <div className="text-center text-xs text-[var(--text-muted)] pt-6 sm:pt-8">
            © 2025 Yaksh. Developed by FOSSEE group, IIT Bombay
          </div>
        </div>
      </div>
    </div>
  );
};

export default Signin;