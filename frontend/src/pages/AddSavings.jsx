import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { savingsAPI } from '../services/api';
import './FinancialPages.css';

const AddSavings = () => {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const [amount, setAmount] = useState('');
    const [action, setAction] = useState('add'); // 'add' or 'withdraw'
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            if (action === 'add') {
                await savingsAPI.addSavings({ amount: parseFloat(amount) });
            } else {
                await savingsAPI.withdrawSavings({ amount: parseFloat(amount) });
            }
            navigate('/dashboard');
        } catch (err) {
            setError(err.response?.data?.error || `Failed to ${action} savings`);
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
                        Manage Savings
                    </p>
                </div>
                <div className="header-right">
                    <Link to="/dashboard" className="nav-link">Dashboard</Link>
                    <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
                </div>
            </header>

            <main className="financial-page-main">
                <div className="page-card">
                    <h2>Manage Savings</h2>
                    <p className="page-description">Save money or withdraw from your savings account.</p>

                    {error && <div className="alert alert-error">{error}</div>}

                    {/* Action Selector */}
                    <div className="action-selector">
                        <button
                            type="button"
                            className={`action-btn ${action === 'add' ? 'active' : ''}`}
                            onClick={() => setAction('add')}
                        >
                            <i className="fas fa-piggy-bank"></i>
                            <span>Save Money</span>
                        </button>
                        <button
                            type="button"
                            className={`action-btn ${action === 'withdraw' ? 'active' : ''}`}
                            onClick={() => setAction('withdraw')}
                        >
                            <i className="fas fa-hand-holding-usd"></i>
                            <span>Withdraw</span>
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="financial-form">
                        <div className="form-group">
                            <label htmlFor="amount">
                                {action === 'add' ? 'Amount to Save:' : 'Amount to Withdraw:'}
                            </label>
                            <input
                                type="number"
                                id="amount"
                                step="0.01"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                placeholder={action === 'add' ? 'Enter amount to save' : 'Enter amount to withdraw'}
                                required
                            />
                        </div>

                        <div className="form-actions">
                            <button type="submit" className="btn btn-primary" disabled={loading}>
                                {loading ? 'Processing...' : (action === 'add' ? 'Save Money' : 'Withdraw Funds')}
                            </button>
                            <Link to="/dashboard" className="btn btn-link">Cancel</Link>
                        </div>
                    </form>
                </div>
            </main>
        </div>
    );
};

export default AddSavings;
