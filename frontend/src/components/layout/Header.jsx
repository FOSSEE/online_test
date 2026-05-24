import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  FaBell,
  FaUser,
  FaSun,
  FaMoon,
  FaCog,
  FaSignOutAlt,
  FaBars,
  FaTimes,
  FaChevronDown,
  FaCheck,
  FaCheckDouble,
  FaArrowRight,
  FaClock,
  FaSync
} from 'react-icons/fa';
import Logo from '../ui/Logo';
import { useStore } from '../../store/useStore';
import { useAuthStore } from '../../store/authStore';
import { useNotificationsStore } from '../../store/notificationsStore';
import { toggleModeratorRole, getModeratorStatus } from '../../api/api';

const Header = ({ isAuth = false, isLanding = false }) => {
  const { theme, toggleTheme } = useStore();
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuthStore((state) => state.logout);
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);

  // Notifications store
  const {
    notifications,
    unreadCount,
    isLoading,
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead
  } = useNotificationsStore();

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [isModeratorActive, setIsModeratorActive] = useState(null);

  const dropdownRef = useRef(null);
  const notificationRef = useRef(null);
  const mobileMenuRef = useRef(null);

  // Fetch notifications on mount and periodically
  useEffect(() => {
    if (isAuth && user) {
      fetchNotifications();
      fetchUnreadCount();

      // Poll for new notifications every 30 seconds
      const interval = setInterval(() => {
        fetchUnreadCount();
      }, 30000);

      return () => clearInterval(interval);
    }
  }, [isAuth, user]);

  const handleSignOut = async () => {
    const result = await logout();
    setIsDropdownOpen(false);
    setIsMobileMenuOpen(false);
    if (result?.success) {
      navigate('/signin', { replace: true });
    }
    // If logout failed, user stays on current page — error is in authStore
  };

  const handleNotificationClick = async (notification) => {
    if (!notification.read) {
      await markAsRead(notification.message_uid);
    }
  };

  const handleMarkAllAsRead = async () => {
    await markAllAsRead();
  };

  const handleToggleModerator = async () => {
    try {
      const response = await toggleModeratorRole();
      if (response.success) {
        setIsModeratorActive(response.is_moderator_active);
        setIsDropdownOpen(false);

        // Check if currently on a teacher route
        const isOnTeacherRoute = location.pathname.startsWith('/teacher');

        // Redirect immediately based on new mode (like old Django version did)
        if (response.is_moderator_active) {
          // Switched to teacher mode - redirect to teacher dashboard
          window.location.href = '/teacher/dashboard';
        } else {
          // Switched to student mode - redirect to student dashboard (like old Django redirects to /exam/)
          window.location.href = '/dashboard';
        }
      }
    } catch (error) {
      console.error('Failed to toggle moderator role:', error);
      // Could show a toast notification here
    }
  };
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setIsNotificationOpen(false);
      }
      if (mobileMenuRef.current && !mobileMenuRef.current.contains(event.target)) {
        setIsMobileMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close mobile menu on window resize
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) {
        setIsMobileMenuOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Fetch moderator status on mount and when user changes
  useEffect(() => {
    const fetchModeratorStatus = async () => {
      if (user?.is_moderator && isAuth) {
        try {
          const status = await getModeratorStatus();
          setIsModeratorActive(status.is_moderator_active);
        } catch (error) {
          console.error('Failed to fetch moderator status:', error);
          // Default to false if we can't fetch status
          setIsModeratorActive(false);
        }
      } else {
        setIsModeratorActive(false);
      }
    };

    fetchModeratorStatus();
  }, [user, isAuth]);

  const ThemeToggle = () => (
    <button
      onClick={toggleTheme}
      className="p-2 sm:p-2.5 rounded-xl hover:bg-white/5 active:scale-95 transition-all duration-200"
      aria-label="Toggle theme"
    >
      {theme === 'dark' ? (
        <FaSun className="w-5 h-5 sm:w-5 sm:h-5 text-amber-400" />
      ) : (
        <FaMoon className="w-5 h-5 sm:w-5 sm:h-5 text-indigo-500" />
      )}
    </button>
  );

  if (isLanding) {
    return (
      <header className="sticky top-0 z-50 bg-[var(--header-bg)] backdrop-blur-xl border-b-2 border-[var(--border-strong)] shadow-[var(--shadow-medium)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 md:h-20">
            {/* Logo */}
            <div className="flex-shrink-0">
              <Logo size="md" />
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-2 lg:gap-4">
              <ThemeToggle />
              <Link
                to="/signin"
                className="px-4 lg:px-5 py-2 text-sm lg:text-base text-[var(--text-secondary)] hover:text-[var(--text-primary)] font-medium transition-colors rounded-lg hover:bg-white/5"
              >
                Sign In
              </Link>
              <Link
                to="/signup"
                className="btn-grad px-5 lg:px-6 py-2 lg:py-2.5 text-sm lg:text-base text-white rounded-xl font-semibold hover:brightness-110 active:scale-95 transition-all duration-200 shadow-lg shadow-purple-500/25"
              >
                Get Started
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <div className="md:hidden flex items-center gap-2">
              <ThemeToggle />
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/5 transition-colors"
                aria-label="Toggle menu"
              >
                {isMobileMenuOpen ? <FaTimes className="w-6 h-6" /> : <FaBars className="w-6 h-6" />}
              </button>
            </div>
          </div>

          {/* Mobile Menu */}
          {isMobileMenuOpen && (
            <div
              ref={mobileMenuRef}
              className="md:hidden py-4 border-t border-[var(--border-color)] animate-in slide-in-from-top duration-200"
            >
              <div className="flex flex-col gap-2">
                <Link
                  to="/signin"
                  className="px-4 py-3 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/5 rounded-lg font-medium transition-colors"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  Sign In
                </Link>
                <Link
                  to="/signup"
                  className="btn-grad px-4 py-3 text-white rounded-xl font-semibold text-center shadow-lg shadow-purple-500/25"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  Get Started
                </Link>
              </div>
            </div>
          )}
        </div>
      </header>
    );
  }

  if (isAuth) {
    return (
      <header className="sticky top-0 z-50 border-b border-white/10 bg-[var(--header-bg)]  shadow-[var(--shadow-header)]">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center gap-2 sm:gap-3 h-16 md:h-20">

            {/* Left: Mobile Logo */}
            <div className="flex items-center gap-2 md:hidden">
              <Logo size="sm" showText={false} />
            </div>

            {/* Right Side Actions */}
            <div className="flex items-center gap-2 sm:gap-3 ml-auto">

              {/* Theme Toggle - Always visible */}
              <ThemeToggle />

              {/* Notifications */}
              <div className="relative" ref={notificationRef}>
                <button
                  onClick={() => {
                    setIsNotificationOpen(!isNotificationOpen);
                    if (!isNotificationOpen) {
                      fetchNotifications();
                    }
                  }}
                  className="relative p-2 sm:p-2.5 rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-2)] active:scale-95 transition-all duration-200"
                  aria-label="Notifications"
                >
                  <FaBell className="w-5 h-5 sm:w-6 sm:h-6" />
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center shadow-md animate-pulse border-2 border-[var(--bg-secondary)]">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </button>

                {/* Notifications Dropdown */}
                {isNotificationOpen && (
                  <>
                    {/* Mobile Overlay */}
                    <div
                      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden transition-opacity"
                      onClick={() => setIsNotificationOpen(false)}
                    />

                    {/* Dropdown Panel */}
                    <div className="fixed md:absolute inset-x-4 top-20 md:inset-x-auto md:right-0 md:top-auto md:mt-2 w-auto md:w-80 lg:w-[26rem] max-w-md mx-auto md:mx-0 card-strong border-2 border-[var(--border-strong)] rounded-2xl shadow-2xl overflow-hidden z-50 animate-in slide-in-from-top-2 md:slide-in-from-top-1 duration-200">

                      {/* Header */}
                      <div className="px-4 py-4 border-b-2 border-[var(--border-subtle)] bg-[var(--surface-2)] flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-blue-500/10 border-2 border-blue-500/30 rounded-xl flex-shrink-0">
                            <FaBell className="w-4 h-4 text-blue-400 group-hover:scale-110 transition-transform" />
                          </div>
                          <div>
                            <h3 className="font-bold text-[var(--text-primary)] text-sm sm:text-base">
                              Notifications
                            </h3>
                            {unreadCount > 0 && (
                              <p className="text-xs font-medium text-[var(--text-secondary)] mt-0.5">
                                {unreadCount} unread
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {notifications.length > 0 && unreadCount > 0 && (
                            <button
                              onClick={handleMarkAllAsRead}
                              className="group flex items-center gap-1.5 px-3 py-1.5 text-xs text-blue-400 dark:text-blue-400 font-bold transition-all hover:bg-blue-500/10 rounded-lg"
                            >
                              <FaCheckDouble className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
                              <span className="hidden sm:inline">Mark all</span>
                            </button>
                          )}
                          {/* Close button for mobile */}
                          <button
                            onClick={() => setIsNotificationOpen(false)}
                            className="md:hidden p-2 hover:bg-[var(--input-bg)] rounded-xl transition-colors"
                          >
                            <FaTimes className="w-4 h-4 text-[var(--text-secondary)]" />
                          </button>
                        </div>
                      </div>

                      {/* Notifications List */}
                      <div className="max-h-[60vh] md:max-h-[28rem] overflow-y-auto custom-scrollbar bg-[var(--surface)]">
                        {isLoading ? (
                          <div className="px-4 py-12 text-center">
                            <div className="inline-block w-10 h-10 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin mb-3"></div>
                            <p className="text-sm font-medium text-[var(--text-secondary)]">Loading notifications...</p>
                          </div>
                        ) : notifications.length === 0 ? (
                          <div className="px-4 py-12 text-center">
                            <div className="w-16 h-16 mx-auto mb-4 bg-[var(--surface-2)] border-2 border-[var(--border-subtle)] rounded-2xl flex items-center justify-center">
                              <FaBell className="w-8 h-8 text-[var(--text-muted)] opacity-50" />
                            </div>
                            <p className="text-sm font-bold text-[var(--text-primary)] mb-1">All caught up!</p>
                            <p className="text-xs font-medium text-[var(--text-secondary)]">No new notifications</p>
                          </div>
                        ) : (
                          <div className="divide-y-2 divide-[var(--border-subtle)]">
                            {notifications.map((notif, index) => (
                              <div
                                key={notif.message_uid}
                                onClick={() => handleNotificationClick(notif)}
                                className={`group relative px-4 py-4 hover:bg-[var(--surface-2)] active:bg-[var(--input-bg)] transition-colors cursor-pointer ${!notif.read
                                  ? 'bg-purple-500/5'
                                  : 'opacity-80 hover:opacity-100'
                                  }`}
                              >


                                <div className="flex items-start gap-3">
                                  {/* Avatar/Icon */}
                                  <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center border-2 shadow-sm ${notif.message_type === 'success' ? 'bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20' :
                                    notif.message_type === 'warning' ? 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/20' :
                                      notif.message_type === 'danger' ? 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20' :
                                        'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20'
                                    }`}>
                                    {notif.sender_name ? (
                                      <span className="text-sm font-bold">
                                        {notif.sender_name.charAt(0).toUpperCase()}
                                      </span>
                                    ) : (
                                      <FaBell className="w-4 h-4" />
                                    )}
                                  </div>

                                  {/* Content */}
                                  <div className="flex-1 min-w-0 pt-0.5">
                                    <div className="flex items-start justify-between gap-2 mb-1">
                                      <p className={`text-sm line-clamp-2 transition-colors ${notif.read ? 'text-[var(--text-secondary)] font-medium' : 'text-[var(--text-primary)] font-bold group-hover:text-purple-600 dark:group-hover:text-purple-400'}`}>
                                        {notif.summary}
                                      </p>
                                      {!notif.read && (
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            markAsRead(notif.message_uid);
                                          }}
                                          className="md:opacity-0 md:group-hover:opacity-100 p-1.5 rounded-lg hover:bg-purple-500/10 text-[var(--text-tertiary)] hover:text-purple-500 transition-all flex-shrink-0"
                                          title="Mark as read"
                                        >
                                          <FaCheck className="w-3.5 h-3.5" />
                                        </button>
                                      )}
                                    </div>

                                    {notif.description && (
                                      <div
                                        className="text-xs text-[var(--text-secondary)] mb-2.5 line-clamp-2 leading-relaxed"
                                        dangerouslySetInnerHTML={{ __html: notif.description }}
                                      />
                                    )}

                                    {/* Meta info */}
                                    <div className="flex items-center gap-2 flex-wrap">
                                      {notif.sender_name && (
                                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[var(--text-secondary)] px-2 py-0.5 rounded-md">
                                          <FaUser className="w-2.5 h-2.5 opacity-70" />
                                          <span className="truncate max-w-[100px] sm:max-w-none">{notif.sender_name}</span>
                                        </span>
                                      )}
                                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[var(--text-muted)]">
                                        <FaClock className="w-2.5 h-2.5 opacity-70" />
                                        {notif.time_since} ago
                                      </span>

                                    </div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Footer */}
                      {notifications.length > 0 && (
                        <div className="px-4 py-3 border-t-2 border-[var(--border-subtle)] bg-[var(--surface-2)]">
                          <button
                            onClick={() => {
                              setIsNotificationOpen(false);
                              navigate('/notifications');
                            }}
                            className="w-full py-2.5 text-sm text-[var(--text-primary)] hover:text-purple-600 dark:hover:text-purple-400 font-bold transition-all hover:bg-[var(--input-bg)] border border-transparent hover:border-[var(--border-subtle)] rounded-xl flex items-center justify-center gap-2 group shadow-sm"
                          >
                            <span>View All Notifications</span>
                            <FaArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                          </button>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>

              {/* User Menu */}
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className="flex items-center gap-2 p-1.5 sm:p-2 rounded-xl hover:bg-white/5 active:scale-95 transition-all duration-200 group"
                >
                  <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-semibold shadow-lg ring-2 ring-purple-500/20 group-hover:ring-purple-500/40 transition-all">
                    {user?.first_name?.charAt(0) || 'U'}
                  </div>
                  <FaChevronDown className={`w-3 h-3 text-[var(--text-secondary)] transition-transform duration-200 hidden sm:block ${isDropdownOpen ? 'rotate-180' : ''}`} />
                </button>

                {/* User Dropdown */}
                {isDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 sm:w-64 card-strong border-2 border-[var(--border-strong)] rounded-2xl shadow-2xl overflow-hidden z-50 animate-in slide-in-from-top-2 duration-200">

                    {/* User Info */}
                    <div className="px-4 py-5 flex flex-row items-center justify-between border-b-2 border-[var(--border-subtle)] bg-[var(--surface-2)]">
                      <div>
                        <p className="font-bold text-[var(--text-primary)] truncate text-base">
                          {user?.first_name} {user?.last_name}
                        </p>
                        <p className="text-xs text-[var(--text-secondary)] font-medium truncate mt-0.5">
                          {user?.email}
                        </p>
                      </div>
                      <span className="inline-block  px-2 py-1 text-xs font-bold rounded-md bg-[var(--surface)] text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 border-2 border-[var(--border-strong)] shadow-sm">
                        {user?.is_moderator ? 'Teacher' : 'Student'}
                      </span>
                    </div>

                    {/* Menu Items */}
                    <div className="py-2">
                      <Link
                        to="/profile"
                        className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--input-bg)] hover:text-[var(--text-primary)] transition-colors group"
                        onClick={() => setIsDropdownOpen(false)}
                      >
                        <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex flex-shrink-0 items-center justify-center group-hover:bg-indigo-500/20 transition-colors">
                          <FaUser className="w-3.5 h-3.5 text-indigo-400 group-hover:scale-110 transition-transform" />
                        </div>
                        <span>My Profile</span>
                      </Link>

                      {user?.is_moderator && (
                        <>
                          <div className="border-t-2 border-[var(--border-subtle)] my-2"></div>
                          <button
                            onClick={handleToggleModerator}
                            className="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--input-bg)] hover:text-[var(--text-primary)] transition-colors group"
                          >
                            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex flex-shrink-0 items-center justify-center group-hover:bg-blue-500/20 transition-colors">
                              <FaSync className="w-3.5 h-3.5 text-blue-400 group-hover:rotate-180 transition-transform duration-300" />
                            </div>
                            <span>{isModeratorActive ? 'Switch To Student' : 'Switch To Teacher'}</span>
                          </button>
                          <div className="border-t-2 border-[var(--border-subtle)] my-2"></div>
                        </>
                      )}

                      <Link
                        to="/settings"
                        className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--input-bg)] hover:text-[var(--text-primary)] transition-colors group"
                        onClick={() => setIsDropdownOpen(false)}
                      >
                        <div className="w-8 h-8 rounded-lg bg-gray-500/10 border border-gray-500/20 flex flex-shrink-0 items-center justify-center group-hover:bg-gray-500/20 transition-colors">
                          <FaCog className="w-3.5 h-3.5 text-gray-400 group-hover:rotate-90 transition-transform duration-300" />
                        </div>
                        <span>Settings</span>
                      </Link>
                    </div>

                    {/* Sign Out */}
                    <div className="border-t-2 border-[var(--border-subtle)] py-2">
                      <button
                        onClick={handleSignOut}
                        className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-500 hover:bg-red-500/10 hover:text-red-400 transition-colors group"
                      >
                        <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center flex-shrink-0 justify-center">
                          <FaSignOutAlt className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                        </div>
                        <span className="font-bold">Sign Out</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>
    );
  }

  return null;
};

export default Header;