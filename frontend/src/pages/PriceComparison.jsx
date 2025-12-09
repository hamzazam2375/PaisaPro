import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './FinancialPages.css';

const API_BASE_PRICE = 'http://localhost:8001/api';
const API_BASE_CART = 'http://localhost:8002/api';

const PriceComparison = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [query, setQuery] = useState('');
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [sources, setSources] = useState(['alfatah', 'daraz', 'imtiaz']);
    const [topN, setTopN] = useState(10);
    const [sortByPrice, setSortByPrice] = useState(true);
    const [equalDistribution, setEqualDistribution] = useState(false);
    const [showFilters, setShowFilters] = useState(false);

    const availableSources = [
        { id: 'alfatah', name: 'Alfatah', color: '#10b981' },
        { id: 'daraz', name: 'Daraz', color: '#f97316' },
        { id: 'imtiaz', name: 'Imtiaz', color: '#3b82f6' }
    ];

    const handleSearch = async () => {
        if (!query.trim()) {
            setError('Please enter a search query');
            return;
        }

        setLoading(true);
        setError('');
        setProducts([]);

        try {
            const params = new URLSearchParams({
                query: query,
                top_n: topN,
                sort: sortByPrice,
                equal_distribution: equalDistribution,
                parallel: true
            });

            if (sources.length > 0) {
                params.append('sources', sources.join(','));
            }

            const response = await fetch(`http://localhost:8001/api/compare?${params}`);

            if (!response.ok) {
                throw new Error('Failed to fetch products. Make sure the FastAPI backend is running on port 8001.');
            }

            const data = await response.json();
            setProducts(data);
        } catch (err) {
            setError(err.message || 'An error occurred while fetching products');
        } finally {
            setLoading(false);
        }
    };

    const toggleSource = (sourceId) => {
        setSources(prev =>
            prev.includes(sourceId)
                ? prev.filter(s => s !== sourceId)
                : [...prev, sourceId]
        );
    };

    const getSourceColor = (sourceName) => {
        const source = availableSources.find(s => s.name.toLowerCase() === sourceName.toLowerCase());
        return source?.color || '#6b7280';
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
            <nav className="navbar navbar-expand-lg navbar-dark">
                <div className="container-fluid" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '2rem' }}>
                    <div style={{ flex: '0 0 auto' }}>
                        <Link to="/" style={{ color: '#fff', fontSize: '1.5rem', fontWeight: 'bold', textDecoration: 'none' }}>PaisaPro</Link>
                        <p style={{ margin: 0, fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)', paddingLeft: '0.25rem' }}>
                            Price Comparison Tool
                        </p>
                    </div>
                    <div className="d-flex align-items-center" style={{ flex: '0 0 auto', marginLeft: 'auto' }}>
                        <Link to="/dashboard" className="btn btn-sm me-2" style={{
                            border: '1px solid rgba(255, 255, 255, 0.3)',
                            color: '#fff',
                            backgroundColor: 'transparent',
                            transition: 'all 0.3s ease',
                            fontSize: '0.875rem',
                            padding: '0.5rem 1.25rem'
                        }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.6)';
                                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                                e.currentTarget.style.boxShadow = '0 0 0 3px rgba(255, 255, 255, 0.05)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.3)';
                                e.currentTarget.style.backgroundColor = 'transparent';
                                e.currentTarget.style.boxShadow = 'none';
                            }}>
                            Dashboard
                        </Link>
                        <button onClick={handleLogout} className="btn btn-sm" style={{
                            border: 'none',
                            color: '#fff',
                            backgroundColor: 'rgba(140, 140, 160, 0.5)',
                            transition: 'all 0.3s ease',
                            fontSize: '0.875rem',
                            padding: '0.5rem 1.25rem'
                        }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.backgroundColor = 'rgba(160, 160, 180, 0.6)';
                                e.currentTarget.style.boxShadow = '0 0 0 3px rgba(255, 255, 255, 0.05)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.backgroundColor = 'rgba(140, 140, 160, 0.5)';
                                e.currentTarget.style.boxShadow = 'none';
                            }}>
                            Logout
                        </button>
                    </div>
                </div>
            </nav>

            <div className="container-fluid mt-4">
                <div className="financial-page-card">
                    <div className="financial-page-header">
                        <div className="d-flex align-items-center justify-content-between mb-3">
                            <div>
                                <h2><i className="fas fa-shopping-cart me-2"></i>Price Comparison Tool</h2>
                                <p>Compare prices across Alfatah, Daraz, and Imtiaz</p>
                            </div>
                            <button
                                onClick={() => setShowFilters(!showFilters)}
                                className="btn btn-sm"
                                style={{
                                    border: '1px solid rgba(255, 255, 255, 0.2)',
                                    color: '#fff',
                                    backgroundColor: 'transparent',
                                    transition: 'all 0.3s ease'
                                }}
                            >
                                <i className="fas fa-filter me-1"></i>
                                {showFilters ? 'Hide' : 'Show'} Filters
                            </button>
                        </div>

                        {/* Search Bar */}
                        <div className="search-section">
                            <div className="input-group">
                                <input
                                    type="text"
                                    className="form-control"
                                    placeholder="Search for products (e.g., milk, rice, flour)..."
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                                />
                                <button
                                    className="btn btn-primary"
                                    onClick={handleSearch}
                                    disabled={loading}
                                >
                                    <i className="fas fa-search me-1"></i>
                                    {loading ? 'Searching...' : 'Search'}
                                </button>
                            </div>
                        </div>

                        {/* Filters */}
                        {showFilters && (
                            <div className="filters-section mt-3">
                                <div className="row g-3">
                                    <div className="col-md-4">
                                        <label className="form-label">Sources</label>
                                        <div className="d-flex gap-2 flex-wrap">
                                            {availableSources.map(source => (
                                                <button
                                                    key={source.id}
                                                    className={`btn btn-sm ${sources.includes(source.id) ? 'btn-success' : 'btn-outline-secondary'}`}
                                                    onClick={() => toggleSource(source.id)}
                                                >
                                                    {source.name}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="col-md-4">
                                        <label className="form-label">Max Results: {topN}</label>
                                        <input
                                            type="range"
                                            className="form-range"
                                            min="5"
                                            max="50"
                                            step="5"
                                            value={topN}
                                            onChange={(e) => setTopN(parseInt(e.target.value))}
                                        />
                                    </div>
                                    <div className="col-md-4">
                                        <label className="form-label">Sort by Price</label>
                                        <div className="form-check form-switch">
                                            <input
                                                className="form-check-input"
                                                type="checkbox"
                                                checked={sortByPrice}
                                                onChange={(e) => setSortByPrice(e.target.checked)}
                                            />
                                            <label className="form-check-label">
                                                {sortByPrice ? 'Enabled' : 'Disabled'}
                                            </label>
                                        </div>
                                    </div>
                                </div>
                                <div className="row g-3 mt-2">
                                    <div className="col-md-12">
                                        <label className="form-label">Equal Distribution</label>
                                        <div className="form-check form-switch">
                                            <input
                                                className="form-check-input"
                                                type="checkbox"
                                                checked={equalDistribution}
                                                onChange={(e) => setEqualDistribution(e.target.checked)}
                                            />
                                            <label className="form-check-label">
                                                {equalDistribution ? 'Get equal products from each source' : 'Show all results together'}
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="alert alert-danger mt-3">
                            <i className="fas fa-exclamation-circle me-2"></i>
                            {error}
                        </div>
                    )}

                    {/* Results */}
                    <div className="results-section mt-4">
                        {products.length > 0 && (
                            <div>
                                <h5 className="mb-3">Found {products.length} products</h5>
                                <div className="row g-3">
                                    {products.map((product, index) => (
                                        <div key={index} className="col-md-6 col-lg-4">
                                            <div className="product-card">
                                                <div
                                                    className="product-source"
                                                    style={{ backgroundColor: getSourceColor(product.source) }}
                                                >
                                                    {product.source}
                                                </div>
                                                <div className="product-info">
                                                    <h6 className="product-name">{product.name}</h6>
                                                    <div className="product-prices" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                                                        <div className="price-usd" style={{ fontSize: '2rem', fontWeight: 'bold', color: '#10b981', lineHeight: 1 }}>
                                                            ${product.price_usd.toFixed(2)} USD
                                                        </div>
                                                        <div className="price-pkr" style={{ fontSize: '1rem', color: '#6b7280', marginTop: '0.25rem' }}>
                                                            Rs. {product.price_pkr.toFixed(2)}
                                                        </div>
                                                    </div>
                                                    {product.url && product.url !== 'N/A' && product.url.startsWith('http') ? (
                                                        <a
                                                            href={product.url}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="btn btn-sm btn-outline-primary mt-2 w-100"
                                                        >
                                                            <i className="fas fa-external-link-alt me-1"></i>
                                                            View Product
                                                        </a>
                                                    ) : (
                                                        <button
                                                            className="btn btn-sm btn-outline-secondary mt-2 w-100"
                                                            disabled
                                                            title="Product URL not available"
                                                        >
                                                            <i className="fas fa-ban me-1"></i>
                                                            URL Not Available
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {!loading && !error && products.length === 0 && query && (
                            <div className="text-center text-muted py-5">
                                <i className="fas fa-search fa-3x mb-3"></i>
                                <p>No products found. Try a different search term.</p>
                            </div>
                        )}

                        {!loading && !query && (
                            <div className="text-center text-muted py-5">
                                <i className="fas fa-shopping-basket fa-3x mb-3"></i>
                                <p>Enter a product name to start comparing prices!</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PriceComparison;
