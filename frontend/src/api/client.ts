import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { useAuth } from '../lib/auth';

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = useAuth.getState().accessToken;
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Refresh-on-401: serialize refresh attempts so we don't fire N parallel refreshes
// when a burst of queries all hit 401 at once.
let refreshing: Promise<string | null> | null = null;

async function refresh(): Promise<string | null> {
  const { refreshToken, setTokens, logout } = useAuth.getState();
  if (!refreshToken) {
    logout();
    return null;
  }
  try {
    const res = await axios.post(`${API_BASE}/auth/refresh`, { refresh_token: refreshToken });
    setTokens(res.data.access_token, res.data.refresh_token);
    return res.data.access_token as string;
  } catch {
    logout();
    return null;
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retried?: boolean };
    // Don't try to refresh the refresh endpoint itself
    if (
      error.response?.status === 401 &&
      original &&
      !original._retried &&
      !original.url?.includes('/auth/refresh') &&
      !original.url?.includes('/auth/login')
    ) {
      original._retried = true;
      if (!refreshing) refreshing = refresh();
      const newToken = await refreshing;
      refreshing = null;
      if (newToken) {
        original.headers = original.headers ?? {};
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      }
    }
    return Promise.reject(error);
  }
);
