import React, { useState } from 'react';
import { Search, TrendingUp, TrendingDown, Minus, Loader2, Download, BarChart3, AlertCircle } from 'lucide-react';

export default function SentimentAnalysisApp() {
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
        `http://localhost:8000/api/analyze?company=${encodeURIComponent(company)}&max_headlines=${maxHeadlines}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to analyze sentiment');
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
        `http://localhost:8000/api/report?company=${encodeURIComponent(company)}&max_headlines=${maxHeadlines}`
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
      return <TrendingUp size={24} style={{color: '#10b981'}} />;
    } else if (sentiment === 'negative') {
      return <TrendingDown size={24} style={{color: '#ef4444'}} />;
    } else {
      return <Minus size={24} style={{color: '#64748b'}} />;
    }
  };

  const getSentimentColor = (sentiment) => {
    const colors = {
      'Strongly Positive': '#10b981',
      'Positive': '#34d399',
      'Neutral': '#64748b',
      'Negative': '#f59e0b',
      'Strongly Negative': '#ef4444',
    };
    return colors[sentiment] || '#64748b';
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(to bottom right, #0f172a, #1e293b, #0f172a)',
      color: '#f1f5f9',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        borderBottom: '1px solid #334155',
        backgroundColor: 'rgba(15, 23, 42, 0.5)',
        backdropFilter: 'blur(10px)',
        position: 'sticky',
        top: 0,
        zIndex: 10
      }}>
        <div style={{maxWidth: '1280px', margin: '0 auto', padding: '24px 16px'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px'}}>
            <div style={{
              padding: '12px',
              background: 'linear-gradient(to bottom right, #8b5cf6, #ec4899)',
              borderRadius: '12px'
            }}>
              <BarChart3 size={32} color="#fff" />
            </div>
            <div>
              <h1 style={{
                fontSize: '30px',
                fontWeight: 'bold',
                background: 'linear-gradient(to right, #a78bfa, #f9a8d4)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                margin: 0
              }}>
                Sentiment Analysis
              </h1>
              <p style={{color: '#94a3b8', fontSize: '14px', margin: '4px 0 0 0'}}>
                Analyze company sentiment from news headlines
              </p>
            </div>
          </div>

          {/* Search Bar */}
          <div style={{display: 'flex', gap: '12px', flexWrap: 'wrap'}}>
            <div style={{flex: '1 1 300px', position: 'relative'}}>
              <Search size={20} style={{
                position: 'absolute',
                left: '16px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#94a3b8'
              }} />
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
                placeholder="Enter company name (e.g., Apple, Tesla, Microsoft)..."
                style={{
                  width: '100%',
                  paddingLeft: '48px',
                  paddingRight: '16px',
                  paddingTop: '16px',
                  paddingBottom: '16px',
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '12px',
                  color: '#f1f5f9',
                  fontSize: '16px',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
            </div>
            
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 16px',
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '12px',
              minWidth: '200px'
            }}>
              <span style={{fontSize: '14px', color: '#94a3b8', whiteSpace: 'nowrap'}}>
                Headlines: {maxHeadlines}
              </span>
              <input
                type="range"
                min="5"
                max="50"
                value={maxHeadlines}
                onChange={(e) => setMaxHeadlines(Number(e.target.value))}
                style={{
                  flex: 1,
                  height: '6px',
                  backgroundColor: '#334155',
                  borderRadius: '3px',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              />
            </div>

            <button
              onClick={handleAnalyze}
              disabled={loading}
              style={{
                padding: '16px 32px',
                background: loading ? '#64748b' : 'linear-gradient(to right, #8b5cf6, #ec4899)',
                border: 'none',
                borderRadius: '12px',
                color: '#fff',
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '16px',
                fontWeight: '600',
                whiteSpace: 'nowrap'
              }}
            >
              {loading ? (
                <>
                  <Loader2 size={20} className="spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <BarChart3 size={20} />
                  Analyze
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{maxWidth: '1280px', margin: '0 auto', padding: '32px 16px'}}>
        {/* Error Message */}
        {error && (
          <div style={{
            marginBottom: '24px',
            padding: '16px',
            backgroundColor: 'rgba(127, 29, 29, 0.3)',
            border: '1px solid #ef4444',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <AlertCircle size={20} color="#f87171" />
            <span style={{color: '#fca5a5'}}>{error}</span>
          </div>
        )}

        {/* Results */}
        {result && (
          <>
            {/* Summary Card */}
            <div style={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '16px',
              padding: '24px',
              marginBottom: '24px'
            }}>
              <h2 style={{margin: '0 0 16px 0', fontSize: '22px', fontWeight: '600'}}>
                Analysis for {result.company_name}
              </h2>
              
              <div style={{
                display: 'inline-block',
                padding: '8px 20px',
                background: getSentimentColor(result.overall),
                borderRadius: '20px',
                fontSize: '18px',
                fontWeight: '700',
                color: '#fff',
                marginBottom: '16px'
              }}>
                {result.overall}
              </div>
              
              <div style={{fontSize: '18px', color: '#cbd5e1', marginBottom: '8px'}}>
                Sentiment Score: <strong>{result.score}</strong>
              </div>
              
              <div style={{fontSize: '14px', color: '#94a3b8'}}>
                Analysis Date: {new Date(result.analysis_date).toLocaleString()}
              </div>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: '16px',
                marginTop: '20px'
              }}>
                <div style={{
                  padding: '16px',
                  backgroundColor: '#0f172a',
                  borderRadius: '12px',
                  border: '1px solid #334155'
                }}>
                  <div style={{fontSize: '14px', color: '#94a3b8', marginBottom: '8px'}}>Positive</div>
                  <div style={{fontSize: '24px', fontWeight: 'bold', color: '#10b981'}}>
                    {result.summary.positive}
                  </div>
                </div>
                <div style={{
                  padding: '16px',
                  backgroundColor: '#0f172a',
                  borderRadius: '12px',
                  border: '1px solid #334155'
                }}>
                  <div style={{fontSize: '14px', color: '#94a3b8', marginBottom: '8px'}}>Negative</div>
                  <div style={{fontSize: '24px', fontWeight: 'bold', color: '#ef4444'}}>
                    {result.summary.negative}
                  </div>
                </div>
                <div style={{
                  padding: '16px',
                  backgroundColor: '#0f172a',
                  borderRadius: '12px',
                  border: '1px solid #334155'
                }}>
                  <div style={{fontSize: '14px', color: '#94a3b8', marginBottom: '8px'}}>Neutral</div>
                  <div style={{fontSize: '24px', fontWeight: 'bold', color: '#64748b'}}>
                    {result.summary.neutral}
                  </div>
                </div>
                <div style={{
                  padding: '16px',
                  backgroundColor: '#0f172a',
                  borderRadius: '12px',
                  border: '1px solid #334155'
                }}>
                  <div style={{fontSize: '14px', color: '#94a3b8', marginBottom: '8px'}}>Total</div>
                  <div style={{fontSize: '24px', fontWeight: 'bold', color: '#a78bfa'}}>
                    {result.summary.total}
                  </div>
                </div>
                <div style={{
                  padding: '16px',
                  backgroundColor: '#0f172a',
                  borderRadius: '12px',
                  border: '1px solid #334155'
                }}>
                  <div style={{fontSize: '14px', color: '#94a3b8', marginBottom: '8px'}}>Avg Confidence</div>
                  <div style={{fontSize: '24px', fontWeight: 'bold', color: '#06b6d4'}}>
                    {result.summary.avg_confidence}
                  </div>
                </div>
              </div>

              <button
                onClick={handleDownloadReport}
                disabled={downloadingReport}
                style={{
                  marginTop: '16px',
                  padding: '12px 24px',
                  background: downloadingReport ? '#64748b' : 'linear-gradient(to right, #0ea5e9, #06b6d4)',
                  border: 'none',
                  borderRadius: '12px',
                  color: '#fff',
                  cursor: downloadingReport ? 'not-allowed' : 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '15px',
                  fontWeight: '600'
                }}
              >
                {downloadingReport ? (
                  <>
                    <Loader2 size={18} className="spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Download size={18} />
                    Download PDF Report
                  </>
                )}
              </button>
            </div>

            {/* Headlines */}
            <h3 style={{fontSize: '20px', fontWeight: '600', marginBottom: '16px'}}>
              Detailed Analysis ({result.details.length} Headlines)
            </h3>
            
            <div style={{display: 'grid', gap: '16px'}}>
              {result.details.map((detail, index) => (
                <div
                  key={index}
                  style={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '12px',
                    padding: '20px'
                  }}
                >
                  <div style={{display: 'flex', alignItems: 'flex-start', gap: '12px'}}>
                    <div style={{flexShrink: 0, marginTop: '4px'}}>
                      {getSentimentIcon(detail.sentiment)}
                    </div>
                    <div style={{flex: 1}}>
                      <div style={{
                        fontSize: '16px',
                        fontWeight: '500',
                        lineHeight: '1.5',
                        marginBottom: '8px'
                      }}>
                        {detail.headline}
                      </div>
                      <div style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '12px',
                        fontSize: '13px',
                        color: '#94a3b8'
                      }}>
                        <span style={{
                          padding: '4px 12px',
                          backgroundColor: '#334155',
                          borderRadius: '12px',
                          fontSize: '13px',
                          fontWeight: '600'
                        }}>
                          Confidence: {(detail.score * 100).toFixed(0)}%
                        </span>
                        <span>Source: {detail.source}</span>
                        <span>Date: {detail.date}</span>
                        {detail.original_sentiment && (
                          <span style={{color: '#f59e0b'}}>
                            (Adjusted from {detail.original_sentiment})
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Empty State */}
        {!loading && !result && !error && (
          <div style={{textAlign: 'center', padding: '80px 20px'}}>
            <div style={{
              display: 'inline-block',
              padding: '24px',
              backgroundColor: '#1e293b',
              borderRadius: '9999px',
              marginBottom: '16px'
            }}>
              <BarChart3 size={64} color="#475569" />
            </div>
            <h2 style={{
              fontSize: '24px',
              fontWeight: '600',
              color: '#94a3b8',
              marginBottom: '8px'
            }}>
              No Analysis Yet
            </h2>
            <p style={{color: '#64748b'}}>
              Enter a company name to analyze sentiment from news headlines
            </p>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div style={{textAlign: 'center', padding: '80px 20px'}}>
            <div style={{
              display: 'inline-block',
              padding: '24px',
              backgroundColor: '#1e293b',
              borderRadius: '9999px',
              marginBottom: '16px'
            }}>
              <Loader2 size={64} color="#8b5cf6" className="spin" />
            </div>
            <h2 style={{
              fontSize: '24px',
              fontWeight: '600',
              color: '#94a3b8',
              marginBottom: '8px'
            }}>
              Analyzing Sentiment...
            </h2>
            <p style={{color: '#64748b'}}>
              Fetching and analyzing news headlines
            </p>
          </div>
        )}
      </div>

      <style>{`
        .spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}