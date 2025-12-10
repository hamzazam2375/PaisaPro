import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { savingsAPI } from '../services/api';
import './FinancialPages.css';

const WithdrawSavings = () => {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const [amount, setAmount] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await savingsAPI.withdrawSavings({ amount: parseFloat(amount) });
            navigate('/dashboard');
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to withdraw from savings');
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
                        Withdraw Savings
                    </p>
                </div>
                <div className="header-right">
                    <Link to="/dashboard" className="nav-link">Dashboard</Link>
                    <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
                </div>
            </header>

            <main className="financial-page-main">
                <div className="page-card">
                    <h2>Withdraw from Savings</h2>
                    <p className="page-description">Transfer money from savings back to your current balance.</p>

                    {error && <div className="alert alert-error">{error}</div>}

                    <form onSubmit={handleSubmit} className="financial-form">
                        <div className="form-group">
                            <label htmlFor="amount">Amount:</label>
                            <input
                                type="number"
                                id="amount"
                                step="1"
                                min="0"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                required
                            />
                        </div>

                        <div className="form-actions">
                            <button type="submit" className="btn btn-primary" disabled={loading}>
                                {loading ? 'Withdrawing...' : 'Withdraw'}
                            </button>
                            <Link to="/dashboard" className="btn btn-link">Cancel</Link>
                        </div>
                    </form>
                </div>
            </main>
        </div>
    );
};

export default WithdrawSavings;
