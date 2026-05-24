import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useQuizGradingStore } from '../../store/quizGradeStore';
import * as api from '../../api/api';

// Mock the API calls
vi.mock('../../api/api', () => ({
  fetchTeacherQuizzesGrouped: vi.fn(),
  getGradingCourses: vi.fn(),
  getQuizUsers: vi.fn(),
  getUserAttempts: vi.fn(),
  gradeUserAttempt: vi.fn(),
}));

describe('useQuizGradingStore', () => {
  beforeEach(() => {
    useQuizGradingStore.getState().reset();
    vi.clearAllMocks();
  });

  it('should have correct initial state', () => {
    const state = useQuizGradingStore.getState();
    expect(state.courses).toEqual([]);
    expect(state.selectedCourse).toBeNull();
    expect(state.loading.courses).toBe(false);
  });

  it('should load teacher quizzes successfully', async () => {
    const mockQuizzes = [{ course_id: 1, course_name: 'Math', quizzes: [] }];
    api.fetchTeacherQuizzesGrouped.mockResolvedValueOnce(mockQuizzes);

    const result = await useQuizGradingStore.getState().loadTeacherQuizzes();
    
    expect(result).toEqual(mockQuizzes);
    const state = useQuizGradingStore.getState();
    expect(state.quizzesByCourse).toEqual(mockQuizzes);
    expect(state.loadingQuizzes).toBe(false);
  });

  it('should handle failure to load teacher quizzes', async () => {
    api.fetchTeacherQuizzesGrouped.mockRejectedValueOnce({
      response: { data: { error: 'Failed' } }
    });

    await expect(useQuizGradingStore.getState().loadTeacherQuizzes()).rejects.toThrow();
    
    const state = useQuizGradingStore.getState();
    expect(state.quizzesError).toBe('Failed');
    expect(state.loadingQuizzes).toBe(false);
  });

  it('should manipulate selection states correctly', () => {
    const mockCourse = { id: 1, name: 'Science' };
    const mockModule = { id: 2, name: 'Physics' };
    
    useQuizGradingStore.getState().selectCourse(mockCourse);
    expect(useQuizGradingStore.getState().selectedCourse).toEqual(mockCourse);
    
    useQuizGradingStore.getState().selectModule(mockModule);
    expect(useQuizGradingStore.getState().selectedModule).toEqual(mockModule);

    useQuizGradingStore.getState().clearCourse();
    expect(useQuizGradingStore.getState().selectedCourse).toBeNull();
    expect(useQuizGradingStore.getState().selectedModule).toBeNull();
  });

  it('should get correct quiz stats', () => {
    useQuizGradingStore.setState({
      quizzesByCourse: [
        {
          course_id: 1,
          quizzes: [
            { id: 1, is_exercise: false, active: true },
            { id: 2, is_exercise: true, active: false }
          ]
        }
      ]
    });

    const stats = useQuizGradingStore.getState().getQuizStats();
    expect(stats.totalQuizzes).toBe(1);
    expect(stats.totalExercises).toBe(1);
    expect(stats.totalActive).toBe(1);
  });
});
