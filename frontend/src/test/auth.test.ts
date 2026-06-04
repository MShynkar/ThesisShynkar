import { describe, expect, it, beforeEach } from 'vitest';
import { useAuth } from '@/lib/auth';

describe('useAuth store', () => {
  beforeEach(() => {
    useAuth.getState().logout();
  });

  it('starts unauthenticated', () => {
    const { user, accessToken } = useAuth.getState();
    expect(user).toBeNull();
    expect(accessToken).toBeNull();
  });

  it('stores tokens on setTokens', () => {
    useAuth.getState().setTokens('access-1', 'refresh-1');
    const { accessToken, refreshToken } = useAuth.getState();
    expect(accessToken).toBe('access-1');
    expect(refreshToken).toBe('refresh-1');
  });

  it('clears state on logout', () => {
    useAuth.getState().setTokens('a', 'b');
    useAuth.getState().setUser({
      id: 'u',
      email: 'a@b.com',
      username: 'x',
      full_name: null,
      role: 'user',
      is_active: true,
      created_at: '',
    });
    useAuth.getState().logout();
    const { user, accessToken, refreshToken } = useAuth.getState();
    expect(user).toBeNull();
    expect(accessToken).toBeNull();
    expect(refreshToken).toBeNull();
  });
});
