// src/hooks/useApi.js
import { useContext } from 'react';
import { ApiContext } from '../context/ApiContext';

export const useApi = () => {
  return useContext(ApiContext);
};