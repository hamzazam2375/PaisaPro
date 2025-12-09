import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import './FinancialPages.css';
import './ShoppingList.css';

const API_BASE = 'http://localhost:8002/api';

const MyShoppingLists = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [lists, setLists] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [showConfirmModal, setShowConfirmModal] = useState(false);
    const [confirmData, setConfirmData] = useState({ listId: null, listName: '' });
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [deleteData, setDeleteData] = useState({ listId: null, listName: '' });
    const [purchasedLists, setPurchasedLists] = useState(new Set());
    const [showSuccessMessage, setShowSuccessMessage] = useState(false);
    const [successData, setSuccessData] = useState({ listName: '', amount: 0 });

    useEffect(() => {
        if (user?.id) {
            loadLists();
        } else {
            setLoading(false);
            setError('User not authenticated. Please log in.');
        }
    }, [user]);

    const loadLists = async () => {
        try {
            setLoading(true);
            setError('');
            const response = await fetch(`${API_BASE}/user/${user.id}/lists`);

            if (!response.ok) {
                throw new Error('Failed to connect to Shopping Cart backend. Make sure it\'s running on port 8002.');
            }

            const data = await response.json();

            if (data.success) {
                setLists(data.lists || []);
                
                // Determine which lists are fully purchased
                const newPurchasedLists = new Set();
                (data.lists || []).forEach(list => {
                    if (list.item_count > 0 && list.purchased_count === list.item_count) {
                        newPurchasedLists.add(list.id);
                    }
                });
                setPurchasedLists(newPurchasedLists);
            } else {
                setError(data.message || 'Failed to load lists');
            }
        } catch (err) {
            console.error('Error loading lists:', err);
            setError(err.message || 'Failed to connect to backend. Please ensure Shopping Cart service is running.');
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteList = (listId, listName) => {
        setDeleteData({ listId, listName });
        setShowDeleteModal(true);
    };

    const confirmDeleteList = async () => {
        const { listId } = deleteData;
        setShowDeleteModal(false);

        try {
            setLoading(true);
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
        } finally {
            setLoading(false);
        }
    };

    const handlePurchaseAll = async (listId, listName) => {
        setConfirmData({ listId, listName });
        setShowConfirmModal(true);
    };

    const confirmPurchaseAll = async () => {
        const { listId, listName } = confirmData;
        setShowConfirmModal(false);

        try {
            setLoading(true);

            console.log('Fetching expense data before marking as purchased...');

            // Get expense data FIRST (before marking as purchased)
            const expenseDataResponse = await fetch(`${API_BASE}/cart/${listId}/expense-data`);
            const expenseData = await expenseDataResponse.json();
            console.log('Expense data received:', expenseData);

            // Mark all as purchased
            console.log('Marking all as purchased for list:', listId);
            const purchaseResponse = await fetch(`${API_BASE}/cart/${listId}/purchase-all?user_id=${user.id}`, {
                method: 'POST'
            });

            if (!purchaseResponse.ok) {
                const errorData = await purchaseResponse.json();
                console.error('Purchase response error:', errorData);
                throw new Error('Failed to mark items as purchased');
            }

            console.log('Items marked as purchased, creating expense...');

            if (expenseData.success && expenseData.amount > 0) {
                // Create expense in Django with category 'shopping' and description as shopping list name
                const expensePayload = {
                    description: listName,
                    amount: expenseData.amount,
                    category: 'shopping',
                    expense_date: new Date().toLocaleDateString('en-CA') // Use local date in YYYY-MM-DD format
                };
                console.log('Creating expense with payload:', expensePayload);

                try {
                    const expenseResponse = await api.post('/expenses/', expensePayload);
                    console.log('Expense response:', expenseResponse.data);
                    setError('');
                    
                    // Mark list as purchased and show success message
                    setPurchasedLists(prev => new Set([...prev, listId]));
                    setSuccessData({ listName, amount: expenseData.amount });
                    setShowSuccessMessage(true);
                    
                    // Hide success message after 5 seconds
                    setTimeout(() => setShowSuccessMessage(false), 5000);
                } catch (err) {
                    console.error('Failed to create expense:', err.response?.data || err);
                    alert(`⚠️ Items marked as purchased, but failed to create expense entry.\n\nError: ${err.response?.data?.error || 'Unknown error'}`);
                }
            } else if (expenseData.success && expenseData.amount === 0) {
                console.log('No expense to create - total amount is 0');
                alert(`✅ All items marked as purchased!\n\nNo expense was created because no prices were found for the items.`);
            } else {
                console.error('Expense data fetch failed:', expenseData);
                alert(`⚠️ Items marked as purchased, but failed to get expense data.`);
            }

            await loadLists();
        } catch (err) {
            console.error('Error purchasing all:', err);
            setError(err.message || 'Failed to purchase all items');
            alert(`❌ Error: ${err.message || 'Failed to purchase all items'}`);
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

    // If user not loaded yet, show loading
    if (!user) {
        return (
            <div className="financial-page-container">
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
                    <div style={{ textAlign: 'center' }}>
                        <i className="fas fa-spinner fa-spin" style={{ fontSize: '3rem', color: '#667eea' }}></i>
                        <p style={{ color: 'rgba(255,255,255,0.6)', marginTop: '1rem' }}>Loading...</p>
                    </div>
                </div>
            </div>
        );
    }

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

            <main className="financial-page-main" style={{ maxWidth: '1000px' }}>
                <div className="page-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                        <div>
                            <h2 style={{ margin: 0 }}>My Shopping Lists</h2>
                            <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', margin: '0.25rem 0 0 0' }}>
                                Manage all your shopping lists
                            </p>
                        </div>
                        <Link to="/shopping-list" className="btn btn-primary">
                            <i className="fas fa-plus"></i> New List
                        </Link>
                    </div>

                    {loading ? (
                        <div style={{ textAlign: 'center', padding: '3rem' }}>
                            <i className="fas fa-spinner fa-spin" style={{ fontSize: '2rem', color: '#667eea' }}></i>
                            <p style={{ color: 'rgba(255,255,255,0.6)', marginTop: '1rem' }}>Loading your lists...</p>
                        </div>
                    ) : error ? (
                        <div style={{
                            textAlign: 'center',
                            padding: '2rem',
                            background: 'rgba(244, 67, 54, 0.1)',
                            borderRadius: '12px',
                            border: '1px solid rgba(244, 67, 54, 0.3)'
                        }}>
                            <i className="fas fa-exclamation-circle" style={{ fontSize: '2rem', color: '#f44336', marginBottom: '1rem' }}></i>
                            <p style={{ color: '#f44336', marginBottom: '1rem' }}>{error}</p>
                            <button onClick={loadLists} className="btn btn-primary">
                                <i className="fas fa-redo"></i> Retry
                            </button>
                        </div>
                    ) : lists.length === 0 ? (
                        <div style={{
                            textAlign: 'center',
                            padding: '4rem 2rem',
                            background: 'rgba(255, 255, 255, 0.03)',
                            borderRadius: '12px',
                            border: '2px dashed rgba(255, 255, 255, 0.1)'
                        }}>
                            <i className="fas fa-shopping-basket" style={{ fontSize: '4rem', color: 'rgba(255,255,255,0.3)', marginBottom: '1rem' }}></i>
                            <h3 style={{ color: 'rgba(255,255,255,0.8)', marginBottom: '0.5rem' }}>No Shopping Lists Yet</h3>
                            <p style={{ color: 'rgba(255,255,255,0.5)', marginBottom: '1.5rem' }}>
                                Create your first shopping list to get started!
                            </p>
                            <Link to="/shopping-list" className="btn btn-primary">
                                <i className="fas fa-plus"></i> Create Your First List
                            </Link>
                        </div>
                    ) : (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.5rem' }}>
                            {lists.map(list => (
                                <div
                                    key={list.id}
                                    style={{
                                        background: 'rgba(255, 255, 255, 0.05)',
                                        borderRadius: '12px',
                                        padding: '1.5rem',
                                        border: '1px solid rgba(255, 255, 255, 0.1)',
                                        transition: 'all 0.3s ease'
                                    }}
                                    onMouseEnter={(e) => {
                                        e.currentTarget.style.transform = 'translateY(-4px)';
                                        e.currentTarget.style.boxShadow = '0 8px 24px rgba(102, 126, 234, 0.2)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.currentTarget.style.transform = 'translateY(0)';
                                        e.currentTarget.style.boxShadow = 'none';
                                    }}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                                        <h3 style={{ color: '#fff', margin: 0, fontSize: '1.2rem' }}>{list.name}</h3>
                                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                                            <Link
                                                to={`/optimized-cart/${list.id}`}
                                                className="btn btn-primary"
                                                style={{ padding: '0.4rem 0.75rem', fontSize: '0.9rem' }}
                                            >
                                                <i className="fas fa-chart-line"></i>
                                            </Link>
                                            <button
                                                onClick={() => handleDeleteList(list.id, list.name)}
                                                className="btn btn-secondary"
                                                style={{ padding: '0.4rem 0.75rem', fontSize: '0.9rem' }}
                                            >
                                                <i className="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </div>

                                    <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.9rem', marginBottom: '1rem' }}>
                                        {typeof list.total_price_usd === 'number' && (
                                            <p style={{ margin: '0.5rem 0', fontWeight: 'bold', color: '#4caf50', fontSize: '1.1rem' }}>
                                                <i className="fas fa-dollar-sign" style={{ marginRight: '0.5rem', color: '#4caf50' }}></i>
                                                Total Price: ${list.total_price_usd.toFixed(2)} USD
                                            </p>
                                        )}
                                        <p style={{ margin: '0.5rem 0' }}>
                                            <i className="fas fa-boxes" style={{ marginRight: '0.5rem', color: '#667eea' }}></i>
                                            {list.item_count || 0} item{(list.item_count || 0) !== 1 ? 's' : ''}
                                        </p>
                                        {list.created_at && (
                                            <p style={{ margin: '0.5rem 0' }}>
                                                <i className="fas fa-calendar" style={{ marginRight: '0.5rem', color: '#667eea' }}></i>
                                                Created: {new Date(list.created_at).toLocaleDateString()}
                                            </p>
                                        )}
                                        {list.updated_at && (
                                            <p style={{ margin: '0.5rem 0' }}>
                                                <i className="fas fa-clock" style={{ marginRight: '0.5rem', color: '#667eea' }}></i>
                                                Updated: {new Date(list.updated_at).toLocaleString()}
                                            </p>
                                        )}
                                    </div>

                                    <div style={{ marginTop: '1rem' }}>
                                        {purchasedLists.has(list.id) ? (
                                            <button
                                                className="btn"
                                                style={{ 
                                                    width: '100%', 
                                                    padding: '0.8rem', 
                                                    fontSize: '1rem',
                                                    background: 'linear-gradient(135deg, #4caf50, #45a049)',
                                                    color: 'white',
                                                    border: 'none',
                                                    borderRadius: '8px',
                                                    cursor: 'default',
                                                    boxShadow: '0 4px 12px rgba(76, 175, 80, 0.3)'
                                                }}
                                                disabled
                                            >
                                                <i className="fas fa-check-circle"></i> Purchased
                                            </button>
                                        ) : (
                                            <button
                                                onClick={() => handlePurchaseAll(list.id, list.name)}
                                                className="btn btn-primary"
                                                style={{ width: '100%', padding: '0.8rem', fontSize: '1rem' }}
                                            >
                                                <i className="fas fa-check"></i> Mark Purchased
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    <Link to="/shopping-list" className="btn btn-link" style={{ marginTop: '2rem', display: 'inline-block' }}>
                        ← Back to Shopping Lists
                    </Link>
                </div>
            </main>

            {/* Custom Confirmation Modal */}
            {showConfirmModal && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(0, 0, 0, 0.7)',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    zIndex: 9999,
                    backdropFilter: 'blur(5px)'
                }}>
                    <div style={{
                        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
                        borderRadius: '16px',
                        padding: '2rem',
                        maxWidth: '500px',
                        width: '90%',
                        border: '1px solid rgba(102, 126, 234, 0.3)',
                        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)'
                    }}>
                        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                            <div style={{
                                width: '60px',
                                height: '60px',
                                borderRadius: '50%',
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                margin: '0 auto 1rem',
                                fontSize: '2rem'
                            }}>
                                🛒
                            </div>
                            <h3 style={{ color: '#fff', margin: '0 0 0.5rem 0', fontSize: '1.3rem' }}>
                                Purchase Confirmation
                            </h3>
                            <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '1rem', margin: 0 }}>
                                Mark all items as purchased in
                            </p>
                            <p style={{
                                color: '#667eea',
                                fontSize: '1.1rem',
                                fontWeight: 'bold',
                                margin: '0.5rem 0',
                                wordBreak: 'break-word'
                            }}>
                                "{confirmData.listName}"?
                            </p>
                        </div>

                        <div style={{
                            background: 'rgba(102, 126, 234, 0.1)',
                            borderRadius: '8px',
                            padding: '1rem',
                            marginBottom: '1.5rem',
                            border: '1px solid rgba(102, 126, 234, 0.2)'
                        }}>
                            <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.9rem', margin: 0, textAlign: 'center' }}>
                                💰 This will add an expense to your account
                            </p>
                        </div>

                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <button
                                onClick={() => setShowConfirmModal(false)}
                                className="btn btn-secondary"
                                style={{ flex: 1, padding: '0.75rem', fontSize: '1rem' }}
                            >
                                <i className="fas fa-times"></i> Cancel
                            </button>
                            <button
                                onClick={confirmPurchaseAll}
                                className="btn btn-primary"
                                style={{ flex: 1, padding: '0.75rem', fontSize: '1rem' }}
                            >
                                <i className="fas fa-check"></i> Confirm
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {showDeleteModal && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(0, 0, 0, 0.7)',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    zIndex: 9999,
                    backdropFilter: 'blur(5px)'
                }}>
                    <div style={{
                        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
                        borderRadius: '16px',
                        padding: '2rem',
                        maxWidth: '500px',
                        width: '90%',
                        border: '1px solid rgba(244, 67, 54, 0.3)',
                        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)'
                    }}>
                        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                            <div style={{
                                width: '60px',
                                height: '60px',
                                borderRadius: '50%',
                                background: 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                margin: '0 auto 1rem',
                                fontSize: '2rem'
                            }}>
                                🗑️
                            </div>
                            <h3 style={{ color: '#fff', margin: '0 0 0.5rem 0', fontSize: '1.3rem' }}>
                                Delete List?
                            </h3>
                            <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '1rem', margin: 0 }}>
                                Are you sure you want to delete
                            </p>
                            <p style={{
                                color: '#f44336',
                                fontSize: '1.1rem',
                                fontWeight: 'bold',
                                margin: '0.5rem 0',
                                wordBreak: 'break-word'
                            }}>
                                "{deleteData.listName}"?
                            </p>
                        </div>

                        <div style={{
                            background: 'rgba(244, 67, 54, 0.1)',
                            borderRadius: '8px',
                            padding: '1rem',
                            marginBottom: '1.5rem',
                            border: '1px solid rgba(244, 67, 54, 0.2)'
                        }}>
                            <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.9rem', margin: 0, textAlign: 'center' }}>
                                ⚠️ This action cannot be undone. All items and price data will be permanently deleted.
                            </p>
                        </div>

                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <button
                                onClick={() => setShowDeleteModal(false)}
                                className="btn btn-secondary"
                                style={{ flex: 1, padding: '0.75rem', fontSize: '1rem' }}
                            >
                                <i className="fas fa-times"></i> Cancel
                            </button>
                            <button
                                onClick={confirmDeleteList}
                                style={{
                                    flex: 1,
                                    padding: '0.75rem',
                                    fontSize: '1rem',
                                    background: 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)',
                                    color: '#fff',
                                    border: 'none',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    fontWeight: '600',
                                    transition: 'all 0.3s ease'
                                }}
                                onMouseEnter={(e) => e.target.style.transform = 'translateY(-2px)'}
                                onMouseLeave={(e) => e.target.style.transform = 'translateY(0)'}
                            >
                                <i className="fas fa-trash"></i> Delete
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Beautiful Success Message */}
            {showSuccessMessage && (
                <div className="success-message">
                    <div className="success-content">
                        <div className="success-header">
                            <div className="success-icon">
                                <i className="fas fa-check-circle"></i>
                            </div>
                            <div>
                                <h4>Purchase Completed! 🎉</h4>
                                <p>Successfully marked as purchased</p>
                            </div>
                        </div>

                        <div className="success-details">
                            <div className="detail-row">
                                <span className="detail-label">List:</span>
                                <span className="detail-value">{successData.listName}</span>
                            </div>
                            <div className="detail-row">
                                <span className="detail-label">Expense Added:</span>
                                <span className="detail-amount">${successData.amount?.toFixed(2)} USD</span>
                            </div>
                        </div>

                        <p className="success-note">
                            💰 Expense has been added to your account balance
                        </p>

                        <button
                            onClick={() => setShowSuccessMessage(false)}
                            className="success-close"
                        >
                            <i className="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            )}

            <style jsx>{`
                @keyframes slideInRight {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            `}</style>
        </div>
    );
};

export default MyShoppingLists;
