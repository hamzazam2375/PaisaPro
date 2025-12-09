import { useState } from 'react';
import { Link } from 'react-router-dom';
import './InfoPages.css';

const Support = () => {
    const [expandedFaq, setExpandedFaq] = useState(null);

    const faqs = [
        {
            question: "How do I get started with PaisaPro?",
            answer: "Simply sign up for a free account, verify your email, and you're ready to go! You can start by adding your income, creating budgets, and tracking your first expense."
        },
        {
            question: "Is my financial data secure?",
            answer: "Absolutely! We use bank-level encryption (AES-256) to protect your data. We never sell your information to third parties and comply with international data protection standards."
        },
        {
            question: "Can I access PaisaPro on mobile devices?",
            answer: "Yes! PaisaPro is fully responsive and works seamlessly on all devices including smartphones, tablets, and desktop computers."
        },
        {
            question: "How does the AI Financial Advisor work?",
            answer: "Our AI analyzes your spending patterns, income, and financial goals to provide personalized recommendations and insights to help you make better financial decisions."
        },
        {
            question: "Can I export my financial data?",
            answer: "Yes, you can export your spending reports as PDF and download your transaction history for your records."
        },
        {
            question: "How do I set up budget alerts?",
            answer: "Go to Budget Overview, create category-wise budgets, and you'll automatically receive alerts when you're approaching or exceeding your limits."
        },
        {
            question: "What payment methods do you support?",
            answer: "PaisaPro is currently free to use. We're focused on helping you track and manage your existing accounts and expenses."
        },
        {
            question: "How do I delete my account?",
            answer: "You can delete your account from Profile Settings. Please note that this action is permanent and will delete all your financial data."
        }
    ];

    const toggleFaq = (index) => {
        setExpandedFaq(expandedFaq === index ? null : index);
    };

    return (
        <div className="info-page">
            <header className="info-header">
                <Link to="/" className="logo">PaisaPro</Link>
                <Link to="/" className="back-link">← Back to Home</Link>
            </header>

            <main className="info-content">
                <h1>Support Center</h1>
                <p className="subtitle">Find answers and get help when you need it</p>

                <div className="support-grid">
                    <div className="support-card">
                        <div className="support-icon">📚</div>
                        <h3>Documentation</h3>
                        <p>Comprehensive guides and tutorials to help you make the most of PaisaPro's features.</p>
                    </div>

                    <div className="support-card">
                        <div className="support-icon">💬</div>
                        <h3>Live Chat</h3>
                        <p>Chat with our support team in real-time during business hours (9 AM - 6 PM, Mon-Fri).</p>
                    </div>

                    <div className="support-card">
                        <div className="support-icon">📧</div>
                        <h3>Email Support</h3>
                        <p>Send us an email at paisaproteam@gmail.com and we'll respond within 24 hours.</p>
                    </div>

                    <div className="support-card">
                        <div className="support-icon">🎥</div>
                        <h3>Video Tutorials</h3>
                        <p>Watch step-by-step video guides to learn how to use different features.</p>
                    </div>
                </div>

                <div className="faq-section">
                    <h2>Frequently Asked Questions</h2>
                    <div className="faq-list">
                        {faqs.map((faq, index) => (
                            <div key={index} className="faq-item">
                                <button
                                    className={`faq-question ${expandedFaq === index ? 'active' : ''}`}
                                    onClick={() => toggleFaq(index)}
                                >
                                    <span>{faq.question}</span>
                                    <span className="faq-icon">{expandedFaq === index ? '−' : '+'}</span>
                                </button>
                                {expandedFaq === index && (
                                    <div className="faq-answer">
                                        {faq.answer}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                <div className="help-section">
                    <h2>Still Need Help?</h2>
                    <p>Can't find what you're looking for? Our support team is ready to assist you.</p>
                    <div className="help-buttons">
                        <Link to="/contact" className="help-button secondary">Email Us</Link>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Support;
