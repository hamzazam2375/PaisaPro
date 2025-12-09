import { useState } from 'react';
import { Link } from 'react-router-dom';
import './InfoPages.css';

const Contact = () => {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        subject: '',
        message: ''
    });
    const [submitted, setSubmitted] = useState(false);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        // In a real application, you would send this to your backend
        console.log('Contact form submitted:', formData);
        setSubmitted(true);
        setTimeout(() => {
            setSubmitted(false);
            setFormData({ name: '', email: '', subject: '', message: '' });
        }, 3000);
    };

    return (
        <div className="info-page">
            <header className="info-header">
                <Link to="/" className="logo">PaisaPro</Link>
                <Link to="/" className="back-link">← Back to Home</Link>
            </header>

            <main className="info-content">
                <h1>Contact Us</h1>
                <p className="subtitle">We'd love to hear from you</p>

                <div className="contact-container">
                    <div className="contact-info">
                        <h2>Get in Touch</h2>
                        <p>Have questions, feedback, or need assistance? Our team is here to help you make the most of PaisaPro.</p>

                        <div className="contact-methods">
                            <div className="contact-method">
                                <div className="method-icon">📧</div>
                                <div>
                                    <h3>Email</h3>
                                    <p>paisaproteam@gmail.com</p>
                                </div>
                            </div>

                            <div className="contact-method">
                                <div className="method-icon">💬</div>
                                <div>
                                    <h3>Live Chat</h3>
                                    <p>Available 9 AM - 6 PM (Mon-Fri)</p>
                                </div>
                            </div>

                            <div className="contact-method">
                                <div className="method-icon">🌐</div>
                                <div>
                                    <h3>Social Media</h3>
                                    <p>Follow us for updates and tips</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="contact-form-section">
                        <h2>Send us a Message</h2>
                        {submitted && (
                            <div className="success-message">
                                ✅ Thank you! We've received your message and will get back to you soon.
                            </div>
                        )}
                        <form onSubmit={handleSubmit} className="contact-form">
                            <div className="form-group">
                                <label htmlFor="name">Name *</label>
                                <input
                                    type="text"
                                    id="name"
                                    name="name"
                                    value={formData.name}
                                    onChange={handleChange}
                                    required
                                    placeholder="Your full name"
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="email">Email *</label>
                                <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    required
                                    placeholder="your.email@example.com"
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="subject">Subject *</label>
                                <input
                                    type="text"
                                    id="subject"
                                    name="subject"
                                    value={formData.subject}
                                    onChange={handleChange}
                                    required
                                    placeholder="What is this about?"
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="message">Message *</label>
                                <textarea
                                    id="message"
                                    name="message"
                                    value={formData.message}
                                    onChange={handleChange}
                                    required
                                    rows="6"
                                    placeholder="Tell us how we can help you..."
                                ></textarea>
                            </div>

                            <button type="submit" className="submit-button">
                                Send Message
                            </button>
                        </form>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Contact;
