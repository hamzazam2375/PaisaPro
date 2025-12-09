import { Link } from 'react-router-dom';
import './InfoPages.css';

const AboutUs = () => {
    return (
        <div className="info-page">
            <header className="info-header">
                <Link to="/" className="logo">PaisaPro</Link>
                <Link to="/" className="back-link">← Back to Home</Link>
            </header>

            <main className="info-content">
                <h1>About Us</h1>
                <p className="subtitle">Empowering people to make smarter financial decisions</p>

                <div className="about-section">
                    <h2>Our Mission</h2>
                    <p>At PaisaPro, we believe that everyone deserves access to intelligent financial management tools. Our mission is to simplify personal finance through innovative technology, making it easy for anyone to track expenses, manage budgets, and achieve their financial goals.</p>
                </div>

                <div className="about-section">
                    <h2>What We Do</h2>
                    <p>PaisaPro is an AI-powered financial management platform that combines expense tracking, budget management, and intelligent insights in one comprehensive solution. We help individuals take control of their finances with features like:</p>
                    <ul className="about-list">
                        <li>Real-time expense tracking and categorization</li>
                        <li>Smart budget management with overspend alerts</li>
                        <li>AI-powered financial advice and recommendations</li>
                        <li>Interactive spending analytics and visualizations</li>
                        <li>Price comparison and shopping list management</li>
                        <li>Market sentiment analysis for informed decisions</li>
                    </ul>
                </div>

                <div className="about-section">
                    <h2>Our Values</h2>
                    <div className="values-grid">
                        <div className="value-card">
                            <h3>🎯 User-Centric</h3>
                            <p>We design every feature with our users' needs in mind, ensuring a seamless and intuitive experience.</p>
                        </div>
                        <div className="value-card">
                            <h3>🔒 Privacy & Security</h3>
                            <p>Your financial data is sacred. We implement bank-level security to protect your information.</p>
                        </div>
                        <div className="value-card">
                            <h3>💡 Innovation</h3>
                            <p>We continuously evolve, leveraging AI and cutting-edge technology to provide intelligent solutions.</p>
                        </div>
                        <div className="value-card">
                            <h3>🤝 Transparency</h3>
                            <p>We believe in honest communication and clear insights about your financial health.</p>
                        </div>
                    </div>
                </div>

                <div className="about-section">
                    <h2>Why Choose PaisaPro?</h2>
                    <p>Unlike traditional finance apps, PaisaPro combines the power of artificial intelligence with user-friendly design to create a truly intelligent financial assistant. We don't just track your money—we help you understand it, optimize it, and make it work harder for you.</p>
                </div>
            </main>
        </div>
    );
};

export default AboutUs;
