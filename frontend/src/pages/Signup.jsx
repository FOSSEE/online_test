import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FaBook, FaStar, FaCheckCircle } from 'react-icons/fa';
import { FaGoogle, FaGithub } from 'react-icons/fa';
import Logo from '../components/ui/Logo';
import { useAuthStore } from '../store/authStore';
import api from '../api/api';

const Signup = () => {
  const navigate = useNavigate();
  const { register, user, isAuthenticated, isLoading, error, initializeAuth, clearError } = useAuthStore();

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    roll_number: '',
    institute: '',
    department: '',
    position: '',
    timezone: 'Asia/Kolkata',
  });

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
    } else if (formData.username.length < 3) {
      errors.username = 'Username must be at least 3 characters';
    }

    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }

    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Please confirm password';
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    if (!formData.first_name.trim()) {
      errors.first_name = 'First name is required';
    }

    if (!formData.last_name.trim()) {
      errors.last_name = 'Last name is required';
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

    const userData = {
      username: formData.username,
      email: formData.email,
      password: formData.password,
      first_name: formData.first_name,
      last_name: formData.last_name,
      roll_number: formData.roll_number,
      institute: formData.institute,
      department: formData.department,
      position: formData.position,
      timezone: formData.timezone
    };

    try {
      const result = await register(userData);

      if (result.success) {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Registration error:', error);
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

  const handleBackToLogin = () => {
    navigate('/signin');
  };

  return (
    <div className="min-h-screen h-screen flex overflow-hidden">
      {/* LEFT: Fixed Background Section */}
      <div className="hidden lg:flex flex-col justify-center items-center w-1/2 h-screen bg-gradient-to-br from-[#0e0e14] to-[#1a1a2e] text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-radial from-purple-500/15 via-transparent to-transparent"></div>

        <div className="relative z-10 max-w-md px-10 text-center">
          <div className="w-20 h-20 mx-auto mb-6 logo-badge rounded-2xl flex items-center justify-center">
            <span className="text-3xl font-bold">Y</span>
          </div>
          <h1 className="text-4xl font-extrabold mb-4 tracking-tight">
            Welcome to <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">Yaksh</span>
          </h1>
          <p className="soft text-lg leading-relaxed">
            Learn, grow, and achieve milestones — all in one platform.
            Unlock badges, complete courses, and showcase your learning journey.
          </p>

          {/* Icons */}
          <div className="mt-12 flex justify-center gap-6">
            <div className="w-16 h-16 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 flex items-center justify-center">
              <FaBook className="w-8 h-8 text-indigo-400" />
            </div>
            <div className="w-16 h-16 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 flex items-center justify-center">
              <FaStar className="w-8 h-8 text-purple-400" />
            </div>
            <div className="w-16 h-16 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 flex items-center justify-center">
              <FaCheckCircle className="w-8 h-8 text-pink-400" />
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT: Scrollable Form Section */}
      <div className="flex flex-col w-full lg:w-1/2 bg-gradient-to-b from-[var(--bg-primary)] to-[var(--bg-secondary)] px-8 sm:px-16 pt-4 lg:pt-12 relative grid-texture overflow-y-auto h-screen">
        <div className="w-full max-w-md mx-auto space-y-6 pb-10">
          {/* Header */}
          <div className="flex items-center mb-4">
            <Logo />
            <button
              onClick={handleBackToLogin}
              className="ml-auto text-sm text-indigo-400 hover:text-indigo-300 transition"
            >
              Back to Login
            </button>
          </div>

          <div>
            <h2 className="text-3xl font-bold text-[var(--text-primary)]">Registration ✨</h2>
            <p className="text-[var(--text-muted)] text-sm mt-2">Please fill in the following details:</p>
          </div>

          {/* Alert */}
          {error && (
            <div className="bg-red-500/20 border border-red-500/50 text-red-200 px-4 py-3 rounded-lg">
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Registration Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">Username</label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                className={`w-full px-4 py-2.5 border ${formErrors.username ? 'border-red-500' : 'border-[var(--border-color)]'} rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:text-sm`}
                placeholder="Username"
                required
                disabled={isLoading}
              />
              {formErrors.username && (
                <p className="text-red-500 text-xs mt-1">{formErrors.username}</p>
              )}
              <p className="text-xs text-[var(--text-muted)] mt-1">Letters, digits, period and underscores only.</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`w-full px-4 py-2.5 border ${formErrors.email ? 'border-red-500' : 'border-[var(--border-color)]'} rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:text-sm`}
                placeholder="you@example.com"
                required
                disabled={isLoading}
              />
              {formErrors.email && (
                <p className="text-red-500 text-xs mt-1">{formErrors.email}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">Password</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={`w-full px-4 py-2.5 border ${formErrors.password ? 'border-red-500' : 'border-[var(--border-color)]'} rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:text-sm`}
                placeholder="•••••••"
                required
                disabled={isLoading}
              />
              {formErrors.password && (
                <p className="text-red-500 text-xs mt-1">{formErrors.password}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">Confirm Password</label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className={`w-full px-4 py-2.5 border ${formErrors.confirmPassword ? 'border-red-500' : 'border-[var(--border-color)]'} rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:text-sm`}
                placeholder="•••••••"
                required
                disabled={isLoading}
              />
              {formErrors.confirmPassword && (
                <p className="text-red-500 text-xs mt-1">{formErrors.confirmPassword}</p>
              )}
            </div>

            <div className="flex gap-3">
              <div className="w-1/2">
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">First Name</label>
                <input
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  className={`w-full px-4 py-2.5 border ${formErrors.first_name ? 'border-red-500' : 'border-[var(--border-color)]'} rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:text-sm`}
                  placeholder="First Name"
                  required
                  disabled={isLoading}
                />
                {formErrors.first_name && (
                  <p className="text-red-500 text-xs mt-1">{formErrors.first_name}</p>
                )}
              </div>
              <div className="w-1/2">
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">Last Name</label>
                <input
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  className={`w-full px-4 py-2.5 border ${formErrors.last_name ? 'border-red-500' : 'border-[var(--border-color)]'} rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:text-sm`}
                  placeholder="Last Name"
                  required
                  disabled={isLoading}
                />
                {formErrors.last_name && (
                  <p className="text-red-500 text-xs mt-1">{formErrors.last_name}</p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">Roll Number</label>
              <input
                type="text"
                name="roll_number"
                value={formData.roll_number}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:text-sm"
                placeholder="Use a dummy if you don't have one"
                disabled={isLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">Institute/Organization</label>
              <input
                type="text"
                name="institute"
                value={formData.institute}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:text-sm"
                placeholder="Institute or Organization"
                disabled={isLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">Department</label>
              <input
                type="text"
                name="department"
                value={formData.department}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:text-sm"
                placeholder="Department you work/study at"
                disabled={isLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">Position</label>
              <input
                type="text"
                name="position"
                value={formData.position}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:text-sm"
                placeholder="Student / Faculty / Researcher / Industry / etc."
                disabled={isLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">Timezone</label>
              <select
                name="timezone"
                value={formData.timezone}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:text-sm"
                disabled={isLoading}
              >
                <option>Asia/Kolkata</option>
                <option>Asia/Dubai</option>
                <option>Europe/London</option>
                <option>America/New_York</option>
                <option>UTC</option>
              </select>
              <p className="text-xs text-[var(--text-muted)] mt-1">All timings are shown based on the selected timezone.</p>
            </div>

            <div className="flex justify-center gap-3 pt-4">
              <button
                type="submit"
                disabled={isLoading}
                className="flex-1 bg-indigo-600 text-white font-semibold py-3 rounded-xl hover:bg-indigo-700 transition px-8"
              >
                {isLoading ? 'Creating Account...' : 'Sign Up'}
              </button>
              <button
                type="button"
                onClick={handleBackToLogin}
                className="flex-1 bg-gray-600 text-white font-semibold py-3 rounded-xl hover:bg-gray-700 transition px-8"
              >
                Cancel
              </button>
            </div>
          </form>

          <div className="flex items-center my-6">
            <div className="flex-grow h-px bg-[var(--border-color)]"></div>
            <span className="mx-4 text-sm text-[var(--text-muted)]">or continue with</span>
            <div className="flex-grow h-px bg-[var(--border-color)]"></div>
          </div>

          <div className="flex justify-center gap-3">
            <button
              type="button"
              onClick={() => handleSocialLogin('Google')}
              className="social-btn flex items-center justify-center rounded-xl p-3 w-14 h-14 bg-[var(--input-bg)] hover:bg-[var(--surface-2)] border border-[var(--border-color)] transition"
              disabled={isLoading}
            >
              <FaGoogle className="w-6 h-6 text-red-500" />
            </button>
            <button
              type="button"
              onClick={() => handleSocialLogin('GitHub')}
              className="social-btn flex items-center justify-center rounded-xl p-3 w-14 h-14 bg-[var(--input-bg)] hover:bg-[var(--surface-2)] border border-[var(--border-color)] transition"
              disabled={isLoading}
            >
              <FaGithub className="w-6 h-6 text-[var(--text-primary)]" />
            </button>

          </div>

          <p className="text-center text-sm text-[var(--text-muted)] mt-6">
            Already have an account?
            <Link to="/signin" className="text-indigo-400 font-medium hover:text-indigo-300 transition ml-1">
              Sign In
            </Link>
          </p>

          {/* Footer */}
          <div className="text-center text-xs text-[var(--text-muted)] pt-8 pb-4">
            © 2025 Yaksh. Developed by FOSSEE group, IIT Bombay
          </div>
        </div>
      </div>
    </div>
  );
};

export default Signup;
