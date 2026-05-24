import { create } from 'zustand';
import {
  fetchGradingSystems,
  createGradingSystem,
  updateGradingSystem,
  deleteGradingSystem,
  fetchGradingSystem,
} from '../api/api';

const useGradingSystemStore = create((set) => ({
  gradingSystems: [],
  selected: null,
  loading: false,
  error: null,

  loadGradingSystems: async () => {
    set({ loading: true, error: null });
    try {
      const data = await fetchGradingSystems();
      set({ gradingSystems: data, loading: false });
    } catch (error) {
      set({ error: 'Failed to load grading systems', loading: false });
    }
  },

  select: (gs) => set({ selected: gs }),
  clearSelected: () => set({ selected: null }),

  addGradingSystem: async (data) => {
    set({ loading: true, error: null });
    try {
      await createGradingSystem(data);
      await useGradingSystemStore.getState().loadGradingSystems();
      set({ loading: false });
    } catch (error) {
      set({ error: 'Failed to add grading system', loading: false });
    }
  },

  updateGradingSystem: async (id, data) => {
    set({ loading: true, error: null });
    try {
      await updateGradingSystem(id, data);
      await useGradingSystemStore.getState().loadGradingSystems();
      set({ loading: false });
    } catch (error) {
      set({ error: 'Failed to update grading system', loading: false });
    }
  },

  deleteGradingSystem: async (id) => {
    set({ loading: true, error: null });
    try {
      await deleteGradingSystem(id);
      await useGradingSystemStore.getState().loadGradingSystems();
      set({ loading: false });
    } catch (error) {
      set({ error: 'Failed to delete grading system', loading: false });
    }
  },
}));

export default useGradingSystemStore;