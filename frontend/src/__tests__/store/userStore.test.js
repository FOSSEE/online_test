import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useUserStore } from '../../store/userStore';
import api from '../../api/api';

// Mock the API
vi.mock('../../api/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  }
}));

describe('useUserStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useUserStore.setState({
      user: null,
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  it('should have correct initial state', () => {
    const state = useUserStore.getState();
    expect(state.user).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('should handle successful profile fetch', async () => {
    const mockUser = { username: 'testuser', email: 'test@test.com' };
    
    api.get.mockResolvedValueOnce({
      data: { user: mockUser }
    });

    const result = await useUserStore.getState().fetchUserProfile('testuser');

    expect(result.success).toBe(true);
    expect(result.user).toEqual(mockUser);
    
    const state = useUserStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.isLoading).toBe(false);
    expect(JSON.parse(localStorage.getItem('user'))).toEqual(mockUser);
  });

  it('should handle failed profile fetch', async () => {
    api.get.mockRejectedValueOnce({
      response: { data: { error: 'User not found' } }
    });

    const result = await useUserStore.getState().fetchUserProfile('unknown');

    expect(result.success).toBe(false);
    expect(result.error).toBe('User not found');
    
    const state = useUserStore.getState();
    expect(state.user).toBeNull();
    expect(state.error).toBe('User not found');
  });

  it('should clear user data correctly', () => {
    useUserStore.setState({ user: { id: 1 } });
    localStorage.setItem('user', JSON.stringify({ id: 1 }));

    useUserStore.getState().clearUser();

    const state = useUserStore.getState();
    expect(state.user).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
  });
});
