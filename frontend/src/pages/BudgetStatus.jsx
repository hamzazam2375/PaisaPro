import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './FinancialPages.css';

const BudgetStatus = () => {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const [budgetData, setBudgetData] = useState(null);
    const [newBudget, setNewBudget] = useState('');
    const [categoryBudgets, setCategoryBudgets] = useState({
        food: '',
        transportation: '',
        entertainment: '',
        utilities: '',
        healthcare: '',
        education: '',
        other: ''
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [recommendations, setRecommendations] = useState(null);
    const [showCategoryForm, setShowCategoryForm] = useState(false);

    useEffect(() => {
        fetchBudgetData();
        fetchRecommendations();
    }, []);

    const fetchBudgetData = async () => {
        try {
            const response = await fetch('/api/budget/', {
                credentials: 'include'
            });
            const data = await response.json();
            setBudgetData(data);
            setNewBudget(data.budget_limit || '');

            // Populate category budgets from response
            const catBudgets = {};
            data.category_budgets.forEach(cb => {
                catBudgets[cb.category] = cb.limit;
            });
            setCategoryBudgets(prev => ({ ...prev, ...catBudgets }));
        } catch (err) {
            setError('Failed to load budget data');
        } finally {
            setLoading(false);
        }
    };

    const fetchRecommendations = async () => {
        try {
            const response = await fetch('/api/financial-insights/', {
                credentials: 'include'
            });
            const data = await response.json();
            setRecommendations(data.budget_recommendations);
        } catch (err) {
            console.error('Failed to load recommendations', err);
        }
    };

    const handleBudgetSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError('');

        try {
            // Prepare category budgets array
            const catBudgetArray = Object.entries(categoryBudgets)
                .filter(([_, limit]) => limit && parseFloat(limit) > 0)
                .map(([category, limit]) => ({
                    category,
                    limit: parseFloat(limit)
                }));

            await fetch('/api/budget/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.cookie.split('csrftoken=')[1]?.split(';')[0]
                },
                credentials: 'include',
                body: JSON.stringify({
                    budget_limit: parseFloat(newBudget),
                    category_budgets: catBudgetArray
                })
            });

            fetchBudgetData();
            setShowCategoryForm(false);
        } catch (err) {
            setError('Failed to update budget');
        } finally {
            setSaving(false);
        }
    };

    const handleLogout = async () => {
        try {
            await logout();
            navigate('/');
        } catch (err) {
            console.error('Logout failed', err);
        }
    };

    const getCategoryIcon = (category) => {
        const icons = {
            food: '🍔',
            transportation: '🚗',
            entertainment: '🎬',
            utilities: '💡',
            healthcare: '🏥',
            education: '📚',
            other: '📦'
        };
        return icons[category] || '📦';
    };

    if (loading) {
        return <div className="financial-page-container"><div className="loading">Loading...</div></div>;
    }

    const percentUsed = budgetData?.budget_limit > 0
        ? budgetData.usage_percentage
        : 0;

    return (
        <div className="financial-page-container">
            <header className="dashboard-header">
                <div className="header-left">
                    <h1 className="logo">PaisaPro</h1>
                    <p style={{ margin: 0, fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)' }}>
                        Budget Status
                    </p>
                </div>
                <div className="header-right">
                    <Link to="/dashboard" className="nav-link">Dashboard</Link>
                    <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
                </div>
            </header>

            <main className="financial-page-main" style={{ maxWidth: '1200px' }}>
                <div className="page-card">
                    <h2>💰 Budget Overview</h2>

                    {error && <div className="alert alert-error">{error}</div>}

                    {/* Overall Budget Summary */}
                    <div className="budget-overview" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
                        <div className="budget-stat">
                            <h3>Total Monthly Budget</h3>
                            <p className="stat-value">${budgetData?.budget_limit?.toFixed(2) || '0.00'}</p>
                        </div>
                        <div className="budget-stat">
                            <h3>Total Spent</h3>
                            <p className="stat-value">${budgetData?.total_expenses?.toFixed(2) || '0.00'}</p>
                        </div>
                        <div className="budget-stat">
                            <h3>Remaining Budget</h3>
                            <p className="stat-value" style={{ color: budgetData?.remaining < 0 ? '#ff6b6b' : '#51cf66' }}>
                                ${budgetData?.remaining?.toFixed(2) || '0.00'}
                            </p>
                        </div>
                        <div className="budget-stat">
                            <h3>Budget Usage</h3>
                            <p className="stat-value">{percentUsed?.toFixed(1) || '0'}%</p>
                        </div>
                    </div>

                    {/* Overall Progress Bar */}
                    {budgetData?.budget_limit > 0 && (
                        <div className="budget-progress" style={{ marginBottom: '2rem' }}>
                            <div className="progress-bar-container">
                                <div
                                    className={`progress-bar ${budgetData.is_over_budget ? 'over-budget' : ''}`}
                                    style={{ width: `${Math.min(percentUsed, 100)}%` }}
                                ></div>
                            </div>
                            <p className="progress-text">{percentUsed?.toFixed(1)}% of total budget used</p>
                        </div>
                    )}

                    {budgetData?.is_over_budget && (
                        <div className="alert alert-error">
                            ⚠️ You have exceeded your total budget limit!
                        </div>
                    )}

                    {/* Category-wise Budget Breakdown */}
                    {budgetData?.category_budgets && budgetData.category_budgets.length > 0 && (
                        <div style={{ marginBottom: '2rem' }}>
                            <h3 style={{ marginBottom: '1.5rem', color: '#fff' }}>📊 Category-wise Budget Breakdown</h3>
                            <div style={{ display: 'grid', gap: '1.5rem' }}>
                                {budgetData.category_budgets.map((catBudget) => {
                                    const isOverBudget = catBudget.is_over_budget;
                                    const usagePercent = catBudget.usage_percentage;

                                    return (
                                        <div key={catBudget.category}
                                            className="category-budget-card"
                                            style={{
                                                background: 'rgba(255, 255, 255, 0.05)',
                                                padding: '1.5rem',
                                                borderRadius: '12px',
                                                border: `1px solid ${isOverBudget ? '#ff6b6b' : 'rgba(255, 255, 255, 0.1)'}`
                                            }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                                    <span style={{ fontSize: '1.5rem' }}>{getCategoryIcon(catBudget.category)}</span>
                                                    <div>
                                                        <h4 style={{ margin: 0, color: '#fff', textTransform: 'capitalize' }}>
                                                            {catBudget.category}
                                                        </h4>
                                                        <p style={{ margin: 0, fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)' }}>
                                                            ${catBudget.spent.toFixed(2)} / ${catBudget.limit.toFixed(2)}
                                                        </p>
                                                    </div>
                                                </div>
                                                <div style={{ textAlign: 'right' }}>
                                                    <p style={{ margin: 0, fontSize: '1.25rem', fontWeight: 'bold', color: isOverBudget ? '#ff6b6b' : '#51cf66' }}>
                                                        ${catBudget.remaining.toFixed(2)}
                                                    </p>
                                                    <p style={{ margin: 0, fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)' }}>
                                                        remaining
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Category Progress Bar */}
                                            <div className="progress-bar-container" style={{ marginBottom: '0.5rem' }}>
                                                <div
                                                    className={`progress-bar ${isOverBudget ? 'over-budget' : ''}`}
                                                    style={{ width: `${Math.min(usagePercent, 100)}%` }}
                                                ></div>
                                            </div>
                                            <p style={{ margin: 0, fontSize: '0.85rem', color: 'rgba(255,255,255,0.7)', textAlign: 'center' }}>
                                                {usagePercent.toFixed(1)}% used
                                            </p>

                                            {/* Overspend Alert */}
                                            {isOverBudget && (
                                                <div style={{ marginTop: '0.75rem', padding: '0.5rem', background: 'rgba(255, 107, 107, 0.1)', border: '1px solid rgba(255, 107, 107, 0.3)', borderRadius: '6px' }}>
                                                    <p style={{ margin: 0, fontSize: '0.85rem', color: '#ff6b6b', textAlign: 'center' }}>
                                                        ⚠️ Over budget by ${Math.abs(catBudget.remaining).toFixed(2)}
                                                    </p>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* Budget Settings Form */}
                    <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '12px' }}>
                        <h3 style={{ marginBottom: '1rem', color: '#fff' }}>⚙️ Budget Settings</h3>

                        <form onSubmit={handleBudgetSubmit} className="financial-form">
                            <div className="form-group">
                                <label htmlFor="budget">Total Monthly Budget:</label>
                                <input
                                    type="number"
                                    id="budget"
                                    step="0.01"
                                    value={newBudget}
                                    onChange={(e) => setNewBudget(e.target.value)}
                                    placeholder="0.00"
                                    required
                                />
                            </div>

                            <button
                                type="button"
                                className="btn btn-secondary"
                                onClick={() => setShowCategoryForm(!showCategoryForm)}
                                style={{ marginBottom: '1rem' }}
                            >
                                {showCategoryForm ? '▼ Hide' : '▶'} Category-wise Budget Limits
                            </button>

                            {showCategoryForm && (
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
                                    {Object.keys(categoryBudgets).map(category => (
                                        <div key={category} className="form-group">
                                            <label htmlFor={category} style={{ textTransform: 'capitalize' }}>
                                                {getCategoryIcon(category)} {category}:
                                            </label>
                                            <input
                                                type="number"
                                                id={category}
                                                step="0.01"
                                                value={categoryBudgets[category]}
                                                onChange={(e) => setCategoryBudgets(prev => ({ ...prev, [category]: e.target.value }))}
                                                placeholder="0.00"
                                            />
                                        </div>
                                    ))}
                                </div>
                            )}

                            <div className="form-actions">
                                <button type="submit" className="btn btn-primary" disabled={saving}>
                                    {saving ? 'Updating...' : 'Update Budget'}
                                </button>
                                <Link to="/dashboard" className="btn btn-link">Cancel</Link>
                            </div>
                        </form>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default BudgetStatus;
