import { describe, it, expect, beforeEach, vi } from 'vitest';
import useManageCourseStore from '../../store/manageCourseStore';
import * as api from '../../api/api';

vi.mock('../../api/api', () => ({
  getTeacherCourse: vi.fn(),
  getCourseModules: vi.fn(),
  getCourseAnalytics: vi.fn(),
  createModule: vi.fn(),
}));

describe('useManageCourseStore', () => {
  beforeEach(() => {
    // Reset Zustand store state
    useManageCourseStore.setState({
      activeTab: 'Modules',
      course: null,
      modules: [],
      loading: true,
      error: null,
      analytics: null,
      loadingAnalytics: false,
    });
    vi.clearAllMocks();
  });

  it('should possess correct initial state', () => {
    const state = useManageCourseStore.getState();
    expect(state.course).toBeNull();
    expect(state.modules).toEqual([]);
    expect(state.loading).toBe(true);
  });

  it('should load course data correctly', async () => {
    const mockCourse = { id: 1, name: 'Chemistry' };
    const mockModules = [{ id: 10, name: 'Module 1' }];
    
    api.getTeacherCourse.mockResolvedValueOnce(mockCourse);
    api.getCourseModules.mockResolvedValueOnce(mockModules);

    await useManageCourseStore.getState().loadCourseData(1);
    
    const state = useManageCourseStore.getState();
    expect(state.course).toEqual(mockCourse);
    expect(state.modules).toEqual(mockModules);
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('should load course data with modules embedded correctly', async () => {
    const mockCourse = { id: 1, name: 'Physics', modules: [{ id: 11, name: 'Module A' }] };
    
    api.getTeacherCourse.mockResolvedValueOnce(mockCourse);

    await useManageCourseStore.getState().loadCourseData(1);
    
    const state = useManageCourseStore.getState();
    expect(state.course).toEqual(mockCourse);
    expect(state.modules).toEqual(mockCourse.modules);
    expect(api.getCourseModules).not.toHaveBeenCalled();
    expect(state.loading).toBe(false);
  });

  it('should set error if course data load fails', async () => {
    api.getTeacherCourse.mockRejectedValueOnce(new Error('Network Error'));

    await useManageCourseStore.getState().loadCourseData(1);
    
    const state = useManageCourseStore.getState();
    expect(state.course).toBeNull();
    expect(state.error).toBe('Network Error');
    expect(state.loading).toBe(false);
  });

  it('should load analytics correctly', async () => {
    const mockAnalytics = { total_students: 50 };
    api.getCourseAnalytics.mockResolvedValueOnce(mockAnalytics);

    await useManageCourseStore.getState().loadAnalytics(1);

    const state = useManageCourseStore.getState();
    expect(state.analytics).toEqual(mockAnalytics);
    expect(state.loadingAnalytics).toBe(false);
  });

  it('should open create module form with correct defaults', () => {
    const currentModules = [{ id: 1 }, { id: 2 }];
    useManageCourseStore.getState().openCreateModule(currentModules);

    const state = useManageCourseStore.getState();
    expect(state.editingModule).toBeNull();
    expect(state.showModuleForm).toBe(true);
    expect(state.moduleFormData.order).toBe(3); // Next order
  });

  it('should handle tab updates', () => {
    useManageCourseStore.getState().setActiveTab('Analytics');
    expect(useManageCourseStore.getState().activeTab).toBe('Analytics');
  });
});
