// src/api.js
import axios from 'axios';

export const api = axios.create({
  baseURL: '/api/',
  withCredentials: true, // Required for CSRF cookie
});

// Helper to get CSRF token
export const getCsrfToken = async () => {
  await api.get('get-csrf/'); // Sets CSRF cookie
};