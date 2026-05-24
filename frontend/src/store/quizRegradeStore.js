import { create } from "zustand";
import {
  regradePaperByQuiz,
  regradePaperByUser,
  regradePaperByQuestion,
} from "../api/api";

const useRegradingStore = create((set) => ({
  loading: false,
  error: null,
  result: null,

  // Trigger regrade by quiz
  regradeByQuiz: async (courseId, questionpaperId, questionId) => {
    set({ loading: true, error: null, result: null });
    try {
      const data = await regradePaperByQuiz(courseId, questionpaperId, questionId);
      set({ result: data, loading: false });
    } catch (error) {
      set({ error: error?.response?.data || error.message, loading: false });
    }
  },

  // Trigger regrade by user
  regradeByUser: async (courseId, questionpaperId, answerpaperId) => {
    set({ loading: true, error: null, result: null });
    try {
      const data = await regradePaperByUser(courseId, questionpaperId, answerpaperId);
      set({ result: data, loading: false });
    } catch (error) {
      set({ error: error?.response?.data || error.message, loading: false });
    }
  },

  // Trigger regrade by question
  regradeByQuestion: async (courseId, questionpaperId, answerpaperId, questionId) => {
    set({ loading: true, error: null, result: null });
    try {
      const data = await regradePaperByQuestion(courseId, questionpaperId, answerpaperId, questionId);
      set({ result: data, loading: false });
    } catch (error) {
      set({ error: error?.response?.data || error.message, loading: false });
    }
  },

  // Reset state
  reset: () => set({ loading: false, error: null, result: null }),
}));

export default useRegradingStore;