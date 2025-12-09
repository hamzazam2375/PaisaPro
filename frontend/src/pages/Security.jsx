import { Link } from 'react-router-dom';
import './InfoPages.css';

const Security = () => {
    return (
        <div className="info-page">
            <header className="info-header">
                <Link to="/" className="logo">PaisaPro</Link>
                <Link to="/" className="back-link">← Back to Home</Link>
            </header>

            <main className="info-content">
                <h1>Security</h1>
                <p className="subtitle">Your financial data security is our top priority</p>

                <div className="security-grid">
                    <div className="security-card">
                        <div className="security-icon">🔒</div>
                        <h3>End-to-End Encryption</h3>
                        <p>All your financial data is encrypted using industry-standard AES-256 encryption, ensuring your information remains private and secure.</p>
                    </div>

                    <div className="security-card">
                        <div className="security-icon">🔐</div>
                        <h3>Secure Authentication</h3>
                        <p>Multi-factor authentication and secure password policies protect your account from unauthorized access.</p>
                    </div>

                    <div className="security-card">
                        <div className="security-icon">🛡️</div>
                        <h3>Data Protection</h3>
                        <p>Your personal and financial information is protected with bank-level security protocols and regular security audits.</p>
                    </div>

                    <div className="security-card">
                        <div className="security-icon">👁️</div>
                        <h3>Privacy First</h3>
                        <p>We never sell your data to third parties. Your financial information belongs to you and you alone.</p>
                    </div>

                    <div className="security-card">
                        <div className="security-icon">🔄</div>
                        <h3>Regular Backups</h3>
                        <p>Automated backups ensure your data is safe and can be recovered in case of any issues.</p>
                    </div>

                    <div className="security-card">
                        <div className="security-icon">⚡</div>
                        <h3>Real-time Monitoring</h3>
                        <p>24/7 security monitoring detects and prevents suspicious activities on your account.</p>
                    </div>

                    <div className="security-card">
                        <div className="security-icon">📱</div>
                        <h3>Secure Sessions</h3>
                        <p>Automatic session timeouts and secure cookie management protect you from session hijacking.</p>
                    </div>

                    <div className="security-card">
                        <div className="security-icon">✅</div>
                        <h3>Compliance</h3>
                        <p>We comply with international data protection regulations and financial security standards.</p>
                    </div>
                </div>

                <div className="security-commitment">
                    <h2>Our Security Commitment</h2>
                    <p>At PaisaPro, we understand that trust is earned through consistent security practices. We continuously update our security measures to stay ahead of potential threats and ensure your financial data remains protected at all times.</p>
                </div>
            </main>
        </div>
    );
};

export default Security;
