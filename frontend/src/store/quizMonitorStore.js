import { create } from "zustand";
import {
  monitorQuizProgress,
  getQuizStatistics,
  downloadQuizCSV,
  uploadMarksCSV,
  getUserData,
  extendAnswerPaperTime,
  allowSpecialAttempt,
  startSpecialAttempt,
  revokeSpecialAttempt,
} from "../api/api";

const useMonitorStore = create((set) => ({
  loading: false,
  error: null,
  result: null,

  // Monitor quiz progress
  monitorQuiz: async (quizId, courseId, attemptNumber = null) => {
    set({ loading: true, error: null, result: null });
    try {
      const data = await monitorQuizProgress(quizId, courseId, attemptNumber);
      set({ result: data, loading: false });
    } catch (error) {
      set({ error: error?.response?.data || error.message, loading: false });
    }
  },

  // Get quiz statistics
  fetchQuizStatistics: async (questionpaperId, courseId, attemptNumber = null) => {
    set({ loading: true, error: null, result: null });
    try {
      const data = await getQuizStatistics(questionpaperId, courseId, attemptNumber);
      set({ result: data, loading: false });
    } catch (error) {
      set({ error: error?.response?.data || error.message, loading: false });
    }
  },

  // Download quiz CSV
  downloadCSV: async (courseId, quizId, attemptNumber) => {
    set({ loading: true, error: null, result: null });
    try {
      const data = await downloadQuizCSV(courseId, quizId, attemptNumber);
      set({ result: data, loading: false });
    } catch (error) {
      set({ error: error?.response?.data || error.message, loading: false });
    }
  },

  // Upload marks CSV
  uploadCSV: async (courseId, questionpaperId, csvFile) => {
    set({ loading: true, error: null, result: null });
    try {
      const data = await uploadMarksCSV(courseId, questionpaperId, csvFile);
      set({ result: data, loading: false });
    } catch (error) {
      set({ error: error?.response?.data || error.message, loading: false });
    }
  },

  // Get user data
  fetchUserData: async (userId, questionpaperId = null, courseId = null) => {
    set({ loading: true, error: null, result: null });
    try {
      const data = await getUserData(userId, questionpaperId, courseId);
      set({ result: data, loading: false });
    } catch (error) {
      set({ error: error?.response?.data || error.message, loading: false });
    }
  },

  // Extend answer paper time
  extendTime: async (paperId, extraTime) => {
    set({ loading: true, error: null, result: null });
    try {
      const data = await extendAnswerPaperTime(paperId, extraTime);
      set({ result: data, loading: false });
    } catch (error) {
      set({ error: error?.response?.data || error.message, loading: false });
    }
  },

  // Allow special attempt
  allowSpecial: async (userId, courseId, quizId) => {
    set({ loading: true, error: null, result: null });
    try {
      const data = await allowSpecialAttempt(userId, courseId, quizId);
      set({ result: data, loading: false });
    } catch (error) {
      set({ error: error?.response?.data || error.message, loading: false });
    }
  },

  // Start special attempt
  startSpecial: async (micromanagerId) => {
    set({ loading: true, error: null, result: null });
    try {
      const data = await startSpecialAttempt(micromanagerId);
      set({ result: data, loading: false });
    } catch (error) {
      set({ error: error?.response?.data || error.message, loading: false });
    }
  },

  // Revoke special attempt
  revokeSpecial: async (micromanagerId) => {
    set({ loading: true, error: null, result: null });
    try {
      const data = await revokeSpecialAttempt(micromanagerId);
      set({ result: data, loading: false });
    } catch (error) {
      set({ error: error?.response?.data || error.message, loading: false });
    }
  },

  // Reset state
  reset: () => set({ loading: false, error: null, result: null }),
}));

export default useMonitorStore;