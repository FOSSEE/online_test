import { create } from 'zustand';
import {
  fetchCourseModules,
  fetchModuleDetail,
} from '../../api/api';

const useManageCourseStore = create((set, get) => ({
  // State
  activeTab: 'Modules',
  activeForumTab: 'Course Forum',
  course: null,
  courseLoading: false,
  courseError: null,

  modules: [],
  modulesLoading: false,
  modulesError: null,
  moduleDetail: null,
  moduleDetailLoading: false,
  moduleDetailError: null,

  // Actions
  setActiveTab: (tab) => set({ activeTab: tab }),
  setActiveForumTab: (tab) => set({ activeForumTab: tab }),

  // Load course data and modules (API returns both in one call)
  loadCourseData: async (courseId) => {
    set({ courseLoading: true, courseError: null, modulesLoading: true, modulesError: null });
    try {
      const data = await fetchCourseModules(courseId);
      
      // Response structure: { course: {...}, modules: [...] }
      if (data && data.course) {
        set({ 
          course: data.course, 
          modules: data.modules || [], 
          courseLoading: false, 
          modulesLoading: false 
        });
      } else {
         set({ 
            courseError: 'Invalid course data received', 
            courseLoading: false,
            modulesLoading: false
         });
      }
    } catch (error) {
      const errorMessage = error.message || 'Failed to load course.';
      set({ 
          courseError: errorMessage, 
          modulesError: errorMessage,
          courseLoading: false, 
          modulesLoading: false 
      });
    }
  },

  // Fetch all modules for a course (same endpoint as loadCourseData)
  loadCourseModules: async (courseId) => {
    await get().loadCourseData(courseId);
  },

  // Fetch details for a specific module
  loadModuleDetail: async (moduleId) => {
    set({ moduleDetailLoading: true, moduleDetailError: null });
    try {
      const data = await fetchModuleDetail(moduleId);
      set({ moduleDetail: data, moduleDetailLoading: false });
    } catch (error) {
      set({ moduleDetailError: error, moduleDetailLoading: false });
    }
  },

  // Optionally, clear module detail
  clearModuleDetail: () => set({ moduleDetail: null, moduleDetailError: null }),
}));

export default useManageCourseStore;