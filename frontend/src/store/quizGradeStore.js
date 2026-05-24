// Updated quizGradeStore.js - Extended with quiz listing functionality
import { create } from 'zustand';
import {
  getGradingCourses,
  getQuizUsers,
  getUserAttempts,
  gradeUserAttempt,
} from '../api/api';
import { fetchTeacherQuizzesGrouped } from '../api/api';

export const useQuizGradingStore = create((set, get) => ({
  // State
  courses: [],
  selectedCourse: null,
  selectedModule: null,
  selectedQuiz: null,
  
  // Quiz listing state (for TeacherQuizzes page)
  quizzesByCourse: [], // Stores grouped quizzes by course
  loadingQuizzes: false,
  quizzesError: null,
  
  // Quiz Users data
  quizUsersData: null, // Will store { quiz, course, users, has_quiz_assignments }
  
  // User Attempts data
  userAttemptsData: null, // Will store { quiz, course, student, attempts, has_user_assignments, users }
  
  // Attempt Details/Grading data
  attemptGradingData: null, // Will store { quiz, course, student, papers }
  
  // Loading states
  loading: {
    courses: false,
    quizUsers: false,
    userAttempts: false,
    attemptGrading: false,
    submittingGrades: false,
  },
  
  // Error states
  error: {
    courses: null,
    quizUsers: null,
    userAttempts: null,
    attemptGrading: null,
    submittingGrades: null,
  },
  
  // Success messages
  successMessage: null,

  // ============================================================
  // QUIZ LISTING (for TeacherQuizzes page)
  // ============================================================

  /**
   * Load all quizzes grouped by course
   * Response: [{ course_id, course_name, course_code, quizzes: [...] }]
   */
  loadTeacherQuizzes: async () => {
    set({ loadingQuizzes: true, quizzesError: null });
    
    try {
      const data = await fetchTeacherQuizzesGrouped();
      set({ 
        quizzesByCourse: data,
        loadingQuizzes: false,
        quizzesError: null
      });
      return data;
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to load quizzes';
      set({ 
        quizzesError: errorMessage,
        loadingQuizzes: false 
      });
      throw err;
    }
  },

  /**
   * Get filtered quizzes based on search and type
   */
  getFilteredQuizzes: (searchQuery = '', filterType = 'all') => {
    const { quizzesByCourse } = get();
    
    return quizzesByCourse.map(course => {
      const filteredQuizzes = course.quizzes.filter(quiz => {
        const matchesSearch = quiz.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            quiz.module_name.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesType = filterType === 'all' || 
                          (filterType === 'quiz' && !quiz.is_exercise) ||
                          (filterType === 'exercise' && quiz.is_exercise);
        return matchesSearch && matchesType;
      });

      return {
        ...course,
        quizzes: filteredQuizzes
      };
    }).filter(course => course.quizzes.length > 0);
  },

  /**
   * Get quiz statistics
   */
  getQuizStats: () => {
    const { quizzesByCourse } = get();
    
    const totalQuizzes = quizzesByCourse.reduce(
      (sum, c) => sum + c.quizzes.filter(q => !q.is_exercise).length, 0
    );
    const totalExercises = quizzesByCourse.reduce(
      (sum, c) => sum + c.quizzes.filter(q => q.is_exercise).length, 0
    );
    const totalActive = quizzesByCourse.reduce(
      (sum, c) => sum + c.quizzes.filter(q => q.active).length, 0
    );
    
    return { totalQuizzes, totalExercises, totalActive };
  },

  // ============================================================
  // COURSES
  // ============================================================

  /**
   * Load all courses available for grading
   * Response: { courses: [...] }
   */
  loadGradingCourses: async () => {
    set((state) => ({
      loading: { ...state.loading, courses: true },
      error: { ...state.error, courses: null },
    }));
    
    try {
      const data = await getGradingCourses();
      set((state) => ({
        courses: data.courses || [],
        loading: { ...state.loading, courses: false },
      }));
      return data;
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to load grading courses';
      set((state) => ({
        error: { ...state.error, courses: errorMessage },
        loading: { ...state.loading, courses: false },
      }));
      throw err;
    }
  },

  /**
   * Select a course for grading
   */
  selectCourse: (course) => {
    set({ 
      selectedCourse: course,
      selectedModule: null,
      selectedQuiz: null,
      quizUsersData: null,
      userAttemptsData: null,
      attemptGradingData: null,
    });
  },

  /**
   * Select a module within the course
   */
  selectModule: (module) => {
    set({
      selectedModule: module,
      selectedQuiz: null,
      quizUsersData: null,
      userAttemptsData: null,
      attemptGradingData: null,
    });
  },

  /**
   * Clear selected course
   */
  clearCourse: () => {
    set({
      selectedCourse: null,
      selectedModule: null,
      selectedQuiz: null,
      quizUsersData: null,
      userAttemptsData: null,
      attemptGradingData: null,
    });
  },

  // ============================================================
  // QUIZ USERS (Level 2)
  // ============================================================

  /**
   * Load users who attempted a specific quiz
   * Response: { quiz, course, users, has_quiz_assignments }
   */
  loadQuizUsers: async (quizId, courseId) => {
    set((state) => ({
      loading: { ...state.loading, quizUsers: true },
      error: { ...state.error, quizUsers: null },
      quizUsersData: null,
      userAttemptsData: null,
      attemptGradingData: null,
    }));

    try {
      const data = await getQuizUsers(quizId, courseId);
      set((state) => ({
        quizUsersData: data,
        loading: { ...state.loading, quizUsers: false },
      }));
      return data;
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to load quiz users';
      set((state) => ({
        error: { ...state.error, quizUsers: errorMessage },
        loading: { ...state.loading, quizUsers: false },
      }));
      throw err;
    }
  },

  /**
   * Select a quiz and load its users
   */
  selectQuizAndLoadUsers: async (quiz, courseId) => {
    set({
      selectedQuiz: quiz,
      userAttemptsData: null,
      attemptGradingData: null,
    });

    return await get().loadQuizUsers(quiz.id, courseId);
  },

  /**
   * Select a quiz without loading users
   */
  selectQuiz: (quiz) => {
    set({
      selectedQuiz: quiz,
      userAttemptsData: null,
      attemptGradingData: null,
    });
  },

  /**
   * Clear quiz selection
   */
  clearQuiz: () => {
    set({
      selectedQuiz: null,
      quizUsersData: null,
      userAttemptsData: null,
      attemptGradingData: null,
    });
  },

  // ============================================================
  // USER ATTEMPTS (Level 3)
  // ============================================================

  /**
   * Load all attempts of a user for a quiz
   * Response: { quiz, course, student, attempts, has_user_assignments, users }
   */
  loadUserAttempts: async (quizId, userId, courseId) => {
    set((state) => ({
      loading: { ...state.loading, userAttempts: true },
      error: { ...state.error, userAttempts: null },
      userAttemptsData: null,
      attemptGradingData: null,
    }));

    try {
      const data = await getUserAttempts(quizId, userId, courseId);
      set((state) => ({
        userAttemptsData: data,
        loading: { ...state.loading, userAttempts: false },
      }));
      return data;
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to load user attempts';
      set((state) => ({
        error: { ...state.error, userAttempts: errorMessage },
        loading: { ...state.loading, userAttempts: false },
      }));
      throw err;
    }
  },

  /**
   * Clear user attempts data
   */
  clearUserAttempts: () => {
    set({
      userAttemptsData: null,
      attemptGradingData: null,
    });
  },

  // ============================================================
  // ATTEMPT GRADING (Level 4)
  // ============================================================

  /**
   * Load grading details for a specific attempt
   * Response: { quiz, course, student, papers }
   * papers contains: [{ id, marks_obtained, percent, status, comments, questions: [{ question, answer }] }]
   */
  loadAttemptGrading: async (quizId, userId, attemptNumber, courseId) => {
    set((state) => ({
      loading: { ...state.loading, attemptGrading: true },
      error: { ...state.error, attemptGrading: null },
      attemptGradingData: null,
    }));

    try {
      const data = await gradeUserAttempt(quizId, userId, attemptNumber, courseId);
      set((state) => ({
        attemptGradingData: data,
        loading: { ...state.loading, attemptGrading: false },
      }));
      return data;
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to load attempt grading details';
      set((state) => ({
        error: { ...state.error, attemptGrading: errorMessage },
        loading: { ...state.loading, attemptGrading: false },
      }));
      throw err;
    }
  },

  /**
   * Submit grades for a specific attempt
   * POST with gradesData
   */
  submitGrades: async (quizId, userId, attemptNumber, courseId, gradesData) => {
    set((state) => ({
      loading: { ...state.loading, submittingGrades: true },
      error: { ...state.error, submittingGrades: null },
      successMessage: null,
    }));

    try {
      const data = await gradeUserAttempt(quizId, userId, attemptNumber, courseId, gradesData);
      
      // Reload attempt grading data after successful submission
      await get().loadAttemptGrading(quizId, userId, attemptNumber, courseId);
      
      set((state) => ({
        loading: { ...state.loading, submittingGrades: false },
        successMessage: 'Grades submitted successfully',
      }));
      
      return data;
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to submit grades';
      set((state) => ({
        error: { ...state.error, submittingGrades: errorMessage },
        loading: { ...state.loading, submittingGrades: false },
      }));
      throw err;
    }
  },

  /**
   * Clear attempt grading data
   */
  clearAttemptGrading: () => {
    set({
      attemptGradingData: null,
    });
  },

  // ============================================================
  // HELPER GETTERS
  // ============================================================

  /**
   * Get all quizzes from the selected course (flattened from modules)
   */
  getAllQuizzesFromCourse: () => {
    const { selectedCourse } = get();
    if (!selectedCourse || !selectedCourse.learning_module) return [];

    const quizzes = [];
    selectedCourse.learning_module.forEach((module) => {
      if (module.learning_unit) {
        module.learning_unit.forEach((unit) => {
          if (unit.type === 'quiz' && unit.quiz) {
            quizzes.push({
              ...unit.quiz,
              module_id: module.id,
              module_name: module.name,
              unit_id: unit.id,
              unit_order: unit.order,
            });
          }
        });
      }
    });

    return quizzes;
  },

  /**
   * Get quizzes from selected module
   */
  getQuizzesFromModule: () => {
    const { selectedModule } = get();
    if (!selectedModule || !selectedModule.learning_unit) return [];

    return selectedModule.learning_unit
      .filter((unit) => unit.type === 'quiz' && unit.quiz)
      .map((unit) => ({
        ...unit.quiz,
        unit_id: unit.id,
        unit_order: unit.order,
        check_prerequisite: unit.check_prerequisite,
      }));
  },

  /**
   * Get users who attempted the current quiz
   */
  getCurrentQuizUsers: () => {
    const { quizUsersData } = get();
    return quizUsersData?.users || [];
  },

  /**
   * Get attempts for current user
   */
  getCurrentUserAttempts: () => {
    const { userAttemptsData } = get();
    return userAttemptsData?.attempts || [];
  },

  /**
   * Get papers/questions for current attempt
   */
  getCurrentAttemptPapers: () => {
    const { attemptGradingData } = get();
    return attemptGradingData?.papers || [];
  },

  /**
   * Get specific paper from current attempt grading
   */
  getCurrentPaper: (paperId) => {
    const { attemptGradingData } = get();
    if (!attemptGradingData?.papers) return null;
    return attemptGradingData.papers.find((paper) => paper.id === paperId);
  },

  /**
   * Get all questions with answers from current paper
   */
  getCurrentPaperQuestions: (paperId = null) => {
    const papers = get().getCurrentAttemptPapers();
    if (papers.length === 0) return [];
    
    const paper = paperId 
      ? papers.find((p) => p.id === paperId)
      : papers[0];
    
    return paper?.questions || [];
  },

  // ============================================================
  // UTILITY METHODS
  // ============================================================

  /**
   * Check if any loading is in progress
   */
  isLoading: () => {
    const { loading, loadingQuizzes } = get();
    return loadingQuizzes || Object.values(loading).some((val) => val === true);
  },

  /**
   * Check if there are any errors
   */
  hasErrors: () => {
    const { error, quizzesError } = get();
    return quizzesError !== null || Object.values(error).some((val) => val !== null);
  },

  /**
   * Get all current errors as an array
   */
  getAllErrors: () => {
    const { error, quizzesError } = get();
    const errors = Object.entries(error)
      .filter(([_, val]) => val !== null)
      .map(([key, val]) => ({ type: key, message: val }));
    
    if (quizzesError) {
      errors.push({ type: 'quizzes', message: quizzesError });
    }
    
    return errors;
  },

  /**
   * Clear all error messages
   */
  clearErrors: () => {
    set({
      quizzesError: null,
      error: {
        courses: null,
        quizUsers: null,
        userAttempts: null,
        attemptGrading: null,
        submittingGrades: null,
      },
    });
  },

  /**
   * Clear specific error
   */
  clearError: (errorType) => {
    if (errorType === 'quizzes') {
      set({ quizzesError: null });
    } else {
      set((state) => ({
        error: { ...state.error, [errorType]: null },
      }));
    }
  },

  /**
   * Clear success message
   */
  clearSuccessMessage: () => {
    set({ successMessage: null });
  },

  /**
   * Reset entire store to initial state
   */
  reset: () => {
    set({
      courses: [],
      selectedCourse: null,
      selectedModule: null,
      selectedQuiz: null,
      quizzesByCourse: [],
      loadingQuizzes: false,
      quizzesError: null,
      quizUsersData: null,
      userAttemptsData: null,
      attemptGradingData: null,
      loading: {
        courses: false,
        quizUsers: false,
        userAttempts: false,
        attemptGrading: false,
        submittingGrades: false,
      },
      error: {
        courses: null,
        quizUsers: null,
        userAttempts: null,
        attemptGrading: null,
        submittingGrades: null,
      },
      successMessage: null,
    });
  },

  // ============================================================
  // NAVIGATION HELPERS
  // ============================================================

  /**
   * Navigate to a specific level in the grading hierarchy
   * Useful for breadcrumb navigation
   */
  navigateToLevel: (level) => {
    switch (level) {
      case 'courses':
        get().clearCourse();
        break;
      case 'course':
        get().clearQuiz();
        set({ selectedModule: null });
        break;
      case 'module':
        get().clearQuiz();
        break;
      case 'quiz':
        get().clearUserAttempts();
        break;
      case 'user':
        get().clearAttemptGrading();
        break;
      default:
        break;
    }
  },
}));

export default useQuizGradingStore;