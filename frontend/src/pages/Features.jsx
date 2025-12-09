import { Link } from 'react-router-dom';
import './InfoPages.css';

const Features = () => {
    return (
        <div className="info-page">
            <header className="info-header">
                <Link to="/" className="logo">PaisaPro</Link>
                <Link to="/" className="back-link">← Back to Home</Link>
            </header>

            <main className="info-content">
                <h1>Features</h1>
                <p className="subtitle">Everything you need to manage your finances effectively</p>

                <div className="features-grid">
                    <div className="feature-card">
                        <div className="feature-icon">💰</div>
                        <h3>Expense Tracking</h3>
                        <p>Track all your expenses with detailed categorization and real-time updates.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon">📊</div>
                        <h3>Budget Management</h3>
                        <p>Set category-wise budgets and get alerts when you're close to limits.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon">💳</div>
                        <h3>Account Overview</h3>
                        <p>Monitor all your accounts and track your total balance in one place.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon">📈</div>
                        <h3>Spending Analytics</h3>
                        <p>Visualize your spending patterns with interactive charts and reports.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon">🤖</div>
                        <h3>AI Financial Advisor</h3>
                        <p>Get personalized financial advice powered by advanced AI technology.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon">🛒</div>
                        <h3>Shopping Lists</h3>
                        <p>Create and manage shopping lists with price comparison features.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon">💡</div>
                        <h3>Financial Insights</h3>
                        <p>Receive intelligent recommendations to improve your financial health.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon">🔔</div>
                        <h3>Smart Notifications</h3>
                        <p>Stay informed with real-time alerts for important financial events.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon">🏷️</div>
                        <h3>Price Comparison</h3>
                        <p>Compare prices across vendors to find the best deals.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon">📱</div>
                        <h3>Mobile Responsive</h3>
                        <p>Access your financial data seamlessly on any device.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon">🎯</div>
                        <h3>Savings Goals</h3>
                        <p>Set and track savings goals to achieve your financial objectives.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon">📉</div>
                        <h3>Market Sentiment</h3>
                        <p>AI-powered analysis of company performance and market trends.</p>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Features;
