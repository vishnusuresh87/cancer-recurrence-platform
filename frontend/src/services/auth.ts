import { authApi } from './api';
import { LoginRequest, RegisterRequest, AuthResponse, User } from '../types';

export const authService = {
    async register(data: RegisterRequest): Promise<AuthResponse> {
        const response = await authApi.post<AuthResponse>('/api/auth/register', data);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        return response.data;
    },

    async login(data: LoginRequest): Promise<AuthResponse> {
        const response = await authApi.post<AuthResponse>('/api/auth/login', data);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        return response.data;
    },

    async getCurrentUser(): Promise<User> {
        const response = await authApi.get<User>('/api/auth/me');
        return response.data;
    },

    async logout() {
        try {
            await authApi.post('/api/auth/logout');
        } catch (e) {
            console.error("Logout API failed", e);
        } finally {
            localStorage.removeItem('user');
            window.location.href = '/login';
        }
    },

    isAuthenticated(): boolean {
        return !!localStorage.getItem('user');
    },
};


