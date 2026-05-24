import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FaBell,
  FaCheck,
  FaCheckDouble,
  FaUser,
  FaClock,
  FaFilter,
  FaInbox,
  FaExclamationCircle,
  FaTimes,
  FaChartLine
} from 'react-icons/fa';
import Header from '../components/layout/Header';
import StudentSidebar from '../components/layout/Sidebar';
import TeacherSidebar from '../components/layout/TeacherSidebar';
import { useAuthStore } from '../store/authStore';
import { useNotificationsStore } from '../store/notificationsStore';
import { getModeratorStatus } from '../api/api';

const Notifications = () => {
  const { user, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all', 'unread', 'read'
  const [typeFilter, setTypeFilter] = useState('all'); // 'all', 'success', 'warning', 'danger', 'info'




  // Notifications store
  const {
    notifications,
    unreadCount,
    isLoading,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    markBulkAsRead
  } = useNotificationsStore();

  const [isModeratorActive, setIsModeratorActive] = useState(false);

  const isTeacher = user?.is_moderator && isModeratorActive;

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        // Fetch notifications
        await fetchNotifications();

        // Fetch current moderator toggle state if user is a moderator
        if (user?.is_moderator) {
          const status = await getModeratorStatus();
          setIsModeratorActive(status.is_moderator_active);
        }
      } catch (error) {
        console.error('Failed to load data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated, fetchNotifications, user]); // Add user to dependency array

  // Filter notifications
  const filteredNotifications = notifications.filter(notif => {
    // Filter by read status
    if (filter === 'unread' && notif.read) return false;
    if (filter === 'read' && !notif.read) return false;

    // Filter by type
    if (typeFilter !== 'all' && notif.message_type !== typeFilter) return false;

    return true;
  });

  const handleNotificationClick = async (notification) => {
    if (!notification.read) {
      await markAsRead(notification.message_uid);
    }
  };

  const handleMarkAllAsRead = async () => {
    await markAllAsRead();
  };

  const handleMarkSelectedAsRead = async () => {
    const unreadNotifications = filteredNotifications
      .filter(n => !n.read)
      .map(n => n.message_uid);

    if (unreadNotifications.length > 0) {
      await markBulkAsRead(unreadNotifications);
    }
  };

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-[var(--text-secondary)] mb-4">Please sign in to view notifications</p>
          <button
            onClick={() => navigate('/signin')}
            className="btn-grad px-6 py-2 rounded-lg"
          >
            Sign In
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex min-h-screen relative grid-texture">
        {isTeacher ? (
          <TeacherSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
        ) : (
          <StudentSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
        )}
        <main className="flex-1 lg:ml-64">
          <Header isAuth />
          <div className="p-8 flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto mb-4"></div>
              <p className="text-[var(--text-muted)] font-medium">Loading notifications...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen relative grid-texture">
      {/* Sidebar - Conditional based on role */}
      {isTeacher ? (
        <TeacherSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      ) : (
        <StudentSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      )}

      {/* Main Content */}
      <main className="flex-1 w-full min-w-0 overflow-x-hidden">
        <Header isAuth />

        <div className="p-4 sm:p-6 lg:p-8 ">
          {/* Header Section */}
          <div className="mb-6 lg:mb-8">
            <h1 className="text-2xl sm:text-3xl font-bold mb-2">Notifications</h1>
            <p className="text-sm muted">Check and manage notifications</p>
          </div>

          <div className="flex flex-col xl:flex-row gap-6">
            {/* Main Card */}
            <div className="flex-1 card-strong border-2 border-[var(--border-strong)] p-4 sm:p-6 relative rounded-2xl">
              {/* Card Header */}
              <div className="flex items-center justify-between gap-4 mb-4 sm:mb-6 pb-4 border-b-2 border-[var(--border-subtle)]">
                <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1 ">
                  <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-blue-500/10 border-2 border-blue-500/30 flex items-center justify-center flex-shrink-0">
                    <FaBell className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h2 className="text-lg sm:text-xl font-bold truncate">
                      All Notifications
                    </h2>
                    <p className="text-xs sm:text-sm muted">
                      {notifications.length} total • {unreadCount} unread
                    </p>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="absolute right-4 top-4 sm:right-6 sm:top-6 flex items-center gap-2 z-10">
                  {/* Statistics Button - Mobile/Tablet only */}
                  {notifications.length > 0 && (
                    <button
                      onClick={() => setIsSummaryOpen(true)}
                      className="xl:hidden bg-green-600 text-white px-3 sm:px-4 py-2 rounded-lg font-semibold hover:bg-purple-700 active:scale-95 transition text-xs sm:text-sm whitespace-nowrap"
                    >
                      <FaChartLine className="inline w-4 h-4 sm:mr-2" />
                      <span className="hidden sm:inline">Stats</span>
                    </button>
                  )}

                  {/* Mark All Read Button */}
                  {notifications.length > 0 && unreadCount > 0 && (
                    <button
                      onClick={handleMarkAllAsRead}
                      disabled={isLoading}
                      className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-blue-600/10 hover:bg-blue-600/20 border border-blue-500/30 text-blue-400 rounded-xl text-sm font-semibold transition-colors"
                    >
                      <FaCheckDouble className="inline w-4 h-4 sm:mr-2" />
                      <span className="hidden sm:inline">Mark All Read</span>
                    </button>
                  )}
                </div>
              </div>
              {/* Filters */}
              {notifications.length > 0 && (
                <div >
                  <div className="grid grid-cols-2 sm:grid-cols-2  gap-3 sm:gap-4">
                    {/* Status Filter */}
                    <div>
                      <label className="block text-xs sm:text-sm font-semibold mb-1.5 sm:mb-2">Status</label>
                      <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="w-full px-2 sm:px-3 md:px-4 py-2 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl text-sm focus:outline-none focus:border-blue-500/50 transition-colors"
                      >
                        <option value="all">All</option>
                        <option value="unread">Unread</option>
                        <option value="read">Read</option>
                      </select>
                    </div>

                    {/* Type Filter */}
                    <div>
                      <label className="block text-xs sm:text-sm font-semibold mb-1.5 sm:mb-2">Type</label>
                      <select
                        value={typeFilter}
                        onChange={(e) => setTypeFilter(e.target.value)}
                        className="w-full px-2 sm:px-3 md:px-4 py-2 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl text-sm focus:outline-none focus:border-blue-500/50 transition-colors"
                      >
                        <option value="all">All Types</option>
                        <option value="info">Info</option>
                        <option value="success">Success</option>
                        <option value="warning">Warning</option>
                        <option value="danger">Danger</option>
                      </select>
                    </div>
                  </div>

                  {/* Quick Action for Filtered Results */}
                  {filteredNotifications.filter(n => !n.read).length > 0 && (
                    <div className="mt-2 pt-2 border-t border-[var(--border-color)]">
                      <button
                        onClick={handleMarkSelectedAsRead}
                        disabled={isLoading}
                        className="text-xs sm:text-sm text-blue-400 hover:text-blue-300 font-medium transition-colors disabled:opacity-50"
                      >
                        Mark all filtered as read ({filteredNotifications.filter(n => !n.read).length})
                      </button>
                    </div>
                  )}
                </div>
              )}
              {/* Notifications List */}
              <div className="pt-4 sm:pt-6 lg:pt-8">
                {filteredNotifications.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-500/10 rounded-full mb-4">
                      {notifications.length === 0 ? (
                        <FaInbox className="w-8 h-8 text-purple-400" />
                      ) : (
                        <FaExclamationCircle className="w-8 h-8 text-purple-400" />
                      )}
                    </div>
                    <h3 className="text-lg sm:text-xl font-semibold mb-2">
                      {notifications.length === 0 ? 'No notifications yet' : 'No notifications match your filters'}
                    </h3>
                    <p className="text-sm muted">
                      {notifications.length === 0
                        ? "You're all caught up! New notifications will appear here."
                        : 'Try adjusting your filters to see more notifications.'}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3 sm:space-y-4">
                    {filteredNotifications.map((notification, index) => (
                      <div
                        key={notification.message_uid}
                        onClick={() => handleNotificationClick(notification)}
                        className={`card-strong p-4 sm:p-5 border-2 border-[var(--border-medium)] hover:shadow-lg hover:border-purple-500/70 dark:hover:border-purple-500/50 transition-all duration-300 group bg-[var(--surface)] rounded-xl ${!notification.read ? 'border-purple-500/30' : ''
                          }`}
                        style={{
                          animationDelay: `${index * 50}ms`,
                          animation: 'slideInUp 0.3s ease-out forwards'
                        }}
                      >
                        <div className="flex items-start gap-3 sm:gap-4">
                          {/* Avatar/Icon */}
                          <div className={`flex-shrink-0 w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center border-2 ${notification.message_type === 'success' ? 'bg-green-500/20 text-green-400 border-green-500/30' :
                            notification.message_type === 'warning' ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' :
                              notification.message_type === 'danger' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                                'bg-purple-500/20 text-purple-400 border-purple-500/30'
                            }`}>
                            {notification.sender_name ? (
                              <span className="text-base sm:text-lg font-bold">
                                {notification.sender_name.charAt(0).toUpperCase()}
                              </span>
                            ) : (
                              <FaBell className="w-5 h-5 sm:w-6 sm:h-6" />
                            )}
                          </div>

                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-3 mb-2">
                              <h3 className="text-sm sm:text-base font-semibold text-[var(--text-primary)] group-hover:text-purple-400 transition-colors">
                                {notification.summary}
                              </h3>
                              {!notification.read && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    markAsRead(notification.message_uid);
                                  }}
                                  className="p-2 flex-shrink-0 rounded-lg hover:bg-purple-500/20 active:bg-purple-500/30 text-purple-400 hover:text-purple-300 transition-all"
                                  title="Mark as read"
                                >
                                  <FaCheck className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                                </button>
                              )}
                            </div>

                            {notification.description && (
                              <div
                                className="text-xs sm:text-sm muted mb-3 leading-relaxed"
                                dangerouslySetInnerHTML={{ __html: notification.description }}
                              />
                            )}

                            {/* Meta info */}
                            <div className="flex flex-wrap items-center gap-x-2 gap-y-2.5 min-w-0">

                              <div className="flex flex-wrap items-center gap-x-2 gap-y-2.5">
                                {notification.sender_name && (
                                  <span className="inline-flex items-center gap-1.5 text-xs muted max-w-full">
                                    <FaUser className="w-3 h-3 flex-shrink-0" />
                                    <span className="truncate max-w-[100px] sm:max-w-none">{notification.sender_name}</span>
                                  </span>
                                )}
                                <span className="inline-flex items-center gap-1.5 text-xs muted">
                                  <FaClock className="w-3 h-3 flex-shrink-0" />
                                  <span className="whitespace-nowrap">{notification.time_since} ago</span>
                                </span>
                              </div>
                              <div className="flex flex-wrap items-center gap-x-2 gap-y-2.5">
                                {notification.message_type && (
                                  <span className={`inline-flex items-center text-xs font-medium ${notification.message_type === 'success' ? 'text-green-400' :
                                    notification.message_type === 'warning' ? 'text-yellow-400' :
                                      notification.message_type === 'danger' ? 'text-red-400' :
                                        'text-blue-400'
                                    }`}>
                                    {notification.message_type}
                                  </span>
                                )}
                                {!notification.read && (
                                  <span className="inline-flex items-center  text-xs font-medium text-purple-400">

                                    <span>unread</span>
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Summary Sidebar - Desktop only */}
            {notifications.length > 0 && (
              <aside className="hidden xl:block xl:w-80 2xl:w-96 flex-shrink-0">
                <div className="card-strong border-2 border-[var(--border-strong)] shadow-lg rounded-2xl p-5 sm:p-6 sticky top-24">

                  <div className="flex items-center gap-3 mb-6 pb-4 border-b-2 border-[var(--border-subtle)]">
                    <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border-2 border-indigo-500/30 flex items-center justify-center">
                      <FaChartLine className="w-5 h-5 text-indigo-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-[var(--text-primary)]">Statistics</h3>
                      <p className="text-xs muted">Overview of your notifications</p>
                    </div>
                  </div>


                  <div className="space-y-4">
                    <div className="p-4 rounded-lg bg-purple-500/10 border border-purple-500/30">
                      <div className="text-2xl sm:text-3xl font-bold text-purple-400 mb-1">
                        {notifications.length}
                      </div>
                      <div className="text-xs sm:text-sm soft">Total Notifications</div>
                    </div>

                    <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30">
                      <div className="text-2xl sm:text-3xl font-bold text-red-400 mb-1">
                        {notifications.filter(n => !n.read).length}
                      </div>
                      <div className="text-xs sm:text-sm soft">Unread</div>
                    </div>

                    <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/30">
                      <div className="text-2xl sm:text-3xl font-bold text-green-400 mb-1">
                        {notifications.filter(n => n.read).length}
                      </div>
                      <div className="text-xs sm:text-sm soft">Read</div>
                    </div>

                    <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
                      <div className="text-2xl sm:text-3xl font-bold text-blue-400 mb-1">
                        {notifications.filter(n => n.message_type === 'success').length}
                      </div>
                      <div className="text-xs sm:text-sm soft">Success Messages</div>
                    </div>
                  </div>



                </div>
              </aside>
            )}
          </div>
        </div>
      </main>

      {/* Mobile/Tablet Summary Modal */}
      {isSummaryOpen && notifications.length > 0 && (
        <div className="fixed inset-0 z-50 xl:hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
            onClick={() => setIsSummaryOpen(false)}
          />

          {/* Modal */}
          <div className="absolute inset-x-4 top-1/2 -translate-y-1/2 sm:inset-x-auto sm:left-1/2 sm:-translate-x-1/2 sm:w-full sm:max-w-md">
            <div className="card-strong rounded-2xl p-6 max-h-[80vh] overflow-y-auto  border-2 border-[var(--border-strong)]">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-xl font-bold flex items-center gap-2">
                    <FaBell className="w-5 h-5 text-purple-400" />
                    Statistics
                  </h3>
                  <p className="text-sm muted mt-1">Overview of your notifications</p>
                </div>
                <button
                  onClick={() => setIsSummaryOpen(false)}
                  className="p-2 hover:bg-white/5 rounded-lg transition-colors"
                >
                  <FaTimes className="w-5 h-5" />
                </button>
              </div>

              {/* Stats */}
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-purple-500/10 border border-purple-500/30">
                  <div className="text-3xl font-bold text-purple-400 mb-1">
                    {notifications.length}
                  </div>
                  <div className="text-sm soft">Total Notifications</div>
                </div>

                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30">
                  <div className="text-3xl font-bold text-red-400 mb-1">
                    {notifications.filter(n => !n.read).length}
                  </div>
                  <div className="text-sm soft">Unread</div>
                </div>

                <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/30">
                  <div className="text-3xl font-bold text-green-400 mb-1">
                    {notifications.filter(n => n.read).length}
                  </div>
                  <div className="text-sm soft">Read</div>
                </div>

                <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
                  <div className="text-3xl font-bold text-blue-400 mb-1">
                    {notifications.filter(n => n.message_type === 'success').length}
                  </div>
                  <div className="text-sm soft">Success Messages</div>
                </div>
              </div>


            </div>
          </div>
        </div>
      )}


      <style jsx>{`
        @keyframes slideInUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default Notifications;