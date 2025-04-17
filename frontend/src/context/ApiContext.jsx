/* eslint-disable react/prop-types */
// src/context/ApiContext.jsx
import { createContext} from 'react';
import { api } from '../api/api'; // Import your centralized Axios instance

const ApiContext = createContext();

export const ApiProvider = ({ children }) => {
  // Define reusable API methods with error handling
  const getData = async (endpoint) => {
    try {
      const response = await api.get(endpoint);
      return response.data;
    } catch (error) {
      console.error('Error during GET request:', error); // Log the error (or add toast notifications like toast.error)
      throw error; // Propagate the error for further handling if needed
    }
  };

  const postData = async (endpoint, data) => {
    try {
      const response = await api.post(endpoint, data);
      return response.data;
    } catch (error) {
      console.error('Error during POST request:', error); // Log the error
      throw error;
    }
  };

  const putData = async (endpoint, data) => {
    try {
      const response = await api.put(endpoint, data);
      return response.data;
    } catch (error) {
      console.error('Error during PUT request:', error); // Log the error
      throw error;
    }
  };

  const deleteData = async (endpoint) => {
    try {
      const response = await api.delete(endpoint);
      return response.data;
    } catch (error) {
      console.error('Error during DELETE request:', error); // Log the error
      throw error;
    }
  };

  return (
    <ApiContext.Provider value={{ getData, postData, putData, deleteData }}>
      {children}
    </ApiContext.Provider>
  );
};



// // src/context/ApiContext.js
// import  { createContext, useContext } from 'react';
// import { api } from '../api/api'; // Import your centralized Axios instance

// const ApiContext = createContext();

// export const ApiProvider = ({ children }) => {
//   // Define reusable API methods
//   const getData = async (endpoint) => {
//     const response = await api.get(endpoint);
//     return response.data;
//   };

//   const postData = async (endpoint, data) => {
//     const response = await api.post(endpoint, data);
//     return response.data;
//   };

//   const putData = async (endpoint, data) => {
//     const response = await api.put(endpoint, data);
//     return response.data;
//   };

//   const deleteData = async (endpoint) => {
//     const response = await api.delete(endpoint);
//     return response.data;
//   };

//   return (
//     <ApiContext.Provider value={{ getData, postData, putData, deleteData }}>
//       {children}
//     </ApiContext.Provider>
//   );
// };

// // Custom hook to use the API methods
// export const useApi = () => {
//   return useContext(ApiContext);
// };