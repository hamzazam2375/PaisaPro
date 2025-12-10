import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './FinancialPages.css';

const SentimentAnalysis = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [company, setCompany] = useState('');
    const [maxHeadlines, setMaxHeadlines] = useState(10);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [result, setResult] = useState(null);
    const [downloadingReport, setDownloadingReport] = useState(false);

    const handleAnalyze = async () => {
        if (!company.trim()) {
            setError('Please enter a company name');
            return;
        }

        setLoading(true);
        setError('');
        setResult(null);

        try {
            const response = await fetch(
                `http://localhost:8001/api/analyze?company=${encodeURIComponent(company)}&max_headlines=${maxHeadlines}`
            );

            if (!response.ok) {
                throw new Error('Failed to analyze sentiment. Make sure the FastAPI backend is running on port 8001.');
            }

            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError(err.message || 'An error occurred during analysis');
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadReport = async () => {
        if (!result) return;

        setDownloadingReport(true);
        try {
            const response = await fetch(
                `http://localhost:8001/api/report?company=${encodeURIComponent(company)}&max_headlines=${maxHeadlines}`
            );

            if (!response.ok) {
                throw new Error('Failed to generate report');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `sentiment_report_${company.replace(/\s+/g, '_')}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (err) {
            setError('Failed to download report');
        } finally {
            setDownloadingReport(false);
        }
    };

    const getSentimentIcon = (sentiment) => {
        if (sentiment === 'positive') {
            return <i className="fas fa-arrow-up" style={{ color: '#10b981', fontSize: '1.2em' }}></i>;
        } else if (sentiment === 'negative') {
            return <i className="fas fa-arrow-down" style={{ color: '#ef4444', fontSize: '1.2em' }}></i>;
        } else {
            return <i className="fas fa-minus" style={{ color: '#fbbf24', fontSize: '1.2em' }}></i>;
        }
    };

    const getSentimentBadgeClass = (sentiment) => {
        const classes = {
            positive: 'badge bg-success',
            negative: 'badge bg-danger',
            neutral: 'badge bg-secondary'
        };
        return classes[sentiment] || 'badge bg-secondary';
    };

    const getOverallSentimentColor = (result) => {
        if (!result) return '#6b7280';
        if (result.overall === 'Positive') return '#10b981';
        if (result.overall === 'Negative') return '#ef4444';
        return '#fbbf24';
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
                            Market Sentiment Analysis
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
                        <h2><i className="fas fa-chart-line me-2"></i>Market Sentiment Analysis</h2>
                        <p>Analyze company sentiment from latest financial news using AI</p>

                        {/* Input Section */}
                        <div className="search-section mt-4">
                            <div className="row g-3">
                                <div className="col-md-8">
                                    <div className="input-group">
                                        <input
                                            type="text"
                                            className="form-control"
                                            placeholder="Enter company name (e.g., Apple, Tesla, Microsoft)..."
                                            value={company}
                                            onChange={(e) => setCompany(e.target.value)}
                                            onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
                                        />
                                        <button
                                            className="btn btn-primary"
                                            onClick={handleAnalyze}
                                            disabled={loading}
                                        >
                                            <i className="fas fa-search me-1"></i>
                                            {loading ? 'Analyzing...' : 'Analyze'}
                                        </button>
                                    </div>
                                </div>
                                <div className="col-md-4">
                                    <div className="input-group">
                                        <span className="input-group-text">Max Headlines</span>
                                        <input
                                            type="number"
                                            className="form-control"
                                            value={maxHeadlines}
                                            onChange={(e) => setMaxHeadlines(parseInt(e.target.value) || 10)}
                                            min="5"
                                            max="50"
                                            step="1"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="alert alert-danger mt-3">
                            <i className="fas fa-exclamation-circle me-2"></i>
                            {error}
                        </div>
                    )}

                    {/* Results */}
                    {result && (
                        <div className="results-section mt-4">
                            {/* Overall Sentiment */}
                            <div className="sentiment-overview mb-4">
                                <div className="row g-3">
                                    <div className="col-md-4">
                                        <div className="sentiment-stat-card" style={{ borderLeftColor: getOverallSentimentColor(result) }}>
                                            <h6 style={{ color: 'rgba(255, 255, 255, 0.95)', fontWeight: 600 }}>OVERALL SENTIMENT</h6>
                                            <h3 style={{ color: '#ffffff', textTransform: 'capitalize', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                {getSentimentIcon(result.overall.toLowerCase())}
                                                <span style={{ color: getOverallSentimentColor(result) }}>{result.overall}</span>
                                            </h3>
                                            <p style={{ color: 'rgba(255, 255, 255, 0.85)', marginBottom: 0 }}>Confidence: {(result.score * 100).toFixed(1)}%</p>
                                        </div>
                                    </div>
                                    <div className="col-md-4">
                                        <div className="sentiment-stat-card" style={{ borderLeftColor: '#10b981' }}>
                                            <h6 style={{ color: 'rgba(255, 255, 255, 0.9)' }}>POSITIVE NEWS</h6>
                                            <h3 className="text-success">{result.summary.positive}</h3>
                                            <p style={{ color: 'rgba(255, 255, 255, 0.7)', marginBottom: 0 }}>
                                                {((result.summary.positive / result.summary.total) * 100).toFixed(1)}% of total
                                            </p>
                                        </div>
                                    </div>
                                    <div className="col-md-4">
                                        <div className="sentiment-stat-card" style={{ borderLeftColor: '#ef4444' }}>
                                            <h6 style={{ color: 'rgba(255, 255, 255, 0.9)' }}>NEGATIVE NEWS</h6>
                                            <h3 className="text-danger">{result.summary.negative}</h3>
                                            <p style={{ color: 'rgba(255, 255, 255, 0.7)', marginBottom: 0 }}>
                                                {((result.summary.negative / result.summary.total) * 100).toFixed(1)}% of total
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {/* Download Report Button */}
                                <div className="mt-3">
                                    <button
                                        className="btn btn-success"
                                        onClick={handleDownloadReport}
                                        disabled={downloadingReport}
                                    >
                                        <i className="fas fa-download me-2"></i>
                                        {downloadingReport ? 'Generating PDF...' : 'Download PDF Report'}
                                    </button>
                                </div>
                            </div>

                            {/* Headlines List */}
                            <div className="headlines-section">
                                <h5 className="mb-3" style={{ color: 'rgba(255, 255, 255, 0.95)' }}>
                                    <i className="fas fa-newspaper me-2"></i>
                                    Analyzed Headlines ({result.details.length})
                                </h5>
                                <div className="headlines-list">
                                    {result.details.map((detail, index) => (
                                        <div key={index} className="headline-card">
                                            <div className="d-flex align-items-start justify-content-between">
                                                <div className="flex-grow-1">
                                                    <div className="d-flex align-items-center gap-2 mb-2">
                                                        <span className={getSentimentBadgeClass(detail.sentiment)}>
                                                            {getSentimentIcon(detail.sentiment)} {detail.sentiment}
                                                        </span>
                                                        <span className="badge bg-info">{(detail.score * 100).toFixed(1)}%</span>
                                                        <small style={{ color: 'rgba(255, 255, 255, 0.65)' }}>{detail.source}</small>
                                                        <small style={{ color: 'rgba(255, 255, 255, 0.65)' }}>{detail.date}</small>
                                                    </div>
                                                    <p className="headline-text mb-0" style={{ color: 'rgba(255, 255, 255, 0.9)' }}>{detail.headline}</p>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Empty State */}
                    {!loading && !result && !error && (
                        <div className="text-center py-5" style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                            <i className="fas fa-chart-bar fa-3x mb-3"></i>
                            <p>Enter a company name to analyze market sentiment from latest news!</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SentimentAnalysis;
