import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { reportsAPI } from '../services/api';
import './FinancialPages.css';

const FinancialInsights = () => {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const [insights, setInsights] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchInsights();
    }, []);

    const fetchInsights = async () => {
        try {
            const response = await reportsAPI.getFinancialInsights();
            setInsights(response.data);
        } catch (err) {
            setError('Failed to load financial insights');
        } finally {
            setLoading(false);
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

    if (loading) {
        return <div className="financial-page-container"><div className="loading">Loading...</div></div>;
    }

    return (
        <div className="financial-page-container">
            <header className="dashboard-header">
                <div className="header-left">
                    <h1 className="logo">PaisaPro</h1>
                    <p style={{ margin: 0, fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)' }}>
                        Financial Insights
                    </p>
                </div>
                <div className="header-right">
                    <Link to="/dashboard" className="nav-link">Dashboard</Link>
                    <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
                </div>
            </header>

            <main className="financial-page-main">
                <div className="page-card">
                    <h2>💡 Financial Insights</h2>
                    <p className="page-description">AI-powered recommendations to improve your financial health</p>

                    {error && <div className="alert alert-error">{error}</div>}

                    {insights && (
                        <div className="insights-container">
                            <div className="insight-section">
                                <h3>⚠️ Spending Mistakes</h3>
                                {insights.spending_mistakes && insights.spending_mistakes.length > 0 ? (
                                    <ul className="unusual-expenses-list">
                                        {insights.spending_mistakes.map((mistake, index) => {
                                            const severityColors = {
                                                critical: { bg: 'rgba(220, 38, 38, 0.15)', border: 'rgba(220, 38, 38, 0.4)', text: '#ef4444' },
                                                high: { bg: 'rgba(255, 107, 107, 0.15)', border: 'rgba(255, 107, 107, 0.3)', text: '#ff6b6b' },
                                                medium: { bg: 'rgba(251, 146, 60, 0.15)', border: 'rgba(251, 146, 60, 0.3)', text: '#fb923c' }
                                            };
                                            const colors = severityColors[mistake.severity] || severityColors.medium;

                                            return (
                                                <li key={index} style={{ marginBottom: '0.75rem', padding: '0.75rem', background: colors.bg, borderRadius: '8px', border: `1px solid ${colors.border}` }}>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                                                        <div style={{ fontWeight: '600', color: colors.text, fontSize: '0.85rem', textTransform: 'uppercase' }}>
                                                            {mistake.type.replace('_', ' ')}
                                                        </div>
                                                        <div style={{ fontWeight: '700', color: colors.text, fontSize: '1.1rem' }}>
                                                            ${mistake.amount.toFixed(2)}
                                                        </div>
                                                    </div>
                                                    <div style={{ fontSize: '0.9rem', color: 'rgba(255,255,255,0.9)', lineHeight: '1.5' }}>
                                                        {mistake.description}
                                                    </div>
                                                </li>
                                            );
                                        })}
                                    </ul>
                                ) : (
                                    <p style={{ color: 'rgba(255,255,255,0.7)' }}>No spending mistakes detected in your recent activity. Keep up the good financial habits!</p>
                                )}
                            </div>

                            <div className="insight-section">
                                <h3>💡 Corrective Financial Actions</h3>
                                {insights.corrective_actions && insights.corrective_actions.length > 0 ? (
                                    <ul className="improvement-list" style={{ listStyle: 'none', padding: 0 }}>
                                        {insights.corrective_actions.map((action, index) => (
                                            <li key={index} style={{ marginBottom: '0.75rem', padding: '0.75rem', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.3)', color: 'rgba(255,255,255,0.9)' }}>
                                                <span style={{ color: '#60a5fa', marginRight: '0.5rem' }}>→</span>
                                                {action}
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p style={{ color: 'rgba(255,255,255,0.7)' }}>No corrective actions needed. Your spending is on track!</p>
                                )}
                            </div>

                            <div className="insight-section">
                                <h3>💰 Savings Tips</h3>
                                {insights.saving_tips && insights.saving_tips.length > 0 ? (
                                    <ul style={{ listStyle: 'none', padding: 0 }}>
                                        {insights.saving_tips.map((tip, index) => (
                                            <li key={index} style={{ marginBottom: '0.75rem', padding: '0.75rem', background: 'rgba(34, 197, 94, 0.1)', borderRadius: '8px', border: '1px solid rgba(34, 197, 94, 0.3)', color: 'rgba(255,255,255,0.9)', lineHeight: '1.6' }}>
                                                <span style={{ color: '#4ade80', marginRight: '0.5rem' }}>💡</span>
                                                {tip}
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p style={{ color: 'rgba(255,255,255,0.7)' }}>No specific saving opportunities identified from your current spending patterns.</p>
                                )}
                            </div>
                        </div>
                    )}

                    <Link to="/dashboard" className="btn btn-link" style={{ marginTop: '2rem' }}>← Back to Dashboard</Link>
                </div>
            </main>
        </div>
    );
};

export default FinancialInsights;
