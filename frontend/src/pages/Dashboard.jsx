import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { accountAPI } from '../services/api';
import NotificationBell from '../components/NotificationBell';
import './Dashboard.css';

const Dashboard = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [account, setAccount] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [showIncomeSetup, setShowIncomeSetup] = useState(false);
    const [monthlyIncome, setMonthlyIncome] = useState('');
    const [isFirstLogin, setIsFirstLogin] = useState(false);

    useEffect(() => {
        // Check if this is user's first login
        if (user?.is_first_login) {
            setIsFirstLogin(true);
        }
        fetchDashboardData();
    }, [user]);

    const fetchDashboardData = async () => {
        try {
            const response = await accountAPI.getAccount();
            setAccount(response.data);

            // Show income setup if monthly income is 0
            if (response.data.monthly_income == 0) {
                setShowIncomeSetup(true);
            }
        } catch (err) {
            setError('Failed to load dashboard data');
        } finally {
            setLoading(false);
        }
    };

    const handleIncomeSetup = async (e) => {
        e.preventDefault();
        try {
            await accountAPI.updateIncome({ monthly_income: monthlyIncome });
            setShowIncomeSetup(false);
            setIsFirstLogin(false);
            fetchDashboardData();
        } catch (err) {
            setError('Failed to update income');
        }
    };

    const handleSkipIncome = () => {
        setShowIncomeSetup(false);
        setIsFirstLogin(false);
    };

    const handleLogout = async () => {
        try {
            await logout();
            navigate('/');
        } catch (err) {
            console.error('Logout failed', err);
        }
    };

    if (loading) {
        return (
            <div className="dashboard-container">
                <div className="loading">Loading...</div>
            </div>
        );
    }

    const greeting = isFirstLogin ? 'Welcome' : 'Welcome back';
    const today = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

    return (
        <div className="dashboard-container theme-enabled">
            {/* Navigation matching original template */}
            <nav className="navbar navbar-expand-lg navbar-dark">
                <div className="container-fluid">
                    <div>
                        <Link to="/" className="navbar-brand">PaisaPro</Link>
                        <p style={{ margin: 0, fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)', paddingLeft: '0.25rem' }}>
                            Dashboard
                        </p>
                    </div>
                    <div className="d-flex align-items-center gap-3">
                        <NotificationBell />
                        <span className="text-light me-3">{user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : user?.username}</span>
                        <Link to="/profile-settings" className="btn btn-sm me-2" style={{
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            color: '#fff',
                            backgroundColor: 'transparent',
                            transition: 'all 0.3s ease'
                        }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.5)';
                                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                                e.currentTarget.style.boxShadow = '0 0 0 3px rgba(255, 255, 255, 0.05)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                                e.currentTarget.style.backgroundColor = 'transparent';
                                e.currentTarget.style.boxShadow = 'none';
                            }}>
                            <i className="fas fa-user me-1"></i>Profile
                        </Link>
                        <button onClick={handleLogout} className="btn btn-sm" style={{
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            color: '#fff',
                            backgroundColor: 'transparent',
                            transition: 'all 0.3s ease'
                        }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.5)';
                                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                                e.currentTarget.style.boxShadow = '0 0 0 3px rgba(255, 255, 255, 0.05)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                                e.currentTarget.style.backgroundColor = 'transparent';
                                e.currentTarget.style.boxShadow = 'none';
                            }}>
                            <i className="fas fa-sign-out-alt me-1"></i>Logout
                        </button>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <div className="container-fluid mt-4">
                {/* Dashboard Header */}
                <div className="dashboard-header text-center mb-5">
                    <h1 className="display-3 mb-3" style={{ fontWeight: '700', color: '#fff' }}>
                        {greeting}, {user?.first_name || user?.username}! 👋
                    </h1>
                    <p className="lead" style={{ fontSize: '1.2rem', color: 'rgba(255,255,255,0.8)' }}>{today}</p>
                </div>

                {error && <div className="alert alert-danger">{error}</div>}

                {/* Income Setup Modal */}
                {showIncomeSetup && (
                    <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
                        <div className="modal-dialog modal-dialog-centered">
                            <div className="modal-content">
                                <div className="modal-header">
                                    <h5 className="modal-title">Set Your Monthly Income</h5>
                                </div>
                                <div className="modal-body">
                                    <p>Let's start by setting up your monthly income to track your finances better.</p>
                                    <form onSubmit={handleIncomeSetup}>
                                        <div className="mb-3">
                                            <input
                                                type="number"
                                                step="0.01"
                                                className="form-control"
                                                placeholder="Enter monthly income"
                                                value={monthlyIncome}
                                                onChange={(e) => setMonthlyIncome(e.target.value)}
                                                required
                                            />
                                        </div>
                                        <div className="d-flex gap-2">
                                            <button type="submit" className="btn btn-primary flex-fill">Save Income</button>
                                            <button type="button" onClick={handleSkipIncome} className="btn btn-secondary flex-fill">Skip for Now</button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Financial Overview Cards - Bootstrap Grid */}
                <div className="row g-4 mb-5">
                    <div className="col-lg-3 col-md-6" style={{ animationDelay: '0.1s' }}>
                        <div className="financial-card income-card">
                            <div className="card-icon-wrapper income-icon">
                                <i className="fas fa-money-bill-wave"></i>
                            </div>
                            <div className="card-details">
                                <div className="metric-label">Monthly Income</div>
                                <div className="metric-value">${parseFloat(account?.monthly_income || 0).toFixed(2)}</div>
                            </div>
                        </div>
                    </div>

                    <div className="col-lg-3 col-md-6" style={{ animationDelay: '0.2s' }}>
                        <div className="financial-card balance-card">
                            <div className="card-icon-wrapper balance-icon">
                                <i className="fas fa-wallet"></i>
                            </div>
                            <div className="card-details">
                                <div className="metric-label">Available Balance</div>
                                <div className="metric-value">${parseFloat(account?.available_balance || 0).toFixed(2)}</div>
                            </div>
                        </div>
                    </div>

                    <div className="col-lg-3 col-md-6" style={{ animationDelay: '0.3s' }}>
                        <div className="financial-card expenses-card">
                            <div className="card-icon-wrapper expenses-icon">
                                <i className="fas fa-receipt"></i>
                            </div>
                            <div className="card-details">
                                <div className="metric-label">Total Expenses</div>
                                <div className="metric-value">${parseFloat(account?.total_expenses || 0).toFixed(2)}</div>
                            </div>
                        </div>
                    </div>

                    <div className="col-lg-3 col-md-6" style={{ animationDelay: '0.4s' }}>
                        <div className="financial-card savings-card">
                            <div className="card-icon-wrapper savings-icon">
                                <i className="fas fa-piggy-bank"></i>
                            </div>
                            <div className="card-details">
                                <div className="metric-label">Savings</div>
                                <div className="metric-value">${parseFloat(account?.savings_balance || 0).toFixed(2)}</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* AI Financial Assistant - Featured Section */}
                <div className="ai-assistant-featured mb-5">
                    <div className="ai-assistant-card">
                        <div className="ai-assistant-content">
                            <div className="ai-icon-wrapper">
                                <i className="fas fa-robot"></i>
                            </div>
                            <div className="ai-text">
                                <h3>AI Financial Advisor</h3>
                                <p>Get instant answers to your financial questions, personalized advice, and smart recommendations powered by advanced AI</p>
                            </div>
                        </div>
                        <Link to="/chatbot" className="btn ai-assistant-btn">
                            <span>Start Conversation</span>
                            <i className="fas fa-arrow-right ms-2"></i>
                        </Link>
                    </div>
                </div>

                {/* Quick Actions Section */}
                <div className="dashboard-widget">
                    <h3 className="widget-title mb-4">Quick Actions</h3>
                    <div className="row g-3">
                        <div className="col-lg-3 col-md-4 col-sm-6">
                            <Link to="/add-money" className="btn quick-action-btn w-100">
                                <i className="fas fa-plus-circle d-block mb-2" style={{ fontSize: '2rem' }}></i>
                                <span>Add Money</span>
                            </Link>
                        </div>
                        <div className="col-lg-3 col-md-4 col-sm-6">
                            <Link to="/add-expense" className="btn quick-action-btn w-100">
                                <i className="fas fa-shopping-cart d-block mb-2" style={{ fontSize: '2rem' }}></i>
                                <span>Log Expense</span>
                            </Link>
                        </div>
                        <div className="col-lg-3 col-md-4 col-sm-6">
                            <Link to="/add-savings" className="btn quick-action-btn w-100">
                                <i className="fas fa-piggy-bank d-block mb-2" style={{ fontSize: '2rem' }}></i>
                                <span>Manage Savings</span>
                            </Link>
                        </div>
                        <div className="col-lg-3 col-md-4 col-sm-6">
                            <Link to="/budget-status" className="btn quick-action-btn w-100">
                                <i className="fas fa-chart-pie d-block mb-2" style={{ fontSize: '2rem' }}></i>
                                <span>Budget Overview</span>
                            </Link>
                        </div>
                    </div>
                </div>

                {/* Analytics & Reports Section */}
                <div className="dashboard-widget mt-4">
                    <h3 className="widget-title mb-4">Analytics & Reports</h3>
                    <div className="row g-3">
                        <div className="col-lg-6 col-md-6">
                            <Link to="/spending-report" className="btn analytics-btn w-100">
                                <i className="fas fa-chart-bar d-block mb-2" style={{ fontSize: '2rem' }}></i>
                                <span>Spending Analytics</span>
                            </Link>
                        </div>
                        <div className="col-lg-6 col-md-6">
                            <Link to="/financial-insights" className="btn analytics-btn w-100">
                                <i className="fas fa-lightbulb d-block mb-2" style={{ fontSize: '2rem' }}></i>
                                <span>Financial Insights</span>
                            </Link>
                        </div>
                    </div>
                </div>

                {/* Market Intelligence Section */}
                <div className="dashboard-widget mt-4">
                    <h3 className="widget-title mb-4">Market Intelligence</h3>
                    <div className="row g-3">
                        <div className="col-lg-6 col-md-6">
                            <Link to="/price-comparison" className="btn market-intelligence-btn w-100">
                                <i className="fas fa-tags d-block mb-2" style={{ fontSize: '2rem' }}></i>
                                <span>Price Comparison</span>
                                <small className="d-block mt-2" style={{ opacity: 0.8 }}>Find the best deals and compare prices</small>
                            </Link>
                        </div>
                        <div className="col-lg-6 col-md-6">
                            <Link to="/sentiment-analysis" className="btn market-intelligence-btn w-100">
                                <i className="fas fa-chart-line d-block mb-2" style={{ fontSize: '2rem' }}></i>
                                <span>Market Sentiment</span>
                                <small className="d-block mt-2" style={{ opacity: 0.8 }}>AI-powered company analysis with real-time market sentiment</small>
                            </Link>
                        </div>
                        <div className="col-lg-6 col-md-6">
                            <Link to="/shopping-list" className="btn market-intelligence-btn w-100">
                                <i className="fas fa-list-ul d-block mb-2" style={{ fontSize: '2rem' }}></i>
                                <span>Shopping List</span>
                                <small className="d-block mt-2" style={{ opacity: 0.8 }}>Create and manage your shopping lists</small>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
