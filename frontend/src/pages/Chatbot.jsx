import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Chatbot.css';

const Chatbot = () => {
    const { logout, user } = useAuth();
    const navigate = useNavigate();
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        // Welcome message
        setMessages([{
            role: 'assistant',
            content: '👋 Hello! I\'m your AI Financial Assistant. I can help you with budgeting, saving, investments, and financial planning. How can I assist you today?',
            timestamp: new Date()
        }]);
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!inputMessage.trim() || loading) return;

        const userMessage = inputMessage.trim();
        const newUserMessage = {
            role: 'user',
            content: userMessage,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, newUserMessage]);
        setInputMessage('');
        setLoading(true);

        try {
            // Build history for API
            const history = messages
                .filter(m => m.role !== 'system')
                .map(m => ({ role: m.role, content: m.content }));

            const response = await fetch('http://localhost:8001/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: userMessage,
                    history: history
                })
            });

            if (!response.ok) {
                throw new Error('Failed to get response from server');
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            const botMessage = {
                role: 'assistant',
                content: data.response,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, botMessage]);
        } catch (err) {
            const errorMessage = {
                role: 'assistant',
                content: 'Sorry, I encountered an error. The AI service might be unavailable. Please make sure the FastAPI backend is running on port 8001.',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
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

    const quickQuestions = [
        'How much should I save for emergency fund?',
        'What is a 401(k)?',
        'Help me create a monthly budget',
        'Best investment strategies for beginners'
    ];

    const handleQuickQuestion = (question) => {
        setInputMessage(question);
    };

    const clearChat = () => {
        setMessages([{
            role: 'assistant',
            content: '👋 Hello! I\'m your AI Financial Assistant. I can help you with budgeting, saving, investments, and financial planning. How can I assist you today?',
            timestamp: new Date()
        }]);
    };

    return (
        <div className="chatbot-container">
            <nav className="navbar navbar-expand-lg navbar-dark">
                <div className="container-fluid">
                    <div>
                        <Link to="/" className="navbar-brand">PaisaPro</Link>
                        <p style={{ margin: 0, fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)', paddingLeft: '0.25rem' }}>
                            AI Financial Assistant
                        </p>
                    </div>
                    <div className="d-flex align-items-center">
                        <span className="text-light me-3">{user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : user?.username}</span>
                        <Link to="/dashboard" className="btn btn-sm me-2" style={{
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            color: '#fff',
                            backgroundColor: 'transparent',
                            transition: 'all 0.3s ease'
                        }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.5)';
                                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                                e.currentTarget.style.boxShadow = '0 0 0 3px rgba(255, 255, 255, 0.05)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                                e.currentTarget.style.backgroundColor = 'transparent';
                                e.currentTarget.style.boxShadow = 'none';
                            }}>
                            <i className="fas fa-home me-1"></i>Dashboard
                        </Link>
                        <button onClick={handleLogout} className="btn btn-sm" style={{
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            color: '#fff',
                            backgroundColor: 'transparent',
                            transition: 'all 0.3s ease'
                        }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.5)';
                                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                                e.currentTarget.style.boxShadow = '0 0 0 3px rgba(255, 255, 255, 0.05)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                                e.currentTarget.style.backgroundColor = 'transparent';
                                e.currentTarget.style.boxShadow = 'none';
                            }}>
                            <i className="fas fa-sign-out-alt me-1"></i>Logout
                        </button>
                    </div>
                </div>
            </nav>

            <main className="chatbot-main">
                <div className="chatbot-card">
                    <div className="chatbot-header">
                        <div className="d-flex align-items-center justify-content-between">
                            <div>
                                <h2><i className="fas fa-robot me-2"></i>AI Financial Assistant</h2>
                                <p>Powered by Advanced AI • Get expert financial advice</p>
                            </div>
                            <button onClick={clearChat} className="btn btn-outline-light btn-sm">
                                <i className="fas fa-trash me-1"></i>Clear Chat
                            </button>
                        </div>
                    </div>

                    <div className="messages-container">
                        {messages.map((msg, index) => (
                            <div key={index} className={`message ${msg.role}`}>
                                <div className="message-content">
                                    <div className="message-avatar">
                                        {msg.role === 'assistant' ? '🤖' : '👤'}
                                    </div>
                                    <div className="message-bubble">
                                        <div className="message-text">
                                            {msg.content}
                                        </div>
                                        <div className="message-time">
                                            {msg.timestamp.toLocaleTimeString()}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}

                        {loading && (
                            <div className="message assistant">
                                <div className="message-content">
                                    <div className="message-avatar">🤖</div>
                                    <div className="message-bubble">
                                        <div className="typing-indicator">
                                            <span></span>
                                            <span></span>
                                            <span></span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {messages.length === 1 && (
                        <div className="quick-questions">
                            <p><i className="fas fa-lightbulb me-2"></i>Quick questions to get started:</p>
                            <div className="quick-questions-grid">
                                {quickQuestions.map((question, index) => (
                                    <button
                                        key={index}
                                        className="quick-question-btn"
                                        onClick={() => handleQuickQuestion(question)}
                                    >
                                        {question}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="chat-input-form">
                        <input
                            type="text"
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            placeholder="Ask me anything about finances..."
                            disabled={loading}
                            className="chat-input"
                        />
                        <button type="submit" className="btn btn-primary chat-send-btn" disabled={loading || !inputMessage.trim()}>
                            <i className="fas fa-paper-plane me-1"></i>
                            {loading ? 'Sending...' : 'Send'}
                        </button>
                    </form>
                </div>
            </main>
        </div>
    );
};

export default Chatbot;
