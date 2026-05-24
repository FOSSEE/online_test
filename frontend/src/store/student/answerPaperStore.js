import { create } from 'zustand';
import { viewAnswerPaper } from '../../api/api';

const useAnswerPaperStore = create((set, get) => ({
  // State
  quiz: null,
  courseId: null,
  courseName: null,
  moduleName: null,
  user: null,
  profile: null,
  papers: [], // Holds all the attempt data returned from the API
  questionPaperId: null,
  hasUserAssignments: false,
  
  // Tab/Attempt Switching State
  selectedAttemptNumber: null,
  selectedPaper: null, // The currently viewed paper attempt

  // Loading & Error States
  loading: false,
  error: null,

  // ============================================================
  // ACTIONS
  // ============================================================

  /**
   * Fetch the answer paper data for a specific question paper and course
   */
  fetchAnswerPaperData: async (questionPaperId, courseId) => {
    set({ loading: true, error: null });
    
    try {
      const data = await viewAnswerPaper(questionPaperId, courseId);
      
      const papers = data.papers || [];
      
      // Select Attempt 1 (or the lowest available attempt) as default
      const defaultPaper = papers.length > 0 
        ? [...papers].sort((a, b) => a.attempt_number - b.attempt_number)[0] 
        : null;
        
      const defaultAttemptNumber = defaultPaper ? defaultPaper.attempt_number : null;

      set({
        quiz: data.quiz,
        courseId: data.course_id,
        courseName: data.course_name,   
        moduleName: data.module_name,
        user: data.user,
        profile: data.profile,
        papers: papers,
        questionPaperId: data.questionpaper_id,
        hasUserAssignments: data.has_user_assignments,
        
        // Auto-select the latest attempt
        selectedPaper: defaultPaper,
        selectedAttemptNumber: defaultAttemptNumber,
        
        loading: false,
      });

      return data;
    } catch (err) {
      const errorMessage =
        err.response?.data?.detail || 
        err.response?.data?.error || 
        'Failed to load answer paper data.';
      
      set({ 
        error: errorMessage, 
        loading: false 
      });
      
      throw err;
    }
  },

  /**
   * Switch the currently viewed attempt tab
   */
  selectAttempt: (attemptNumber) => {
    const { papers } = get();
    // Find the paper corresponding to the selected attempt number
    const newSelectedPaper = papers.find(
      (paper) => paper.attempt_number === attemptNumber
    );

    if (newSelectedPaper) {
      set({
        selectedAttemptNumber: attemptNumber,
        selectedPaper: newSelectedPaper,
      });
    }
  },

  /**
   * Clear the store state (useful when unmounting the component)
   */
  reset: () => {
    set({
      quiz: null,
      courseId: null,
      courseName: null,
      moduleName: null,
      user: null,
      profile: null,
      papers: [],
      questionPaperId: null,
      hasUserAssignments: false,
      selectedAttemptNumber: null,
      selectedPaper: null,
      loading: false,
      error: null,
    });
  },

  // ============================================================
  // GETTERS (Selectors)
  // ============================================================

  /**
   * Get an array of all available attempt numbers for rendering tabs
   */
  getAvailableAttemptNumbers: () => {
    const { papers } = get();
    // Returning sorted attempt numbers (optional: sort them descending or ascending as preferred)
    return papers.map((p) => p.attempt_number).sort((a, b) => b - a);
  }
}));

export default useAnswerPaperStore;