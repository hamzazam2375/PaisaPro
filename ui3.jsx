import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, DollarSign, TrendingUp, MessageSquare, Trash2, User, Bot } from 'lucide-react';

export default function FinancialChatbotApp() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your Financial Assistant. I can help you with budgeting, saving, investments, and financial planning. How can I assist you today?'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setError('');

    // Add user message to chat
    const newMessages = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);
    setLoading(true);

    try {
      // Build history for API (exclude system messages)
      const history = messages
        .filter(m => m.role !== 'system')
        .map(m => ({ role: m.role, content: m.content }));

      const response = await fetch('http://localhost:8000/api/chat', {
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

      // Add assistant response
      setMessages([...newMessages, { role: 'assistant', content: data.response }]);
    } catch (err) {
      setError(err.message || 'An error occurred. Please try again.');
      setMessages(newMessages);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: 'Hello! I\'m your Financial Assistant. I can help you with budgeting, saving, investments, and financial planning. How can I assist you today?'
      }
    ]);
    setError('');
  };

  const quickQuestions = [
    "How much should I save for emergency fund?",
    "What is a 401(k)?",
    "Help me create a monthly budget",
    "Best investment strategies for beginners"
  ];

  const handleQuickQuestion = (question) => {
    setInput(question);
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(to bottom right, #0f172a, #1e293b, #0f172a)',
      color: '#f1f5f9',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header */}
      <div style={{
        borderBottom: '1px solid #334155',
        backgroundColor: 'rgba(15, 23, 42, 0.8)',
        backdropFilter: 'blur(10px)',
        position: 'sticky',
        top: 0,
        zIndex: 10
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '20px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
            <div style={{
              padding: '12px',
              background: 'linear-gradient(to bottom right, #10b981, #059669)',
              borderRadius: '12px'
            }}>
              <DollarSign size={28} color="#fff" />
            </div>
            <div>
              <h1 style={{
                fontSize: '26px',
                fontWeight: 'bold',
                background: 'linear-gradient(to right, #34d399, #10b981)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                margin: 0
              }}>
                Financial Assistant
              </h1>
              <p style={{color: '#94a3b8', fontSize: '14px', margin: '2px 0 0 0'}}>
                Your AI-powered financial advisor
              </p>
            </div>
          </div>
          
          <button
            onClick={clearChat}
            style={{
              padding: '10px 20px',
              background: 'transparent',
              border: '1px solid #334155',
              borderRadius: '10px',
              color: '#f1f5f9',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              fontWeight: '500',
              transition: 'all 0.3s'
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#1e293b';
              e.target.style.borderColor = '#10b981';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = 'transparent';
              e.target.style.borderColor = '#334155';
            }}
          >
            <Trash2 size={16} />
            Clear Chat
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div style={{
        flex: 1,
        maxWidth: '1200px',
        width: '100%',
        margin: '0 auto',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Messages Container */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          marginBottom: '24px',
          paddingRight: '8px'
        }}>
          {messages.map((message, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                gap: '12px',
                marginBottom: '20px',
                alignItems: 'flex-start'
              }}
            >
              {/* Avatar */}
              <div style={{
                flexShrink: 0,
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                background: message.role === 'user' 
                  ? 'linear-gradient(to bottom right, #8b5cf6, #ec4899)'
                  : 'linear-gradient(to bottom right, #10b981, #059669)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {message.role === 'user' ? (
                  <User size={20} color="#fff" />
                ) : (
                  <Bot size={20} color="#fff" />
                )}
              </div>

              {/* Message Content */}
              <div style={{
                flex: 1,
                backgroundColor: message.role === 'user' ? '#1e293b' : '#0f172a',
                border: '1px solid #334155',
                borderRadius: '12px',
                padding: '16px',
                maxWidth: '80%'
              }}>
                <div style={{
                  fontSize: '12px',
                  fontWeight: '600',
                  color: message.role === 'user' ? '#a78bfa' : '#34d399',
                  marginBottom: '8px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}>
                  {message.role === 'user' ? 'You' : 'Assistant'}
                </div>
                <div style={{
                  fontSize: '15px',
                  lineHeight: '1.6',
                  color: '#e2e8f0',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}>
                  {message.content}
                </div>
              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {loading && (
            <div style={{
              display: 'flex',
              gap: '12px',
              marginBottom: '20px',
              alignItems: 'flex-start'
            }}>
              <div style={{
                flexShrink: 0,
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                background: 'linear-gradient(to bottom right, #10b981, #059669)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Bot size={20} color="#fff" />
              </div>
              <div style={{
                backgroundColor: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '12px',
                padding: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <Loader2 size={18} color="#10b981" className="spin" />
                <span style={{color: '#94a3b8', fontSize: '14px'}}>Thinking...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Questions (show only when chat is empty) */}
        {messages.length === 1 && (
          <div style={{marginBottom: '20px'}}>
            <div style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#94a3b8',
              marginBottom: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <MessageSquare size={16} />
              Quick Questions
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '12px'
            }}>
              {quickQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickQuestion(question)}
                  style={{
                    padding: '12px 16px',
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '10px',
                    color: '#e2e8f0',
                    fontSize: '14px',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.3s'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = '#334155';
                    e.target.style.borderColor = '#10b981';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = '#1e293b';
                    e.target.style.borderColor = '#334155';
                  }}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div style={{
            marginBottom: '16px',
            padding: '12px 16px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid #ef4444',
            borderRadius: '10px',
            color: '#fca5a5',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}

        {/* Input Area */}
        <div style={{
          backgroundColor: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '16px',
          padding: '16px',
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-end'
        }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about finance..."
            disabled={loading}
            rows={1}
            style={{
              flex: 1,
              backgroundColor: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '10px',
              padding: '12px 16px',
              color: '#f1f5f9',
              fontSize: '15px',
              outline: 'none',
              resize: 'none',
              minHeight: '48px',
              maxHeight: '120px',
              fontFamily: 'inherit'
            }}
            onInput={(e) => {
              e.target.style.height = 'auto';
              e.target.style.height = e.target.scrollHeight + 'px';
            }}
          />
          
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            style={{
              padding: '12px 24px',
              background: (!input.trim() || loading) 
                ? '#334155' 
                : 'linear-gradient(to right, #10b981, #059669)',
              border: 'none',
              borderRadius: '10px',
              color: '#fff',
              cursor: (!input.trim() || loading) ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '15px',
              fontWeight: '600',
              transition: 'all 0.3s',
              height: '48px'
            }}
            onMouseEnter={(e) => {
              if (input.trim() && !loading) {
                e.target.style.background = 'linear-gradient(to right, #34d399, #10b981)';
              }
            }}
            onMouseLeave={(e) => {
              if (input.trim() && !loading) {
                e.target.style.background = 'linear-gradient(to right, #10b981, #059669)';
              }
            }}
          >
            {loading ? (
              <Loader2 size={20} className="spin" />
            ) : (
              <Send size={20} />
            )}
            Send
          </button>
        </div>

        {/* Footer Info */}
        <div style={{
          marginTop: '16px',
          textAlign: 'center',
          color: '#64748b',
          fontSize: '13px'
        }}>
          <TrendingUp size={14} style={{display: 'inline', marginRight: '6px'}} />
          Powered by AI • Financial advice for educational purposes only
        </div>
      </div>

      <style>{`
        .spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        /* Custom scrollbar */
        *::-webkit-scrollbar {
          width: 8px;
        }
        *::-webkit-scrollbar-track {
          background: #0f172a;
          border-radius: 10px;
        }
        *::-webkit-scrollbar-thumb {
          background: #334155;
          border-radius: 10px;
        }
        *::-webkit-scrollbar-thumb:hover {
          background: #475569;
        }
      `}</style>
    </div>
  );
}