import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import ScrollToTop from './components/ScrollToTop'

// Auth Pages
import Home from './pages/Home'
import Login from './pages/Login'
import Signup from './pages/Signup'
import VerifyOTP from './pages/VerifyOTP'
import ForgotPassword from './pages/ForgotPassword'
import VerifyPasswordResetOTP from './pages/VerifyPasswordResetOTP';
import SetNewPassword from './pages/SetNewPassword';

// Dashboard Pages (placeholder for now)
import { Dashboard, ProfileSettings, IncomeSetup, AddExpense, AddMoney, AddSavings, WithdrawSavings, BudgetStatus, SpendingReport, FinancialInsights, Chatbot } from './pages/placeholder.jsx'
import PriceComparison from './pages/PriceComparison'
import SentimentAnalysis from './pages/SentimentAnalysis'
import ShoppingList from './pages/ShoppingList'
import MyShoppingLists from './pages/MyShoppingLists'
import OptimizedCart from './pages/OptimizedCart'

// Info Pages
import Features from './pages/Features'
import Security from './pages/Security'
import AboutUs from './pages/AboutUs'
import Contact from './pages/Contact'
import Support from './pages/Support'

import './App.css'

function App() {
    return (
        <Router>
            <ScrollToTop />
            <AuthProvider>
                <Routes>
                    {/* Public Routes */}
                    <Route path="/" element={<Home />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/signup" element={<Signup />} />
                    <Route path="/verify-otp" element={<VerifyOTP />} />
                    <Route path="/forgot-password" element={<ForgotPassword />} />
                    <Route path="/verify-password-reset-otp" element={<VerifyPasswordResetOTP />} />
                    <Route path="/set-new-password" element={<SetNewPassword />} />

                    {/* Protected Routes */}
                    <Route path="/dashboard" element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    } />
                    <Route path="/profile-settings" element={
                        <ProtectedRoute>
                            <ProfileSettings />
                        </ProtectedRoute>
                    } />
                    <Route path="/income-setup" element={
                        <ProtectedRoute>
                            <IncomeSetup />
                        </ProtectedRoute>
                    } />
                    <Route path="/add-expense" element={
                        <ProtectedRoute>
                            <AddExpense />
                        </ProtectedRoute>
                    } />
                    <Route path="/add-money" element={
                        <ProtectedRoute>
                            <AddMoney />
                        </ProtectedRoute>
                    } />
                    <Route path="/add-savings" element={
                        <ProtectedRoute>
                            <AddSavings />
                        </ProtectedRoute>
                    } />
                    <Route path="/withdraw-savings" element={
                        <ProtectedRoute>
                            <WithdrawSavings />
                        </ProtectedRoute>
                    } />
                    <Route path="/budget-status" element={
                        <ProtectedRoute>
                            <BudgetStatus />
                        </ProtectedRoute>
                    } />
                    <Route path="/spending-report" element={
                        <ProtectedRoute>
                            <SpendingReport />
                        </ProtectedRoute>
                    } />
                    <Route path="/financial-insights" element={
                        <ProtectedRoute>
                            <FinancialInsights />
                        </ProtectedRoute>
                    } />
                    <Route path="/chatbot" element={
                        <ProtectedRoute>
                            <Chatbot />
                        </ProtectedRoute>
                    } />
                    <Route path="/price-comparison" element={
                        <ProtectedRoute>
                            <PriceComparison />
                        </ProtectedRoute>
                    } />
                    <Route path="/sentiment-analysis" element={
                        <ProtectedRoute>
                            <SentimentAnalysis />
                        </ProtectedRoute>
                    } />
                    <Route path="/shopping-list" element={
                        <ProtectedRoute>
                            <ShoppingList />
                        </ProtectedRoute>
                    } />
                    <Route path="/my-shopping-lists" element={
                        <ProtectedRoute>
                            <MyShoppingLists />
                        </ProtectedRoute>
                    } />
                    <Route path="/optimized-cart/:listId" element={
                        <ProtectedRoute>
                            <OptimizedCart />
                        </ProtectedRoute>
                    } />

                    {/* Info Pages */}
                    <Route path="/features" element={<Features />} />
                    <Route path="/security" element={<Security />} />
                    <Route path="/about" element={<AboutUs />} />
                    <Route path="/contact" element={<Contact />} />
                    <Route path="/support" element={<Support />} />

                    {/* Catch all */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </AuthProvider>
        </Router>
    )
}

export default App
