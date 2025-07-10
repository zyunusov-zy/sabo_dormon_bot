import axios from 'axios';
import getCookie from './token';

const baseURL = 'http://localhost:8000';

const axiosInstance = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Request interceptor: attach access token from cookie
axiosInstance.interceptors.request.use(
  async (config) => {
    const token = getCookie('access');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refresh = getCookie('refresh'); // ✅ читаем из cookie
        const res = await axios.post(
          `${baseURL}/api/token/refresh/`,
          { refresh },
          { withCredentials: true }
        );

        document.cookie = `access=${res.data.access}; path=/`;

        originalRequest.headers['Authorization'] = `Bearer ${res.data.access}`;

        return axiosInstance(originalRequest);
      } catch (err) {
        console.error('Refresh failed:', err);
        document.cookie = 'access=; Max-Age=0';
        document.cookie = 'refresh=; Max-Age=0';
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
