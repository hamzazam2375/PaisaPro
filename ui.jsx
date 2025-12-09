import React, { useState } from 'react';
import { Search, ShoppingCart, TrendingUp, Loader2, ExternalLink, Filter, X } from 'lucide-react';

export default function PriceComparisonApp() {
  const [query, setQuery] = useState('');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sources, setSources] = useState(['alfatah', 'daraz', 'imtiaz']);
  const [topN, setTopN] = useState(10);
  const [sortByPrice, setSortByPrice] = useState(true);
  const [equalDistribution, setEqualDistribution] = useState(false);
  const [parallel, setParallel] = useState(true);
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
        parallel: parallel
      });

      if (sources.length > 0) {
        params.append('sources', sources.join(','));
      }

      const response = await fetch(`http://localhost:8000/api/compare?${params}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch products');
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

  const styles = {
    container: {
      minHeight: '100vh',
      background: 'linear-gradient(to bottom right, #111827, #1f2937, #111827)',
      color: '#f3f4f6',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    },
    header: {
      borderBottom: '1px solid #374151',
      backgroundColor: 'rgba(17, 24, 39, 0.5)',
      backdropFilter: 'blur(10px)',
      position: 'sticky',
      top: 0,
      zIndex: 10
    },
    headerContent: {
      maxWidth: '1280px',
      margin: '0 auto',
      padding: '24px 16px'
    },
    headerTop: {
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      marginBottom: '24px'
    },
    iconBox: {
      padding: '12px',
      background: 'linear-gradient(to bottom right, #a855f7, #ec4899)',
      borderRadius: '12px'
    },
    title: {
      fontSize: '30px',
      fontWeight: 'bold',
      background: 'linear-gradient(to right, #c084fc, #f9a8d4)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text',
      margin: 0
    },
    subtitle: {
      color: '#9ca3af',
      fontSize: '14px',
      margin: '4px 0 0 0'
    },
    searchBar: {
      display: 'flex',
      gap: '12px',
      marginBottom: '16px'
    },
    searchContainer: {
      flex: 1,
      position: 'relative'
    },
    searchIcon: {
      position: 'absolute',
      left: '16px',
      top: '50%',
      transform: 'translateY(-50%)',
      color: '#9ca3af'
    },
    input: {
      width: '100%',
      paddingLeft: '48px',
      paddingRight: '16px',
      paddingTop: '16px',
      paddingBottom: '16px',
      backgroundColor: '#1f2937',
      border: '1px solid #374151',
      borderRadius: '12px',
      color: '#f3f4f6',
      fontSize: '16px',
      outline: 'none'
    },
    button: {
      padding: '16px 24px',
      backgroundColor: '#1f2937',
      border: '1px solid #374151',
      borderRadius: '12px',
      color: '#f3f4f6',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      fontSize: '16px',
      fontWeight: '500',
      transition: 'all 0.3s'
    },
    searchButton: {
      padding: '16px 32px',
      background: 'linear-gradient(to right, #9333ea, #db2777)',
      border: 'none',
      borderRadius: '12px',
      color: '#fff',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      fontSize: '16px',
      fontWeight: '600',
      transition: 'all 0.3s'
    },
    filterPanel: {
      marginTop: '16px',
      padding: '24px',
      backgroundColor: '#1f2937',
      border: '1px solid #374151',
      borderRadius: '12px'
    },
    sourceButtons: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: '8px',
      marginTop: '12px'
    },
    sourceButton: (isActive, color) => ({
      padding: '8px 16px',
      borderRadius: '8px',
      border: 'none',
      cursor: 'pointer',
      fontWeight: '500',
      backgroundColor: isActive ? color : '#374151',
      color: isActive ? '#fff' : '#9ca3af',
      transition: 'all 0.3s'
    }),
    optionsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
      gap: '24px',
      marginTop: '24px'
    },
    checkbox: {
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      cursor: 'pointer',
      marginBottom: '12px'
    },
    checkboxInput: {
      width: '20px',
      height: '20px',
      cursor: 'pointer'
    },
    mainContent: {
      maxWidth: '1280px',
      margin: '0 auto',
      padding: '32px 16px'
    },
    errorBox: {
      marginBottom: '24px',
      padding: '16px',
      backgroundColor: 'rgba(127, 29, 29, 0.3)',
      border: '1px solid #ef4444',
      borderRadius: '12px',
      display: 'flex',
      alignItems: 'center',
      gap: '12px'
    },
    resultsHeader: {
      marginBottom: '16px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      color: '#9ca3af'
    },
    productsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
      gap: '24px'
    },
    productCard: {
      backgroundColor: '#1f2937',
      border: '1px solid #374151',
      borderRadius: '12px',
      overflow: 'hidden',
      transition: 'all 0.3s'
    },
    productContent: {
      padding: '24px'
    },
    badgeContainer: {
      display: 'flex',
      justifyContent: 'space-between',
      marginBottom: '16px'
    },
    badge: (color) => ({
      padding: '4px 12px',
      backgroundColor: color,
      borderRadius: '9999px',
      fontSize: '12px',
      fontWeight: '600',
      color: '#fff'
    }),
    topBadge: {
      padding: '4px 12px',
      background: 'linear-gradient(to right, #eab308, #f97316)',
      borderRadius: '9999px',
      fontSize: '12px',
      fontWeight: '600',
      color: '#fff'
    },
    productName: {
      fontSize: '18px',
      fontWeight: '600',
      marginBottom: '16px',
      minHeight: '56px',
      display: '-webkit-box',
      WebkitLineClamp: 2,
      WebkitBoxOrient: 'vertical',
      overflow: 'hidden'
    },
    priceContainer: {
      marginBottom: '16px'
    },
    price: {
      fontSize: '30px',
      fontWeight: 'bold',
      background: 'linear-gradient(to right, #34d399, #10b981)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text'
    },
    priceUsd: {
      fontSize: '14px',
      color: '#9ca3af',
      marginTop: '8px'
    },
    productLink: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '8px',
      width: '100%',
      padding: '12px',
      background: 'linear-gradient(to right, #9333ea, #db2777)',
      borderRadius: '8px',
      color: '#fff',
      textDecoration: 'none',
      fontWeight: '500',
      transition: 'all 0.3s'
    },
    emptyState: {
      textAlign: 'center',
      padding: '80px 20px'
    },
    emptyIconBox: {
      display: 'inline-block',
      padding: '24px',
      backgroundColor: '#1f2937',
      borderRadius: '9999px',
      marginBottom: '16px'
    },
    emptyTitle: {
      fontSize: '24px',
      fontWeight: '600',
      color: '#9ca3af',
      marginBottom: '8px'
    },
    emptyText: {
      color: '#6b7280'
    },
    slider: {
      width: '100%',
      height: '8px',
      backgroundColor: '#374151',
      borderRadius: '4px',
      outline: 'none',
      cursor: 'pointer'
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerContent}>
          <div style={styles.headerTop}>
            <div style={styles.iconBox}>
              <ShoppingCart size={32} color="#fff" />
            </div>
            <div>
              <h1 style={styles.title}>Price Comparison</h1>
              <p style={styles.subtitle}>Find the best deals across Pakistan</p>
            </div>
          </div>

          {/* Search Bar */}
          <div style={styles.searchBar}>
            <div style={styles.searchContainer}>
              <div style={styles.searchIcon}>
                <Search size={20} />
              </div>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search for products..."
                style={styles.input}
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              style={styles.button}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#374151'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#1f2937'}
            >
              <Filter size={20} />
              Filters
            </button>
            <button
              onClick={handleSearch}
              disabled={loading}
              style={{...styles.searchButton, opacity: loading ? 0.5 : 1, cursor: loading ? 'not-allowed' : 'pointer'}}
              onMouseEnter={(e) => !loading && (e.target.style.background = 'linear-gradient(to right, #a855f7, #ec4899)')}
              onMouseLeave={(e) => !loading && (e.target.style.background = 'linear-gradient(to right, #9333ea, #db2777)')}
            >
              {loading ? (
                <>
                  <Loader2 size={20} style={{animation: 'spin 1s linear infinite'}} />
                  Searching...
                </>
              ) : (
                <>
                  <Search size={20} />
                  Search
                </>
              )}
            </button>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div style={styles.filterPanel}>
              <div>
                <label style={{fontSize: '14px', fontWeight: '600', color: '#d1d5db'}}>Sources</label>
                <div style={styles.sourceButtons}>
                  {availableSources.map(source => (
                    <button
                      key={source.id}
                      onClick={() => toggleSource(source.id)}
                      style={styles.sourceButton(sources.includes(source.id), source.color)}
                    >
                      {source.name}
                    </button>
                  ))}
                </div>
              </div>

              <div style={styles.optionsGrid}>
                <div>
                  <label style={{fontSize: '14px', fontWeight: '600', color: '#d1d5db', display: 'block', marginBottom: '8px'}}>
                    Number of Results: {topN}
                  </label>
                  <input
                    type="range"
                    min="5"
                    max="50"
                    value={topN}
                    onChange={(e) => setTopN(Number(e.target.value))}
                    style={styles.slider}
                  />
                </div>

                <div>
                  <label style={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={sortByPrice}
                      onChange={(e) => setSortByPrice(e.target.checked)}
                      style={styles.checkboxInput}
                    />
                    <span style={{fontSize: '14px', color: '#d1d5db'}}>Sort by Price</span>
                  </label>

                  <label style={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={equalDistribution}
                      onChange={(e) => setEqualDistribution(e.target.checked)}
                      style={styles.checkboxInput}
                    />
                    <span style={{fontSize: '14px', color: '#d1d5db'}}>Equal Distribution</span>
                  </label>

                  <label style={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={parallel}
                      onChange={(e) => setParallel(e.target.checked)}
                      style={styles.checkboxInput}
                    />
                    <span style={{fontSize: '14px', color: '#d1d5db'}}>Parallel Search</span>
                  </label>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div style={styles.mainContent}>
        {/* Error Message */}
        {error && (
          <div style={styles.errorBox}>
            <X size={20} color="#f87171" />
            <span style={{color: '#fca5a5'}}>{error}</span>
          </div>
        )}

        {/* Results */}
        {products.length > 0 && (
          <div style={styles.resultsHeader}>
            <TrendingUp size={20} />
            <span>Found {products.length} products</span>
          </div>
        )}

        <div style={styles.productsGrid}>
          {products.map((product, index) => (
            <div
              key={index}
              style={styles.productCard}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#a855f7';
                e.currentTarget.style.boxShadow = '0 20px 25px -5px rgba(168, 85, 247, 0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#374151';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div style={styles.productContent}>
                <div style={styles.badgeContainer}>
                  <span style={styles.badge(getSourceColor(product.source))}>
                    {product.source}
                  </span>
                  {index < 3 && (
                    <span style={styles.topBadge}>
                      Top {index + 1}
                    </span>
                  )}
                </div>

                <h3 style={styles.productName}>
                  {product.name}
                </h3>

                <div style={styles.priceContainer}>
                  <div style={styles.price}>
                    Rs {product.price_pkr.toLocaleString()}
                  </div>
                  <div style={styles.priceUsd}>
                    ${product.price_usd.toFixed(2)} USD
                  </div>
                </div>

                {product.url !== 'N/A' && (
                  <a
                    href={product.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={styles.productLink}
                    onMouseEnter={(e) => e.target.style.background = 'linear-gradient(to right, #a855f7, #ec4899)'}
                    onMouseLeave={(e) => e.target.style.background = 'linear-gradient(to right, #9333ea, #db2777)'}
                  >
                    View Product
                    <ExternalLink size={16} />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {!loading && products.length === 0 && !error && (
          <div style={styles.emptyState}>
            <div style={styles.emptyIconBox}>
              <Search size={64} color="#4b5563" />
            </div>
            <h2 style={styles.emptyTitle}>No Results Yet</h2>
            <p style={styles.emptyText}>Search for products to compare prices</p>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div style={styles.emptyState}>
            <div style={{...styles.emptyIconBox, animation: 'pulse 2s ease-in-out infinite'}}>
              <Loader2 size={64} color="#a855f7" style={{animation: 'spin 1s linear infinite'}} />
            </div>
            <h2 style={styles.emptyTitle}>Searching...</h2>
            <p style={styles.emptyText}>Finding the best prices for you</p>
          </div>
        )}
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}