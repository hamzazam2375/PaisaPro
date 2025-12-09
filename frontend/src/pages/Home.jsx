import { Link } from 'react-router-dom';
import './Home.css';

const Home = () => {
    return (
        <div className="home-container">
            <nav className="navbar">
                <div className="nav-brand">
                    <h1>PaisaPro</h1>
                    <span className="tagline">Financial Intelligence Platform</span>
                </div>
                <div className="nav-links">
                    <Link to="/login" className="btn btn-outline">Login</Link>
                    <Link to="/signup" className="btn btn-primary">Get Started</Link>
                </div>
            </nav>

            <section className="hero">
                <div className="hero-content">
                    <div className="badge">AI-Powered Financial Platform</div>
                    <h1 className="hero-title">Take Control of Your Financial Future</h1>
                    <p className="hero-subtitle">
                        Comprehensive financial management platform combining intelligent expense tracking,
                        real-time budget monitoring, AI-powered advisory, and advanced market analytics
                        to help you make smarter financial decisions.
                    </p>
                    <div className="hero-stats">
                        <div className="stat-item">
                            <div className="stat-number">10,000+</div>
                            <div className="stat-label">Active Users</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-number">$2M+</div>
                            <div className="stat-label">Money Tracked</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-number">95%</div>
                            <div className="stat-label">Success Rate</div>
                        </div>
                    </div>
                    <div className="hero-actions">
                        <Link to="/signup" className="btn btn-primary btn-lg">
                            Start Free Trial
                            <i className="fas fa-arrow-right ms-2"></i>
                        </Link>
                        <Link to="/login" className="btn btn-outline btn-lg">Sign In</Link>
                    </div>
                </div>
            </section>

            <section className="features">
                <div className="section-header">
                    <h2>Complete Financial Management Suite</h2>
                    <p>Everything you need to master your finances in one intelligent platform</p>
                </div>
                <div className="features-grid">
                    <div className="feature-card">
                        <div className="feature-icon gradient-purple">
                            <i className="fas fa-chart-line"></i>
                        </div>
                        <h3>Real-Time Expense Tracking</h3>
                        <p>Monitor every transaction with automatic categorization and intelligent pattern recognition to understand your spending habits</p>
                    </div>
                    <div className="feature-card">
                        <div className="feature-icon gradient-blue">
                            <i className="fas fa-wallet"></i>
                        </div>
                        <h3>Smart Budget Management</h3>
                        <p>Set custom spending limits, receive proactive alerts, and stay on track with automated budget optimization recommendations</p>
                    </div>
                    <div className="feature-card">
                        <div className="feature-icon gradient-gold">
                            <i className="fas fa-robot"></i>
                        </div>
                        <h3>AI Financial Advisor</h3>
                        <p>24/7 access to intelligent financial guidance powered by advanced language models for personalized recommendations and insights</p>
                    </div>
                    <div className="feature-card">
                        <div className="feature-icon gradient-green">
                            <i className="fas fa-chart-bar"></i>
                        </div>
                        <h3>Advanced Analytics Dashboard</h3>
                        <p>Comprehensive reports with interactive visualizations, spending trends, and predictive analytics for informed decision-making</p>
                    </div>
                    <div className="feature-card">
                        <div className="feature-icon gradient-pink">
                            <i className="fas fa-piggy-bank"></i>
                        </div>
                        <h3>Savings Goal Tracker</h3>
                        <p>Define financial objectives, monitor progress with visual milestones, and receive motivational insights to achieve your targets</p>
                    </div>
                    <div className="feature-card featured">
                        <div className="feature-badge">Most Popular</div>
                        <div className="feature-icon gradient-orange">
                            <i className="fas fa-brain"></i>
                        </div>
                        <h3>Market Intelligence</h3>
                        <p>AI-powered sentiment analysis and price comparison tools to make informed investment and purchase decisions</p>
                    </div>
                </div>
                <section className="cta-section">
                    <div className="cta-content">
                        <h2>Ready to Transform Your Financial Life?</h2>
                        <p>Join thousands of users who have taken control of their finances with PaisaPro</p>
                        <Link to="/signup" className="btn btn-primary btn-lg">
                            Create Free Account
                            <i className="fas fa-arrow-right ms-2"></i>
                        </Link>
                    </div>
                </section>
            </section>

            <footer className="footer">
                <div className="footer-content">
                    <div className="footer-section">
                        <h3>PaisaPro</h3>
                        <p>Your intelligent financial management partner</p>
                    </div>
                    <div className="footer-section">
                        <h4>Platform</h4>
                        <ul>
                            <li><Link to="/features">Features</Link></li>
                            <li><Link to="/security">Security</Link></li>
                        </ul>
                    </div>
                    <div className="footer-section">
                        <h4>Company</h4>
                        <ul>
                            <li><Link to="/about">About Us</Link></li>
                            <li><Link to="/contact">Contact</Link></li>
                            <li><Link to="/support">Support</Link></li>
                        </ul>
                    </div>
                </div>
                <div className="footer-bottom">
                    <p>&copy; 2025 PaisaPro. All rights reserved. Built with intelligence and care.</p>
                </div>
            </footer>
        </div>
    );
};

export default Home;
