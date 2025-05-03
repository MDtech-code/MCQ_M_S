// // src/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true, // Ensures cookies are sent automatically
});

// Function to fetch CSRF Token & store it in Axios defaults
export const fetchCsrfToken = async () => {
  try {
    const response = await api.get('/get-csrf/');
    api.defaults.headers['X-CSRFToken'] = response.data.csrf_token; // Store CSRF token globally
  } catch (error) {
    console.error('Error fetching CSRF token:', error);
  }
};

// Global interceptor to attach CSRF Token automatically
api.interceptors.request.use(
  async (config) => {
    if (!api.defaults.headers['X-CSRFToken']) {
      await fetchCsrfToken(); // Ensure CSRF token is set before sending requests
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export { api };

// import axios from 'axios';

// const api = axios.create({
//   baseURL:import.meta.env.VITE_API_BASE_URL,
//   withCredentials: true,
// });

// // Example interceptor for handling auth token headers
// api.interceptors.request.use(
//   (config) => {
//     const csrfToken = document.cookie
//     .split('; ')
//     .find(row => row.startsWith('csrftoken='))
//     ?.split('=')[1];
//   config.headers['X-CSRFToken'] = csrfToken;
//     return config;
//   },
//   (error) => Promise.reject(error)
// );



// export { api };

// // Fetch CSRF token explicitly
// export const getCsrfToken = async () => {

//   await api.get('get-csrf/');
// };






// // Global error handler (optional)
// api.interceptors.response.use(
//   (response) => response,
//   (error) => {
//     if (error.response?.status === 401) {
//       // Optionally redirect or show login prompt
//     }
//     return Promise.reject(error);
//   }
// );










