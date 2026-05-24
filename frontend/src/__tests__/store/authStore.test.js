import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from '../../store/authStore';
import api from '../../api/api';

// Mock the API
vi.mock('../../api/api', () => ({
  default: {
    post: vi.fn(),
  },
  requestPasswordResetOTP: vi.fn(),
  confirmPasswordResetOTP: vi.fn(),
}));

describe('useAuthStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  it('should have correct initial state', () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('should handle successful login', async () => {
    const mockUser = { id: 1, name: 'Test User' };
    const mockToken = 'test-token';
    
    api.post.mockResolvedValueOnce({
      data: { user: mockUser, token: mockToken }
    });

    const result = await useAuthStore.getState().login({ email: 'test@test.com', password: 'password' });

    expect(result.success).toBe(true);
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual(mockUser);
    expect(state.token).toBe(mockToken);
    expect(localStorage.getItem('authToken')).toBe(mockToken);
  });

  it('should handle failed login', async () => {
    api.post.mockRejectedValueOnce({
      response: { data: { error: 'Invalid credentials' } }
    });

    const result = await useAuthStore.getState().login({ email: 'test@test.com', password: 'wrong' });

    expect(result.success).toBe(false);
    expect(result.error).toBe('Invalid credentials');
    
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.error).toBe('Invalid credentials');
  });

  it('should handle successful logout', async () => {
    // Setup authenticated state
    useAuthStore.setState({ isAuthenticated: true, user: { id: 1 }, token: 'token' });
    localStorage.setItem('authToken', 'token');
    
    api.post.mockResolvedValueOnce({});

    const result = await useAuthStore.getState().logout();

    expect(result.success).toBe(true);
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(localStorage.getItem('authToken')).toBeNull();
  });
});
