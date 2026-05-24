import { create } from 'zustand';
import {
  apiStartQuiz,
  apiQuitQuiz,
  apiCompleteQuiz,
  apiCheckAnswer,
  apiSkipQuestion,
  testQuestion as apiTestQuestion,
} from '../api/api';

const useQuizStore = create((set, get) => ({
  // State
  quizIntro: null,
  currentQuestion: null,
  paper: null,
  loading: false,
  error: null,
  quizResult: null,
  answerResult: null,
  timeLeft: null,
  
  // Quiz parameters
  questionpaperId: null,
  moduleId: null,
  courseId: null,
  attemptNum: null,

  // Actions

  /**
   * Set quiz parameters
   */
  setQuizParams: (params) => set({
    questionpaperId: params.questionpaperId,
    moduleId: params.moduleId,
    courseId: params.courseId,
    attemptNum: params.attemptNum,
  }),

  /**
   * Get quiz intro (first step before starting)
   */
  getQuizIntro: async (questionpaperId, moduleId, courseId, attemptNum = null) => {
    set({ loading: true, error: null });
    try {
      const intro = await apiStartQuiz(questionpaperId, moduleId, courseId, attemptNum, null);
      set({ 
        quizIntro: intro,
        questionpaperId,
        moduleId,
        courseId,
        attemptNum,
        loading: false 
      });
      return intro;
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Failed to load quiz intro';
      set({ error: errorMsg, loading: false });
      throw new Error(errorMsg);
    }
  },

  startQuiz: async (questionpaperId, moduleId, courseId, attemptNum = null) => {
  set({ loading: true, error: null });
  try {
    const quizData = await apiStartQuiz(questionpaperId, moduleId, courseId, attemptNum, {});
    
    // Handle response - API returns current_question
    const question = quizData.current_question || quizData.question;
    
    // Check if this is a resume scenario
    const isResume = quizData.status === 'resume';
    
    set({ 
      currentQuestion: question,
      paper: {
        id: quizData.answerpaper_id,
        attempt_number: quizData.attempt_number,
        time_left: quizData.time_left,
        is_trial_mode: quizData.is_trial_mode,
        questions_answered: quizData.questions_answered,
        questions_unanswered: quizData.questions_unanswered,
      },
      timeLeft: quizData.time_left,
      questionpaperId: quizData.questionpaper_id || questionpaperId,
      moduleId: quizData.module_id || moduleId,
      courseId: quizData.course_id || courseId,
      attemptNum: quizData.attempt_number || attemptNum,
      loading: false 
    });
    
    // Return full data including resume status
    return {
      ...quizData,
      isResume,
    };
  } catch (err) {
    const errorMsg = err.response?.data?.error || 'Failed to start quiz';
    set({ error: errorMsg, loading: false });
    throw new Error(errorMsg);
  }
},

  /**
   * Resume quiz with existing attempt
   */
  resumeQuiz: async (attemptNum, moduleId, questionpaperId, courseId) => {
    set({ loading: true, error: null });
    try {
      const quizData = await apiStartQuiz(questionpaperId, moduleId, courseId, attemptNum);
      
      const question = quizData.current_question || quizData.question;
      
      set({ 
        currentQuestion: question,
        paper: {
          id: quizData.answerpaper_id,
          attempt_number: quizData.attempt_number,
          time_left: quizData.time_left,
          is_trial_mode: quizData.is_trial_mode,
          questions_answered: quizData.questions_answered,
          questions_unanswered: quizData.questions_unanswered,
        },
        timeLeft: quizData.time_left,
        questionpaperId: quizData.questionpaper_id || questionpaperId,
        moduleId: quizData.module_id || moduleId,
        courseId: quizData.course_id || courseId,
        attemptNum,
        loading: false 
      });
      return quizData;
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Failed to resume quiz';
      set({ error: errorMsg, loading: false });
      throw new Error(errorMsg);
    }
  },

  /**
   * Submit an answer for the current question
   */
  submitAnswer: async (questionId, answerData) => {
  const { attemptNum, moduleId, questionpaperId, courseId } = get();
  set({ loading: true, error: null });
  
  try {
    const result = await apiCheckAnswer(
      questionId,
      attemptNum,
      moduleId,
      questionpaperId,
      courseId,
      answerData
    );
    
    // Handle response - could have next_question or current_question
    const nextQuestion = result.next_question || result.current_question || result.question;
    
    set({ 
      answerResult: {
        success: result.success,
        error_message: result.error_message || result.message,
      },
      currentQuestion: nextQuestion,
      paper: {
        ...get().paper,
        time_left: result.time_left || result.paper?.time_left,
        questions_answered: result.questions_answered || result.paper?.questions_answered,
        questions_unanswered: result.questions_unanswered || result.paper?.questions_unanswered,
      },
      timeLeft: result.time_left || result.paper?.time_left || get().timeLeft,
      loading: false 
    });
    
    return result;
  } catch (err) {
    const errorMsg = err.response?.data?.error || 'Failed to submit answer';
    set({ error: errorMsg, loading: false });
    throw new Error(errorMsg);
  }
},

  /**
   * Get current question state (without submitting)
   */
  getCurrentQuestion: async (questionId) => {
    const { attemptNum, moduleId, questionpaperId, courseId } = get();
    set({ loading: true, error: null });
    
    try {
      const result = await apiCheckAnswer(
        questionId,
        attemptNum,
        moduleId,
        questionpaperId,
        courseId,
        null
      );
      
      const question = result.current_question || result.question;
      
      set({ 
        currentQuestion: question,
        paper: {
          ...get().paper,
          time_left: result.time_left || result.paper?.time_left,
        },
        timeLeft: result.time_left || result.paper?.time_left || get().timeLeft,
        loading: false 
      });
      
      return result;
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Failed to get question';
      set({ error: errorMsg, loading: false });
      throw new Error(errorMsg);
    }
  },

  /**
   * Skip current question
   */
  skipQuestion: async (questionId, nextQuestionId = null, codeData = null) => {
    const { attemptNum, moduleId, questionpaperId, courseId } = get();
    set({ loading: true, error: null });
    
    try {
      const result = await apiSkipQuestion(
        questionId,
        attemptNum,
        moduleId,
        questionpaperId,
        courseId,
        nextQuestionId,
        codeData
      );
      
      const nextQuestion = result.question || result.next_question || result.current_question;
      
      set({ 
        currentQuestion: nextQuestion,
        paper: {
          ...get().paper,
          time_left: result.time_left || result.paper?.time_left,
          questions_answered: result.questions_answered,
          questions_unanswered: result.questions_unanswered,
        },
        timeLeft: result.time_left || result.paper?.time_left || get().timeLeft,
        loading: false 
      });
      
      return result;
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Failed to skip question';
      set({ error: errorMsg, loading: false });
      throw new Error(errorMsg);
    }
  },

  /**
   * Complete/submit the quiz
   */
  completeQuiz: async () => {
    const { attemptNum, moduleId, questionpaperId, courseId } = get();
    set({ loading: true, error: null });
    
    try {
      const result = await apiCompleteQuiz(
        attemptNum,
        moduleId,
        questionpaperId,
        courseId,
        {}
      );
      
      set({ 
        quizResult: result,
        paper: result.paper || get().paper,
        loading: false 
      });
      
      return result;
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Failed to complete quiz';
      set({ error: errorMsg, loading: false });
      throw new Error(errorMsg);
    }
  },

  /**
   * Quit the quiz
   */
  quitQuiz: async (reason = null) => {
    const { attemptNum, moduleId, questionpaperId, courseId } = get();
    set({ loading: true, error: null });
    
    try {
      const result = await apiQuitQuiz(
        attemptNum,
        moduleId,
        questionpaperId,
        courseId,
        reason
      );
      
      set({ 
        quizResult: result,
        paper: result.paper || get().paper,
        loading: false 
      });
      
      return result;
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Failed to quit quiz';
      set({ error: errorMsg, loading: false });
      throw new Error(errorMsg);
    }
  },

  /**
   * Test a question (teacher only)
   * This creates a test quiz and returns the full quiz data with first question
   */
  testQuestion: async (questionId) => {
    set({ loading: true, error: null });
    try {
      // The test API returns the complete quiz response with current_question
      const result = await apiTestQuestion(questionId);
      
      // Extract question from response
      const question = result.current_question || result.question;
      
      // Set all state from the test response
      set({ 
        currentQuestion: question,
        paper: {
          id: result.answerpaper_id,
          attempt_number: result.attempt_number,
          time_left: result.time_left,
          is_trial_mode: result.is_trial_mode,
          questions_answered: result.questions_answered,
          questions_unanswered: result.questions_unanswered,
        },
        timeLeft: result.time_left,
        questionpaperId: result.questionpaper_id,
        moduleId: result.module_id,
        courseId: result.course_id,
        attemptNum: result.attempt_number,
        loading: false 
      });
      
      return result;
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message || 'Failed to create test quiz';
      set({ error: errorMsg, loading: false });
      throw new Error(errorMsg);
    }
  },

  /**
   * Clear error
   */
  clearError: () => set({ error: null }),

  /**
   * Reset quiz state
   */
  resetQuiz: () => set({
    quizIntro: null,
    currentQuestion: null,
    paper: null,
    loading: false,
    error: null,
    quizResult: null,
    answerResult: null,
    timeLeft: null,
    questionpaperId: null,
    moduleId: null,
    courseId: null,
    attemptNum: null,
  }),

  /**
   * Update time left (for countdown timer)
   */
  updateTimeLeft: (seconds) => set({ timeLeft: seconds }),
}));

export default useQuizStore;