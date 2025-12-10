import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { accountAPI } from '../services/api';
import './FinancialPages.css';

const IncomeSetup = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [monthlyIncome, setMonthlyIncome] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        fetchCurrentIncome();
    }, []);

    const fetchCurrentIncome = async () => {
        try {
            const response = await accountAPI.getAccount();
            setMonthlyIncome(response.data.monthly_income || '');
        } catch (err) {
            console.error('Failed to fetch income', err);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setLoading(true);

        try {
            await accountAPI.updateIncome({ monthly_income: monthlyIncome });
            setSuccess('Monthly income updated successfully!');
            setTimeout(() => navigate('/dashboard'), 1500);
        } catch (err) {
            setError('Failed to update income');
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

    return (
        <div className="financial-page-container">
            <header className="dashboard-header">
                <div className="header-left">
                    <h1 className="logo">PaisaPro</h1>
                    <p style={{ margin: 0, fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)' }}>
                        Income Setup
                    </p>
                </div>
                <div className="header-right">
                    <Link to="/dashboard" className="nav-link">Dashboard</Link>
                    <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
                </div>
            </header>

            <main className="financial-page-main">
                <div className="page-card">
                    <h2>Set Your Monthly Income</h2>
                    <p className="page-description">Provide your monthly income to personalize your dashboard and budget.</p>

                    {error && <div className="alert alert-error">{error}</div>}
                    {success && <div className="alert alert-success">{success}</div>}

                    <form onSubmit={handleSubmit} className="financial-form">
                        <div className="form-group">
                            <label htmlFor="monthlyIncome">Monthly income:</label>
                            <input
                                type="number"
                                id="monthlyIncome"
                                step="1"
                                min="0"
                                value={monthlyIncome}
                                onChange={(e) => setMonthlyIncome(e.target.value)}
                                placeholder="0"
                                required
                                style={{
                                    MozAppearance: 'textfield',
                                    WebkitAppearance: 'none',
                                    appearance: 'textfield'
                                }}
                            />
                            <style>{`
                                input[type=number]::-webkit-inner-spin-button,
                                input[type=number]::-webkit-outer-spin-button {
                                    -webkit-appearance: none;
                                    margin: 0;
                                }
                            `}</style>
                        </div>

                        <div className="form-actions">
                            <button type="submit" className="btn btn-primary" disabled={loading}>
                                {loading ? 'Saving...' : 'Save'}
                            </button>
                            <Link to="/dashboard" className="btn btn-link">Skip</Link>
                        </div>
                    </form>

                    <Link to="/dashboard" className="back-link">← Back to Dashboard</Link>
                </div>
            </main>
        </div>
    );
};

export default IncomeSetup;
