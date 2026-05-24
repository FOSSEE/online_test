import { create } from 'zustand';
import {
  fetchTeacherQuestions,
  getTeacherQuestion,
  deleteQuestionFile,
  updateQuestion,
  deleteQuestion,
  createQuestion,
  uploadQuestionFile,
  bulkUploadQuestions,
  downloadQuestionTemplate,
  //testQuestion,
} from '../api/api';

const useQuestionsStore = create((set, get) => ({
  questions: [],
  loading: false,
  error: null,
  filters: {
    type: '',
    language: '',
    search: '',
    active: undefined,
  },

  setFilters: (filters) => set({ filters }),

  loadQuestions: async () => {
    set({ loading: true, error: null });
    try {
      const { filters } = get();
      const data = await fetchTeacherQuestions(filters);
      set({ questions: data, error: null });
    } catch (err) {
      set({ error: 'Failed to load questions' });
    } finally {
      set({ loading: false });
    }
  },

  getQuestion: async (id) => {
    try {
      return await getTeacherQuestion(id);
    } catch (err) {
      set({ error: 'Failed to fetch question' });
      return null;
    }
  },

  deleteQuestion: async (id) => {
    try {
      await deleteQuestion(id);
      await get().loadQuestions();
    } catch (err) {
      set({ error: 'Failed to delete question' });
      throw err;
    }
  },

  updateQuestion: async (id, data) => {
    try {
      return await updateQuestion(id, data);
    } catch (err) {
      set({ error: 'Failed to update question' });
      throw err;
    }
  },

  createQuestion: async (data) => {
    try {
      return await createQuestion(data);
    } catch (err) {
      set({ error: 'Failed to create question' });
      throw err;
    }
  },

  deleteQuestionFile: async (fileId) => {
    try {
      return await deleteQuestionFile(fileId);
    } catch (err) {
      set({ error: 'Failed to delete file' });
      throw err;
    }
  },


  uploadQuestionFile: async (questionId, file) => {
    try {
      return await uploadQuestionFile(questionId, file);
    } catch (err) {
      set({ error: 'Failed to upload file' });
      throw err;
    }
  },

  bulkUploadQuestions: async (file) => {
    set({ loading: true, error: null, uploadProgress: 'Uploading...' });
    try {
      const result = await bulkUploadQuestions(file);
      set({ uploadProgress: result.message, error: null });
      // Reload questions after successful upload
      await get().loadQuestions();
      return result;
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Failed to upload questions file';
      set({ error: errorMsg, uploadProgress: null });
      throw new Error(errorMsg);
    } finally {
      set({ loading: false });
      // Clear progress after 3 seconds
      setTimeout(() => set({ uploadProgress: null }), 3000);
    }
  },

  downloadQuestionTemplate: async () => {
    try {
      await downloadQuestionTemplate();
    } catch (err) {
      set({ error: 'Failed to download template' });
      throw err;
    }
  },

  






}));

export default useQuestionsStore;