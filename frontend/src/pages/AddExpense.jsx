import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { expenseAPI } from '../services/api';
import './FinancialPages.css';

const AddExpense = () => {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const [action, setAction] = useState('add'); // 'add' or 'remove'
    const [formData, setFormData] = useState({
        amount: '',
        category: '',
        description: '',
        expense_date: new Date().toLocaleDateString('en-CA') // Use local date in YYYY-MM-DD format
    });
    const [expenses, setExpenses] = useState([]);
    const [selectedExpenseId, setSelectedExpenseId] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (action === 'remove') {
            fetchExpenses();
        }
    }, [action]);

    const fetchExpenses = async () => {
        try {
            const response = await expenseAPI.getExpenses();
            setExpenses(response.data);
        } catch (err) {
            setError('Failed to load expenses');
        }
    };

    const categories = [
        { value: 'food', label: 'Food' },
        { value: 'transportation', label: 'Transportation' },
        { value: 'entertainment', label: 'Entertainment' },
        { value: 'utilities', label: 'Utilities' },
        { value: 'healthcare', label: 'Healthcare' },
        { value: 'education', label: 'Education' },
        { value: 'shopping', label: 'Shopping' },
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
            if (action === 'add') {
                await expenseAPI.addExpense(formData);
            } else {
                if (!selectedExpenseId) {
                    setError('Please select an expense to remove');
                    setLoading(false);
                    return;
                }
                await expenseAPI.deleteExpense(selectedExpenseId);
            }
            navigate('/dashboard');
        } catch (err) {
            setError(err.response?.data?.error || `Failed to ${action} expense`);
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
                        Manage Expenses
                    </p>
                </div>
                <div className="header-right">
                    <Link to="/dashboard" className="nav-link">Dashboard</Link>
                    <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
                </div>
            </header>

            <main className="financial-page-main">
                <div className="page-card">
                    <h2>Manage Expenses</h2>
                    <p className="page-description">Add a new expense or remove an existing one.</p>

                    {error && <div className="alert alert-error">{error}</div>}

                    {/* Action Selector */}
                    <div className="action-selector">
                        <button
                            type="button"
                            className={`action-btn ${action === 'add' ? 'active' : ''}`}
                            onClick={() => setAction('add')}
                        >
                            <i className="fas fa-plus-circle"></i>
                            <span>Add Expense</span>
                        </button>
                        <button
                            type="button"
                            className={`action-btn ${action === 'remove' ? 'active' : ''}`}
                            onClick={() => setAction('remove')}
                        >
                            <i className="fas fa-minus-circle"></i>
                            <span>Remove Expense</span>
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="financial-form">
                        {action === 'remove' && (
                            <div className="form-group">
                                <label htmlFor="expense">Select Expense to Remove:</label>
                                <select
                                    id="expense"
                                    value={selectedExpenseId}
                                    onChange={(e) => setSelectedExpenseId(e.target.value)}
                                    required
                                    style={{ color: '#fff', backgroundColor: '#2d2d2d' }}
                                >
                                    <option value="" style={{ color: '#fff', backgroundColor: '#2d2d2d' }}>---------</option>
                                    {expenses.map(expense => (
                                        <option key={expense.id} value={expense.id} style={{ color: '#fff', backgroundColor: '#2d2d2d' }}>
                                            {expense.expense_date} - {expense.category} - Rs.{expense.amount} - {expense.description || 'No description'}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {action === 'add' && (
                            <>
                                <div className="form-group">
                                    <label htmlFor="amount">Amount:</label>
                                    <input
                                        type="number"
                                        id="amount"
                                        name="amount"
                                        step="0.01"
                                        value={formData.amount}
                                        onChange={handleChange}
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="category">Category:</label>
                                    <select
                                        id="category"
                                        name="category"
                                        value={formData.category}
                                        onChange={handleChange}
                                        required
                                        style={{ color: '#fff', backgroundColor: '#2d2d2d' }}
                                    >
                                        <option value="" style={{ color: '#fff', backgroundColor: '#2d2d2d' }}>---------</option>
                                        {categories.map(cat => (
                                            <option key={cat.value} value={cat.value} style={{ color: '#fff', backgroundColor: '#2d2d2d' }}>{cat.label}</option>
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
                                        rows="4"
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="expense_date">Expense date:</label>
                                    <input
                                        type="date"
                                        id="expense_date"
                                        name="expense_date"
                                        value={formData.expense_date}
                                        onChange={handleChange}
                                        required
                                    />
                                </div>
                            </>
                        )}

                        <div className="form-actions">
                            <button type="submit" className="btn btn-primary" disabled={loading}>
                                {loading ? (action === 'add' ? 'Adding...' : 'Removing...') : (action === 'add' ? 'Add Expense' : 'Remove Expense')}
                            </button>
                            <Link to="/dashboard" className="btn btn-link">Cancel</Link>
                        </div>
                    </form>
                </div>
            </main>
        </div>
    );
};

export default AddExpense;
