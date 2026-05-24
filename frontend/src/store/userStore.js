import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import api from '../api/api';

// User store using Zustand
export const useUserStore = create(
  persist(
    (set, get) => ({
      // State
      user: null,
      isLoading: false,
      error: null,

      // Actions
      fetchUserProfile: async (username) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.get(`api/auth/profile/?username=${username}`);
          const { user } = response.data;
          
          // Update user in both local storage and store
          localStorage.setItem('user', JSON.stringify(user));
          set({ 
            user, 
            isLoading: false 
          });
          
          return { success: true, user };
        } catch (error) {
          const errorMessage = error.response?.data?.error || 'Failed to fetch profile';
          set({ 
            isLoading: false, 
            error: errorMessage 
          });
          return { success: false, error: errorMessage };
        }
      },

      updateUserProfile: async (username, userData) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post('api/auth/profile/update/', {
            username,
            ...userData
          });
          
          const { user } = response.data;
          
          // Update user in both local storage and store
          const currentUser = get().user;
          const updatedUser = { ...currentUser, ...user };
          localStorage.setItem('user', JSON.stringify(updatedUser));
          
          set({ 
            user: updatedUser, 
            isLoading: false 
          });
          
          return { success: true, user: updatedUser };
        } catch (error) {
          const errorMessage = error.response?.data?.error || 'Failed to update profile';
          set({ 
            isLoading: false, 
            error: errorMessage 
          });
          return { success: false, error: errorMessage };
        }
      },

      // Update local user data (for immediate UI updates)
      updateLocalUser: (userData) => {
        const currentUser = get().user;
        const updatedUser = { ...currentUser, ...userData };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        set({ user: updatedUser });
      },

      // Clear user data
      clearUser: () => {
        localStorage.removeItem('user');
        set({ 
          user: null, 
          isLoading: false, 
          error: null 
        });
      },

      // Initialize user from localStorage
      initializeUser: () => {
        const userStr = localStorage.getItem('user');
        if (userStr) {
          try {
            const user = JSON.parse(userStr);
            set({ user });
          } catch (error) {
            console.error('Failed to parse user data:', error);
            localStorage.removeItem('user');
          }
        }
      },

      // Clear error
      clearError: () => set({ error: null }),
    }),
    {
      name: 'user-storage',
      partialize: (state) => ({
        user: state.user,
        isLoading: state.isLoading,
      }),
    }
  )
);
