// src/api.js

import axios from 'axios';

const api = axios.create({
  baseURL:import.meta.env.VITE_API_BASE_URL,
  withCredentials: true,
});

// Example interceptor for handling auth token headers (if added later)
api.interceptors.request.use(
  (config) => {
    // const token = localStorage.getItem('access_token');
    // if (token) config.headers['Authorization'] = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// Global error handler (optional)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Optionally redirect or show login prompt
    }
    return Promise.reject(error);
  }
);

export { api };

// Fetch CSRF token explicitly
export const getCsrfToken = async () => {
  await api.get('get-csrf/');
};















