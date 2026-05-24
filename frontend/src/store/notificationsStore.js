import { create } from 'zustand';
import { 
  getNotifications, 
  getUnreadNotificationsCount, 
  markNotificationRead, 
  markAllNotificationsRead, 
  markBulkNotificationsRead 
} from '../api/api';

export const useNotificationsStore = create((set, get) => ({
  // State
  notifications: [],
  unreadCount: 0,
  isLoading: false,
  error: null,

  // Actions
  fetchNotifications: async (includeRead = false, limit = null) => {
    set({ isLoading: true, error: null });
    try {
      const params = new URLSearchParams();
      if (includeRead) params.append('include_read', 'true');
      if (limit) params.append('limit', limit);
      
      const response = await getNotifications();
      
      set({ 
        notifications: response.notifications || [],
        unreadCount: response.count || 0,
        isLoading: false 
      });
      
      return { success: true, data: response };
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to fetch notifications';
      set({ 
        isLoading: false, 
        error: errorMessage 
      });
      return { success: false, error: errorMessage };
    }
  },

  fetchUnreadCount: async () => {
    try {
      const response = await getUnreadNotificationsCount();
      
      set({ 
        unreadCount: response.unread_count || 0 
      });
      
      return { success: true, count: response.unread_count };
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to fetch unread count';
      return { success: false, error: errorMessage };
    }
  },

  markAsRead: async (messageUid) => {
    set({ error: null });
    try {
      const response = await markNotificationRead(messageUid);
      
      // Update local state
      const notifications = get().notifications.map(notif => 
        notif.message_uid === messageUid 
          ? { ...notif, read: true } 
          : notif
      );
      
      const unreadCount = notifications.filter(n => !n.read).length;
      
      set({ 
        notifications,
        unreadCount 
      });
      
      return { success: true, data: response };
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to mark notification as read';
      set({ error: errorMessage });
      return { success: false, error: errorMessage };
    }
  },

  markAllAsRead: async () => {
    set({ error: null });
    try {
      const response = await markAllNotificationsRead();
      
      // Update local state - mark all as read
      const notifications = get().notifications.map(notif => 
        ({ ...notif, read: true })
      );
      
      set({ 
        notifications,
        unreadCount: 0 
      });
      
      return { success: true, data: response };
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to mark all notifications as read';
      set({ error: errorMessage });
      return { success: false, error: errorMessage };
    }
  },

  markBulkAsRead: async (messageUids) => {
    set({ error: null });
    try {
      const response = await markBulkNotificationsRead(messageUids);
      
      // Update local state
      const notifications = get().notifications.map(notif => 
        messageUids.includes(notif.message_uid)
          ? { ...notif, read: true }
          : notif
      );
      
      const unreadCount = notifications.filter(n => !n.read).length;
      
      set({ 
        notifications,
        unreadCount 
      });
      
      return { success: true, data: response };
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to mark notifications as read';
      set({ error: errorMessage });
      return { success: false, error: errorMessage };
    }
  },

  // Clear error
  clearError: () => set({ error: null }),

  // Reset store
  resetStore: () => set({ 
    notifications: [], 
    unreadCount: 0, 
    isLoading: false, 
    error: null 
  }),
  
}));