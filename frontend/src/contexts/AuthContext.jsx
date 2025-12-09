import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const response = await authAPI.getCurrentUser();
            // Only set user if we have valid user data
            if (response.data && !response.data.error) {
                setUser(response.data);
            } else {
                setUser(null);
            }
        } catch (error) {
            // Only log errors that aren't 401 (which is expected when not logged in)
            if (error.response?.status !== 401) {
                console.error('Auth check error:', error);
            }
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = async (credentials) => {
        const response = await authAPI.login(credentials);
        setUser(response.data.user);
        return response;
    };

    const signup = async (data) => {
        const response = await authAPI.signup(data);
        return response;
    };

    const logout = async () => {
        await authAPI.logout();
        setUser(null);
    };

    const value = {
        user,
        loading,
        login,
        signup,
        logout,
        checkAuth,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
