import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';
import './FinancialPages.css';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend
);

const SpendingReport = () => {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const [reportData, setReportData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [downloadingPDF, setDownloadingPDF] = useState(false);
    const [showAllExpenses, setShowAllExpenses] = useState(false);

    useEffect(() => {
        window.scrollTo(0, 0);
        fetchReportData();
    }, []);

    const fetchReportData = async () => {
        setLoading(true);
        try {
            const response = await fetch(`/api/spending-report/`, {
                credentials: 'include'
            });
            const data = await response.json();
            setReportData(data);
        } catch (err) {
            setError('Failed to load spending report');
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadPDF = async () => {
        setDownloadingPDF(true);
        try {
            // Create printable version
            const printContent = document.getElementById('spending-analytics-content');
            const originalDisplay = printContent.style.display;

            // Temporarily show all content
            printContent.style.display = 'block';

            // Use browser print functionality
            window.print();

            // Restore original display
            printContent.style.display = originalDisplay;
        } catch (err) {
            setError('Failed to export PDF');
        } finally {
            setDownloadingPDF(false);
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

    if (loading) {
        return <div className="financial-page-container"><div className="loading">Loading...</div></div>;
    }

    const categoryColors = {
        food: '#FF6384',
        transportation: '#36A2EB',
        entertainment: '#FFCE56',
        utilities: '#4BC0C0',
        healthcare: '#9966FF',
        education: '#FF9F40',
        other: '#C9CBCF'
    };

    // Chart Data Preparation
    const monthlyTrendData = {
        labels: reportData?.monthly_trend?.map(d => d.month) || [],
        datasets: [
            {
                label: 'Monthly Spending',
                data: reportData?.monthly_trend?.map(d => d.total) || [],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }
        ]
    };

    const categoryBreakdownData = {
        labels: Object.keys(reportData?.category_breakdown || {}).map(c => c.charAt(0).toUpperCase() + c.slice(1)),
        datasets: [
            {
                label: 'Spending by Category',
                data: Object.values(reportData?.category_breakdown || {}),
                backgroundColor: Object.keys(reportData?.category_breakdown || {}).map(c => categoryColors[c] || '#999'),
                borderWidth: 0
            }
        ]
    };

    const cashflowData = {
        labels: reportData?.cashflow_data?.map(d => d.month) || [],
        datasets: [
            {
                label: 'Income',
                data: reportData?.cashflow_data?.map(d => d.income) || [],
                backgroundColor: '#51cf66',
                borderColor: '#51cf66',
                borderWidth: 2
            },
            {
                label: 'Expenses',
                data: reportData?.cashflow_data?.map(d => d.expenses) || [],
                backgroundColor: '#ff6b6b',
                borderColor: '#ff6b6b',
                borderWidth: 2
            }
        ]
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                labels: {
                    color: '#fff'
                }
            }
        },
        scales: {
            x: {
                ticks: { color: '#fff' },
                grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
            y: {
                ticks: { color: '#fff' },
                grid: { color: 'rgba(255, 255, 255, 0.1)' }
            }
        }
    };

    const pieOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                labels: {
                    color: '#fff'
                }
            }
        }
    };

    return (
        <div className="financial-page-container">
            <header className="dashboard-header no-print">
                <div className="header-left">
                    <h1 className="logo">PaisaPro</h1>
                </div>
                <div className="header-right">
                    <Link to="/dashboard" className="nav-link">Dashboard</Link>
                    <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
                </div>
            </header>

            <main className="financial-page-main" style={{ maxWidth: '1400px' }}>
                <div className="page-card" id="spending-analytics-content">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                        <h2>📊 Spending Analytics</h2>
                        <button
                            className="btn btn-primary no-print"
                            onClick={handleDownloadPDF}
                            disabled={downloadingPDF}
                        >
                            <i className="fas fa-file-pdf"></i> {downloadingPDF ? 'Exporting...' : 'Export PDF'}
                        </button>
                    </div>

                    {error && <div className="alert alert-error">{error}</div>}

                    {/* Summary Stats */}
                    <div className="report-summary" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
                        <div className="summary-item" style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '1.5rem', borderRadius: '12px' }}>
                            <h3>Total Expenses</h3>
                            <p className="summary-value">${reportData?.total_expenses?.toFixed(2) || '0.00'}</p>
                        </div>
                        <div className="summary-item" style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '1.5rem', borderRadius: '12px' }}>
                            <h3>Total Transactions</h3>
                            <p className="summary-value">{reportData?.expense_count || 0}</p>
                        </div>
                        <div className="summary-item" style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '1.5rem', borderRadius: '12px' }}>
                            <h3>Top Category</h3>
                            <p className="summary-value" style={{ textTransform: 'capitalize', fontSize: '1.5rem' }}>
                                {reportData?.top_categories?.[0]?.[0] || 'N/A'}
                            </p>
                        </div>
                        <div className="summary-item" style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '1.5rem', borderRadius: '12px' }}>
                            <h3>Avg. Transaction</h3>
                            <p className="summary-value">
                                ${reportData?.expense_count > 0 ? (reportData.total_expenses / reportData.expense_count).toFixed(2) : '0.00'}
                            </p>
                        </div>
                    </div>

                    {/* Charts Section */}
                    <div style={{ display: 'grid', gap: '2rem', marginBottom: '2rem' }}>
                        {/* Monthly Spending Trend */}
                        <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '1.5rem', borderRadius: '12px' }}>
                            <h3 style={{ marginBottom: '1rem', color: '#fff' }}>📈 Monthly Spending Trend</h3>
                            <div style={{ height: '300px' }}>
                                <Line data={monthlyTrendData} options={chartOptions} />
                            </div>
                        </div>

                        {/* Category Breakdown */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                            <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '1.5rem', borderRadius: '12px' }}>
                                <h3 style={{ marginBottom: '1rem', color: '#fff' }}>🎯 Category Breakdown</h3>
                                <div style={{ height: '300px' }}>
                                    <Pie data={categoryBreakdownData} options={pieOptions} />
                                </div>
                            </div>

                            {/* Top Spending Categories */}
                            <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '1.5rem', borderRadius: '12px' }}>
                                <h3 style={{ marginBottom: '1rem', color: '#fff' }}>🏆 Top Spending Categories</h3>
                                <div>
                                    {reportData?.top_categories?.map(([category, amount], index) => (
                                        <div key={category} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', marginBottom: '0.5rem', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '8px' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                                <span style={{ fontSize: '1.5rem', color: categoryColors[category] }}>
                                                    {index + 1}.
                                                </span>
                                                <span style={{ textTransform: 'capitalize', color: '#fff' }}>
                                                    {category}
                                                </span>
                                            </div>
                                            <span style={{ fontWeight: 'bold', color: '#fff' }}>
                                                ${amount.toFixed(2)}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Income vs Expenses Cashflow */}
                        <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '1.5rem', borderRadius: '12px' }}>
                            <h3 style={{ marginBottom: '1rem', color: '#fff' }}>💰 Income vs Expenses Cashflow</h3>
                            <div style={{ height: '300px' }}>
                                <Bar data={cashflowData} options={chartOptions} />
                            </div>
                        </div>
                    </div>

                    {/* Recent Expenses */}
                    {reportData && reportData.recent_expenses && reportData.recent_expenses.length > 0 && (
                        <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '1.5rem', borderRadius: '12px' }}>
                            <h3 style={{ marginBottom: '1rem', color: '#fff' }}>📝 Recent Expenses</h3>
                            <div className="expense-list">
                                {(showAllExpenses ? reportData.recent_expenses : reportData.recent_expenses.slice(0, 3)).map((expense, index) => (
                                    <div key={index} className="expense-item">
                                        <div className="expense-info">
                                            <span className="expense-category" style={{ textTransform: 'capitalize' }}>
                                                {expense.category}
                                            </span>
                                            <span className="expense-description">{expense.description || 'No description'}</span>
                                            <span className="expense-date">{new Date(expense.expense_date).toLocaleDateString()}</span>
                                        </div>
                                        <span className="expense-amount">${parseFloat(expense.amount).toFixed(2)}</span>
                                    </div>
                                ))}
                            </div>
                            {reportData.recent_expenses.length > 3 && (
                                <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                                    <button
                                        onClick={() => setShowAllExpenses(!showAllExpenses)}
                                        className="btn"
                                        style={{
                                            padding: '0.4rem 1rem',
                                            fontSize: '0.85rem',
                                            background: 'rgba(102, 126, 234, 0.2)',
                                            color: '#667eea',
                                            border: '1px solid rgba(102, 126, 234, 0.3)'
                                        }}
                                    >
                                        {showAllExpenses ? 'Show Less' : 'Show All'}
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

                    <Link to="/dashboard" className="btn btn-link no-print" style={{ marginTop: '2rem' }}>← Back to Dashboard</Link>
                </div>
            </main>

            <style>{`
                @media print {
                    .no-print {
                        display: none !important;
                    }
                    .financial-page-container {
                        background: white !important;
                    }
                    .page-card {
                        background: white !important;
                        color: black !important;
                    }
                    .page-card * {
                        color: black !important;
                    }
                }
            `}</style>
        </div>
    );
};

export default SpendingReport;
