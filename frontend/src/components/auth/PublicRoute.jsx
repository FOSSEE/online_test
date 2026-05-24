import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

/**
 * PublicRoute - renders public pages (like the landing page) only when
 * the user is NOT authenticated.
 *
 * If the user IS authenticated:
 *   - Teachers (is_moderator === true)  → /teacher/dashboard
 *   - Students                          → /dashboard
 */
const PublicRoute = () => {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Outlet />;
  }

  // Redirect authenticated users to the correct dashboard
  const redirectTo = user?.is_moderator ? '/teacher/dashboard' : '/dashboard';
  return <Navigate to={redirectTo} replace />;
};

export default PublicRoute;
