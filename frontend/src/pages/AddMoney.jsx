import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { accountAPI } from '../services/api';
import './FinancialPages.css';

const AddMoney = () => {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        amount: '',
        money_type: 'salary',
        description: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const moneyTypes = [
        { value: 'salary', label: 'Salary' },
        { value: 'bonus', label: 'Bonus' },
        { value: 'investment', label: 'Investment' },
        { value: 'other', label: 'Other' }
    ];

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await accountAPI.addMoney(formData);
            navigate('/dashboard');
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to add money');
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
                        Add Money
                    </p>
                </div>
                <div className="header-right">
                    <Link to="/dashboard" className="nav-link">Dashboard</Link>
                    <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
                </div>
            </header>

            <main className="financial-page-main">
                <div className="page-card">
                    <h2>Add Money to Balance</h2>
                    <p className="page-description">Add money from salary, investment, bonus, or other sources.</p>

                    {error && <div className="alert alert-error">{error}</div>}

                    <form onSubmit={handleSubmit} className="financial-form">
                        <div className="form-group">
                            <label htmlFor="amount">Amount:</label>
                            <input
                                type="number"
                                id="amount"
                                name="amount"
                                step="1"
                                min="0"
                                value={formData.amount}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="money_type">Money type:</label>
                            <select
                                id="money_type"
                                name="money_type"
                                value={formData.money_type}
                                onChange={handleChange}
                                required
                                style={{ color: '#fff', backgroundColor: '#2d2d2d' }}
                            >
                                {moneyTypes.map(type => (
                                    <option key={type.value} value={type.value} style={{ color: '#fff', backgroundColor: '#2d2d2d' }}>{type.label}</option>
                                ))}
                            </select>
                        </div>

                        <div className="form-group">
                            <label htmlFor="description">Description:</label>
                            <textarea
                                id="description"
                                name="description"
                                value={formData.description}
                                onChange={handleChange}
                                placeholder="Optional description"
                                rows="3"
                            />
                        </div>

                        <div className="form-actions">
                            <button type="submit" className="btn btn-primary" disabled={loading}>
                                {loading ? 'Adding...' : 'Add Money'}
                            </button>
                            <Link to="/dashboard" className="btn btn-link">Cancel</Link>
                        </div>
                    </form>
                </div>
            </main>
        </div>
    );
};

export default AddMoney;
