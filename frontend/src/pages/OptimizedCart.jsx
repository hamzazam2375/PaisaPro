import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './FinancialPages.css';
import './ShoppingList.css';

const API_BASE = 'http://localhost:8002/api';

const OptimizedCart = () => {
    const { user, logout } = useAuth();
    const { listId } = useParams();
    const navigate = useNavigate();
    const [cartData, setCartData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [refreshing, setRefreshing] = useState(false);
    const [showAddItem, setShowAddItem] = useState(false);
    const [newItem, setNewItem] = useState({ product_name: '', quantity: 1 });
    const [addingItem, setAddingItem] = useState(false);

    useEffect(() => {
        if (user?.id && listId) {
            loadOptimizedCart();
        }
    }, [user, listId]);

    const loadOptimizedCart = async () => {
        try {
            setLoading(true);
            setError('');
            const response = await fetch(`${API_BASE}/cart/${listId}/optimized`);
            const data = await response.json();

            if (data.success) {
                setCartData(data);
            } else {
                setError(data.message || 'Failed to load optimized cart');
            }
        } catch (err) {
            console.error('Error loading optimized cart:', err);
            setError('Failed to load optimized cart. Make sure the backend is running.');
        } finally {
            setLoading(false);
        }
    };

    const handleRefreshPrices = async () => {
        setRefreshing(true);
        await loadOptimizedCart();
        setRefreshing(false);
    };

    const handleMarkPurchased = async (itemId) => {
        try {
            const response = await fetch(`${API_BASE}/cart/item/${itemId}/purchased`, {
                method: 'POST'
            });

            if (response.ok) {
                loadOptimizedCart();
            } else {
                alert('Failed to mark item as purchased');
            }
        } catch (err) {
            console.error('Error marking purchased:', err);
            alert('Failed to mark item as purchased');
        }
    };

    const handleAddItem = async (e) => {
        e.preventDefault();
        if (!newItem.product_name.trim()) return;

        try {
            setAddingItem(true);
            const response = await fetch(`${API_BASE}/cart/${listId}/items`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: user.id,
                    items: [newItem]
                })
            });

            const data = await response.json();
            if (data.success) {
                setNewItem({ product_name: '', quantity: 1 });
                setShowAddItem(false);
                await loadOptimizedCart();
            } else {
                alert(data.message || 'Failed to add item');
            }
        } catch (err) {
            console.error('Error adding item:', err);
            alert('Failed to add item');
        } finally {
            setAddingItem(false);
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

    const getBadgeColor = (rank) => {
        if (rank === 1) return '#4caf50'; // Green for best
        if (rank === 2) return '#ff9800'; // Orange for second
        return '#9e9e9e'; // Gray for third
    };

    // Helper to calculate potential savings in USD if not provided by backend
    const calculatePotentialSavingsUSD = () => {
        if (!cartData?.items) return 0;
        let savings = 0;
        cartData.items.forEach(item => {
            if (item.recommendations && item.recommendations.length > 1) {
                // Best price is rank 1, next best is rank 2
                const best = item.recommendations.find(r => r.rank === 1);
                const nextBest = item.recommendations.find(r => r.rank === 2);
                if (best && nextBest) {
                    savings += (nextBest.price_usd - best.price_usd) * item.quantity;
                }
            }
        });
        return savings;
    };

    return (
        <div className="financial-page-container">
            <header className="dashboard-header">
                <div className="header-left">
                    <h1 className="logo">PaisaPro</h1>
                    <p style={{ margin: 0, fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)' }}>
                        Optimized Shopping Cart
                    </p>
                </div>
                <div className="header-right">
                    <Link to="/dashboard" className="nav-link">Dashboard</Link>
                    <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
                </div>
            </header>

            <main className="financial-page-main" style={{ maxWidth: '1200px' }}>
                <div className="page-card">
                    {loading ? (
                        <div style={{ textAlign: 'center', padding: '3rem' }}>
                            <i className="fas fa-spinner fa-spin" style={{ fontSize: '2rem', color: '#667eea' }}></i>
                            <p style={{ color: 'rgba(255,255,255,0.6)', marginTop: '1rem' }}>
                                Analyzing prices across stores...
                            </p>
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
                            <button onClick={loadOptimizedCart} className="btn btn-primary">
                                <i className="fas fa-redo"></i> Retry
                            </button>
                        </div>
                    ) : cartData ? (
                        <>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                                <div>
                                    <h2 style={{ margin: 0 }}>{cartData.list_name}</h2>
                                    <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', margin: '0.25rem 0 0 0' }}>
                                        Price comparison results
                                    </p>
                                </div>
                                <div style={{ display: 'flex', gap: '0.75rem' }}>
                                    <button
                                        onClick={() => setShowAddItem(!showAddItem)}
                                        className="btn btn-primary"
                                    >
                                        <i className="fas fa-plus"></i> Add Item
                                    </button>
                                    <button
                                        onClick={handleRefreshPrices}
                                        className="btn btn-primary"
                                        disabled={refreshing}
                                    >
                                        <i className={`fas fa-sync-alt ${refreshing ? 'fa-spin' : ''}`}></i>
                                        {refreshing ? ' Refreshing...' : ' Refresh Prices'}
                                    </button>
                                </div>
                            </div>

                            {/* Add Item Form */}
                            {showAddItem && (
                                <div style={{
                                    background: 'rgba(102, 126, 234, 0.1)',
                                    borderRadius: '12px',
                                    padding: '1.5rem',
                                    marginBottom: '2rem',
                                    border: '1px solid rgba(102, 126, 234, 0.3)'
                                }}>
                                    <h3 style={{ margin: '0 0 1rem 0', color: '#fff' }}>Add New Item</h3>
                                    <form onSubmit={handleAddItem} style={{ display: 'flex', gap: '0.75rem', alignItems: 'end' }}>
                                        <div style={{ flex: 1 }}>
                                            <label style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.85rem', display: 'block', marginBottom: '0.5rem' }}>
                                                Product Name
                                            </label>
                                            <input
                                                type="text"
                                                value={newItem.product_name}
                                                onChange={(e) => setNewItem({ ...newItem, product_name: e.target.value })}
                                                placeholder="Enter product name"
                                                style={{
                                                    width: '100%',
                                                    color: '#fff',
                                                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                                                    border: '1px solid rgba(255, 255, 255, 0.2)',
                                                    padding: '0.5rem',
                                                    borderRadius: '8px'
                                                }}
                                                required
                                            />
                                        </div>
                                        <div style={{ width: '120px' }}>
                                            <label style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.85rem', display: 'block', marginBottom: '0.5rem' }}>
                                                Quantity
                                            </label>
                                            <input
                                                type="number"
                                                value={newItem.quantity}
                                                onChange={(e) => setNewItem({ ...newItem, quantity: parseInt(e.target.value) || 1 })}
                                                min="1"
                                                step="1"
                                                style={{
                                                    width: '100%',
                                                    color: '#fff',
                                                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                                                    border: '1px solid rgba(255, 255, 255, 0.2)',
                                                    padding: '0.5rem',
                                                    borderRadius: '8px',
                                                    textAlign: 'center'
                                                }}
                                            />
                                        </div>
                                        <button
                                            type="submit"
                                            className="btn btn-primary"
                                            disabled={addingItem}
                                            style={{ whiteSpace: 'nowrap' }}
                                        >
                                            {addingItem ? 'Adding...' : 'Add to List'}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setShowAddItem(false)}
                                            className="btn btn-secondary"
                                        >
                                            Cancel
                                        </button>
                                    </form>
                                </div>
                            )}

                            {/* Summary Card */}
                            <div style={{
                                background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15))',
                                borderRadius: '12px',
                                padding: '2rem',
                                marginBottom: '2rem',
                                border: '1px solid rgba(102, 126, 234, 0.3)'
                            }}>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem' }}>
                                    <div>
                                        <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.85rem', margin: '0 0 0.5rem 0' }}>
                                            Total Items
                                        </p>
                                        <p style={{ color: '#fff', fontSize: '2rem', fontWeight: 'bold', margin: 0 }}>
                                            {cartData.items?.length || 0}
                                        </p>
                                    </div>
                                    <div>
                                        <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.85rem', margin: '0 0 0.5rem 0' }}>
                                            Best Total Price
                                        </p>
                                        <p style={{ color: '#4caf50', fontSize: '2rem', fontWeight: 'bold', margin: 0 }}>
                                            ${cartData.total_cart_cost_usd?.toFixed(2) || 'N/A'} USD
                                        </p>
                                    </div>
                                    <div>
                                        <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.85rem', margin: '0 0 0.5rem 0' }}>
                                            Potential Savings
                                        </p>
                                        <p style={{ color: '#ff9800', fontSize: '2rem', fontWeight: 'bold', margin: 0 }}>
                                            {
                                                (() => {
                                                    if (typeof cartData.total_potential_savings_usd === 'number') {
                                                        return `$${cartData.total_potential_savings_usd.toFixed(2)} USD`;
                                                    } else {
                                                        const savings = calculatePotentialSavingsUSD();
                                                        return `$${savings.toFixed(2)} USD`;
                                                    }
                                                })()
                                            }
                                        </p>
                                        <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.85rem', margin: '0.25rem 0 0 0' }}>
                                            (Compare best vs other options)
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Items List */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                                {cartData.items?.map((item) => (
                                    <div
                                        key={item.item_id}
                                        style={{
                                            background: 'rgba(255, 255, 255, 0.05)',
                                            borderRadius: '12px',
                                            padding: '1.5rem',
                                            border: item.status === 'purchased'
                                                ? '2px solid #4caf50'
                                                : '1px solid rgba(255, 255, 255, 0.1)'
                                        }}
                                    >
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                                            <div>
                                                <h3 style={{
                                                    color: '#fff',
                                                    margin: 0,
                                                    fontSize: '1.1rem',
                                                    textDecoration: item.status === 'purchased' ? 'line-through' : 'none',
                                                    opacity: item.status === 'purchased' ? 0.6 : 1
                                                }}>
                                                    {item.product_name}
                                                </h3>
                                                <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', margin: '0.25rem 0 0 0' }}>
                                                    Quantity: {item.quantity}
                                                </p>
                                            </div>
                                            {/* Removed individual Mark Purchased button and purchased status */}
                                        </div>

                                        {/* Price Recommendations */}
                                        <div style={{
                                            display: 'grid',
                                            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                                            gap: '1rem',
                                            marginTop: '1rem'
                                        }}>
                                            {item.recommendations?.map((rec, idx) => (
                                                <div
                                                    key={idx}
                                                    style={{
                                                        background: item.status === 'purchased'
                                                            ? 'rgba(76, 175, 80, 0.15)'
                                                            : idx === 0
                                                                ? 'rgba(76, 175, 80, 0.1)'
                                                                : 'rgba(255, 255, 255, 0.03)',
                                                        padding: '1rem',
                                                        borderRadius: '8px',
                                                        border: item.status === 'purchased'
                                                            ? '2px solid #4caf50'
                                                            : `1px solid ${getBadgeColor(rec.rank)}`,
                                                        position: 'relative',
                                                        opacity: item.status === 'purchased' ? 0.7 : 1
                                                    }}
                                                >
                                                    <div style={{
                                                        position: 'absolute',
                                                        top: '0.5rem',
                                                        right: '0.5rem',
                                                        background: getBadgeColor(rec.rank),
                                                        color: '#fff',
                                                        padding: '0.25rem 0.5rem',
                                                        borderRadius: '4px',
                                                        fontSize: '0.75rem',
                                                        fontWeight: 'bold'
                                                    }}>
                                                        #{rec.rank}
                                                    </div>

                                                    <p style={{
                                                        color: '#667eea',
                                                        fontSize: '0.9rem',
                                                        fontWeight: '600',
                                                        margin: '0 0 0.5rem 0'
                                                    }}>
                                                        {rec.source}
                                                    </p>

                                                    <p style={{
                                                        color: '#fff',
                                                        fontSize: '1.5rem',
                                                        fontWeight: 'bold',
                                                        margin: '0.5rem 0'
                                                    }}>
                                                        ${rec.price_usd?.toFixed(2)} USD
                                                    </p>

                                                    {rec.url && (
                                                        <a
                                                            href={rec.url}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="btn btn-secondary"
                                                            style={{
                                                                width: '100%',
                                                                padding: '0.5rem',
                                                                fontSize: '0.85rem',
                                                                textAlign: 'center'
                                                            }}
                                                        >
                                                            <i className="fas fa-external-link-alt"></i> View Product
                                                        </a>
                                                    )}
                                                </div>
                                            ))}
                                        </div>

                                        {(!item.recommendations || item.recommendations.length === 0) && (
                                            <div style={{
                                                textAlign: 'center',
                                                padding: '1.5rem',
                                                background: 'rgba(255, 152, 0, 0.1)',
                                                borderRadius: '8px',
                                                marginTop: '1rem'
                                            }}>
                                                <i className="fas fa-info-circle" style={{ color: '#ff9800', marginRight: '0.5rem' }}></i>
                                                <span style={{ color: 'rgba(255,255,255,0.7)' }}>
                                                    No price data available. Try refreshing.
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>

                            <Link to="/my-shopping-lists" className="btn btn-link" style={{ marginTop: '2rem', display: 'inline-block' }}>
                                ← Back to My Lists
                            </Link>
                        </>
                    ) : null}
                </div>
            </main>
        </div>
    );
};

export default OptimizedCart;
