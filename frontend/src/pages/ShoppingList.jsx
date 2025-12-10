import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './FinancialPages.css';
import './ShoppingList.css';

const API_BASE = 'http://localhost:8002/api';

const ShoppingList = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [lists, setLists] = useState([]);
    const [showMyLists, setShowMyLists] = useState(false);
    const [newListName, setNewListName] = useState('');
    const [newListItems, setNewListItems] = useState([{ product_name: '', quantity: '' }]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (user?.id) {
            loadLists();
        }
    }, [user]);

    const loadLists = async () => {
        if (!user?.id) return;

        try {
            const response = await fetch(`${API_BASE}/user/${user.id}/lists`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    setLists(data.lists || []);
                }
            }
        } catch (err) {
            console.error('Error loading lists:', err);
        }
    };

    const handleAddItem = () => {
        setNewListItems([...newListItems, { product_name: '', quantity: '' }]);
    };

    const handleRemoveItem = (index) => {
        if (newListItems.length > 1) {
            const updatedItems = newListItems.filter((_, i) => i !== index);
            setNewListItems(updatedItems);
        }
    };

    const handleItemChange = (index, field, value) => {
        const updatedItems = [...newListItems];
        if (field === 'quantity') {
            // Allow empty string for quantity, will be validated later
            updatedItems[index][field] = value === '' ? '' : (parseInt(value) || '');
        } else {
            updatedItems[index][field] = value;
        }
        setNewListItems(updatedItems);
    };

    const handleCreateList = async (e) => {
        e.preventDefault();
        setError('');

        if (!newListName.trim()) {
            setError('Please enter a list name');
            return;
        }

        const validItems = newListItems.filter(item => {
            const hasValidName = item.product_name.trim() !== '';
            const hasValidQuantity = item.quantity !== '' && parseInt(item.quantity) > 0;
            return hasValidName && hasValidQuantity;
        });

        if (validItems.length === 0) {
            setError('Please add at least one item with a valid name and quantity');
            return;
        }

        if (!user?.id) {
            setError('User not authenticated');
            return;
        }

        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/cart/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: user.id,
                    list_name: newListName,
                    items: validItems
                })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to create list');
            }

            const data = await response.json();

            // Redirect immediately
            navigate('/my-shopping-lists');
        } catch (err) {
            setError(err.message || 'Failed to create shopping list');
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteList = async (listId) => {
        if (!window.confirm('Are you sure you want to delete this list?')) return;

        try {
            const response = await fetch(`${API_BASE}/cart/${listId}?user_id=${user.id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                await loadLists();
            } else {
                alert('Failed to delete list');
            }
        } catch (err) {
            console.error('Error deleting list:', err);
            alert('Failed to delete list');
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
                        Smart Shopping Cart Optimizer
                    </p>
                </div>
                <div className="header-right">
                    <Link to="/dashboard" className="nav-link">Dashboard</Link>
                    <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
                </div>
            </header>

            <main className="financial-page-main" style={{ maxWidth: '800px' }}>
                <div className="page-card">
                    <div style={{ marginBottom: '1rem' }}>
                        <h2 style={{ margin: 0 }}>Shopping Lists</h2>
                        <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', margin: '0.25rem 0 0 0' }}>
                            Welcome back, Hamza Azam! 👋
                        </p>
                    </div>

                    {error && (
                        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
                            {error}
                        </div>
                    )}

                    {/* Create New List Form */}
                    <div style={{
                        background: 'rgba(255, 255, 255, 0.03)',
                        borderRadius: '12px',
                        padding: '1.5rem',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        marginTop: '1.5rem'
                    }}>
                        <h3 style={{ marginBottom: '1.25rem', fontSize: '1.1rem' }}>Create New Shopping List</h3>
                        <form onSubmit={handleCreateList}>
                            <div className="form-group">
                                <label htmlFor="listName">List Name (e.g., Weekly Groceries):</label>
                                <input
                                    type="text"
                                    id="listName"
                                    value={newListName}
                                    onChange={(e) => setNewListName(e.target.value)}
                                    placeholder="Enter list name"
                                    className="list-name-input"
                                    autoComplete="off"
                                    required
                                />
                            </div>

                            <div style={{ marginBottom: '1.5rem' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                                    <label style={{ margin: 0, color: '#fff', fontWeight: '500' }}>
                                        Items:
                                    </label>
                                    <button
                                        type="button"
                                        onClick={handleAddItem}
                                        className="btn"
                                        style={{
                                            padding: '0.4rem 1rem',
                                            fontSize: '0.85rem',
                                            background: 'rgba(102, 126, 234, 0.3)',
                                            color: '#fff',
                                            border: '1px solid rgba(102, 126, 234, 0.5)',
                                            fontWeight: '500'
                                        }}
                                    >
                                        <i className="fas fa-plus"></i> Add Item
                                    </button>
                                </div>
                                {newListItems.map((item, index) => (
                                    <div key={index} style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.75rem' }}>
                                        <input
                                            type="text"
                                            value={item.product_name}
                                            onChange={(e) => handleItemChange(index, 'product_name', e.target.value)}
                                            placeholder="Product name"
                                            style={{
                                                flex: 1,
                                                color: '#fff',
                                                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                                                border: '1px solid rgba(255, 255, 255, 0.2)',
                                                padding: '0.5rem',
                                                borderRadius: '8px'
                                            }}
                                            required
                                        />
                                        <input
                                            type="number"
                                            value={item.quantity}
                                            onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                                            onBlur={(e) => {
                                                // Set default quantity to 1 if empty on blur
                                                if (item.quantity === '' || item.quantity === 0) {
                                                    handleItemChange(index, 'quantity', 1);
                                                }
                                            }}
                                            placeholder="Qty"
                                            min="1"
                                            step="1"
                                            style={{
                                                width: '80px',
                                                color: '#fff',
                                                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                                                border: '1px solid rgba(255, 255, 255, 0.2)',
                                                padding: '0.5rem',
                                                borderRadius: '8px',
                                                textAlign: 'center'
                                            }}
                                        />
                                        {newListItems.length > 1 && (
                                            <button
                                                type="button"
                                                onClick={() => handleRemoveItem(index)}
                                                className="btn btn-secondary"
                                                style={{ padding: '0.5rem 0.75rem' }}
                                            >
                                                <i className="fas fa-times"></i>
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </div>

                            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                                <button
                                    type="submit"
                                    className="btn btn-primary"
                                    disabled={loading}
                                >
                                    {loading ? 'Creating...' : 'Create List'}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setNewListName('');
                                        setNewListItems([{ product_name: '', quantity: 1 }]);
                                        setError('');
                                    }}
                                    className="btn btn-secondary"
                                    disabled={loading}
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>

                    {/* My Lists Button */}
                    <div style={{ marginTop: '1.5rem' }}>
                        <Link
                            to="/my-shopping-lists"
                            className="btn"
                            style={{
                                background: 'rgba(16, 185, 129, 0.2)',
                                color: '#10b981',
                                border: '1px solid rgba(16, 185, 129, 0.3)',
                                padding: '0.75rem 1.5rem',
                                display: 'inline-block',
                                textDecoration: 'none'
                            }}
                        >
                            <i className="fas fa-list"></i> My Lists ({lists.length})
                        </Link>
                    </div>                    <Link to="/dashboard" className="btn btn-link" style={{ marginTop: '2rem', display: 'inline-block' }}>
                        ← Back to Dashboard
                    </Link>
                </div>
            </main>
        </div>
    );
};

export default ShoppingList;
