import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true, // Important for session-based auth
});

// Fetch CSRF token on load
const getCsrfToken = () => {
    const csrfToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return csrfToken;
};

// Ensure CSRF token is available
(async () => {
    if (!getCsrfToken()) {
        try {
            await axios.get('/api/csrf/', { withCredentials: true });
        } catch (error) {
            console.error('Failed to fetch CSRF token', error);
        }
    }
})();

// Add CSRF token to requests
api.interceptors.request.use((config) => {
    const csrfToken = getCsrfToken();

    if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
    }

    return config;
});

// Handle authentication errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // Only redirect on 401 if it's not the current-user check and not already on auth pages
        const isAuthCheck = error.config?.url?.includes('/current-user/');
        const isAuthPage = window.location.pathname.includes('/login') ||
            window.location.pathname.includes('/signup') ||
            window.location.pathname === '/';

        if (error.response?.status === 401 && !isAuthCheck && !isAuthPage) {
            // Redirect to login only for protected API calls
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Auth API
export const authAPI = {
    signup: (data) => api.post('/signup/', data),
    login: (data) => api.post('/login/', data),
    logout: () => api.post('/logout/'),
    verifyOTP: (data) => api.post('/verify-otp/', data),
    resendOTP: (data) => api.post('/resend-otp/', data),
    forgotPassword: (data) => api.post('/forgot-password/', data),
    verifyPasswordResetOTP: (data) => api.post('/verify-password-reset-otp/', data),
    setNewPassword: (data) => api.post('/set-new-password/', data),
    getCurrentUser: () => api.get('/current-user/'),
    updateProfile: (data) => api.put('/update-profile/', data),
    verifyEmailChange: (data) => api.post('/verify-email-change/', data),
    deleteAccount: () => api.delete('/delete-account/'),
};

// Account API
export const accountAPI = {
    getAccount: () => api.get('/account/'),
    updateAccount: (data) => api.put('/account/', data),
    updateIncome: (data) => api.post('/income-setup/', data),
    addMoney: (data) => api.post('/add-money/', data),
    getDashboard: () => api.get('/dashboard/'),
};

// Expense API
export const expenseAPI = {
    getExpenses: (params) => api.get('/expenses/', { params }),
    addExpense: (data) => api.post('/expenses/', data),
    deleteExpense: (id) => api.delete(`/expenses/${id}/`),
    getExpenseCategories: () => api.get('/expense-categories/'),
};

// Savings API
export const savingsAPI = {
    getSavings: () => api.get('/savings/'),
    addSavings: (data) => api.post('/add-savings/', data),
    withdrawSavings: (data) => api.post('/withdraw-savings/', data),
};

// Budget API
export const budgetAPI = {
    getBudgetStatus: () => api.get('/budget/'),
    updateBudgetLimit: (data) => api.post('/budget/', data),
};

// Reports API
export const reportsAPI = {
    getSpendingReport: (params) => api.get('/spending-report/', { params }),
    getFinancialInsights: () => api.get('/financial-insights/'),
};

// Chatbot API
export const chatbotAPI = {
    sendMessage: (data) => api.post('/chatbot/', data),
};

export default api;
