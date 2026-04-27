import axios from 'axios';

// Single entry point via the BFF Gateway
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Shared instance for all backend calls
const bffApi = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' },
    withCredentials: true,
});

// For backward compatibility with existing service files
export const authApi = bffApi;
export const predictApi = bffApi;
export const featureApi = bffApi;

// Handle 401 errors globally
const handle401 = (error: any) => {
    if (error.response?.status === 401) {
        localStorage.removeItem('user');
        window.location.href = '/login';
    }
    return Promise.reject(error);
};

bffApi.interceptors.response.use((response) => response, handle401);

export const api = bffApi;