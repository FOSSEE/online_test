import { create } from 'zustand';
import { 
  fetchCoursesList, 
  searchNewCourses, 
  fetchAvailableCourses as fetchAvailableCoursesApi,
  requestCourseEnrollment, 
  selfEnrollInCourse 
} from '../../api/api';

const useCourseStore = create((set, get) => ({
  // State
  courses: [],
  newCourses: [],
  loading: false,
  error: null,
  enrollmentLoading: false,
  enrollmentError: null,
  enrollmentSuccess: null,

  // Fetch enrolled courses only
  fetchCourses: async () => {
    set({ loading: true, error: null });
    try {
      const data = await fetchCoursesList();
      set({ courses: data.courses || [], loading: false });
    } catch (err) {
      set({ error: err.message || 'Failed to fetch courses', loading: false });
    }
  },

  // Search for new courses by code
  searchCourses: async (courseCode) => {
    set({ loading: true, error: null });
    try {
      const data = await searchNewCourses(courseCode);
      set({ newCourses: data.courses || [], loading: false });
    } catch (err) {
      set({ error: err.message || 'Failed to search courses', loading: false });
    }
  },

  // Fetch all available (non-enrolled) courses
  fetchAvailableCourses: async () => {
    set({ loading: true, error: null });
    try {
      const data = await fetchAvailableCoursesApi();
      set({ newCourses: data.courses || [], loading: false });
    } catch (err) {
      set({ error: err.message || 'Failed to fetch available courses', loading: false });
    }
  },

  // Request enrollment in a course (requires approval)
  requestEnrollment: async (courseId) => {
    set({ enrollmentLoading: true, enrollmentError: null, enrollmentSuccess: null });
    try {
      const data = await requestCourseEnrollment(courseId);
      set({ 
        enrollmentLoading: false, 
        enrollmentSuccess: data.message || 'Enrollment request sent successfully',
      });
      
      // Optionally refresh the courses list after successful request
      // Uncomment if you want to auto-refresh
      // get().fetchCourses();
      
      return { success: true, data };
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to send enrollment request';
      set({ 
        enrollmentError: errorMessage, 
        enrollmentLoading: false 
      });
      return { success: false, error: errorMessage };
    }
  },

  // Self-enroll in a course (direct enrollment)
  selfEnroll: async (courseId) => {
    set({ enrollmentLoading: true, enrollmentError: null, enrollmentSuccess: null });
    try {
      const data = await selfEnrollInCourse(courseId);
      set({ 
        enrollmentLoading: false, 
        enrollmentSuccess: data.message || 'Successfully enrolled in course',
      });
      
      // Optionally refresh the courses list after successful enrollment
      // Uncomment if you want to auto-refresh
      // get().fetchCourses();
      
      return { success: true, data };
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to enroll in course';
      set({ 
        enrollmentError: errorMessage, 
        enrollmentLoading: false 
      });
      return { success: false, error: errorMessage };
    }
  },

  // Smart enroll function - automatically chooses between request and self-enroll
  enrollInCourse: async (courseId, isSelfEnroll = false) => {
    if (isSelfEnroll) {
      return get().selfEnroll(courseId);
    } else {
      return get().requestEnrollment(courseId);
    }
  },

  // Clear search results
  clearSearch: () => set({ newCourses: [] }),

  // Clear enrollment messages
  clearEnrollmentMessages: () => set({ 
    enrollmentError: null, 
    enrollmentSuccess: null 
  }),

  // Reset all state
  resetStore: () => set({
    courses: [],
    newCourses: [],
    loading: false,
    error: null,
    enrollmentLoading: false,
    enrollmentError: null,
    enrollmentSuccess: null,
  }),
}));

export default useCourseStore;