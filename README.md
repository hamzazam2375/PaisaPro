
# 💰 PaisaPro - Financial Management Platform

Personal finance app with React frontend, Django REST API, and FastAPI services for AI insights, expense tracking, price comparison, and chatbot assistance.

## 🚀 Quick Start

```powershell
pip install -r requirements.txt
cd frontend && npm install && cd ..
python manage.py migrate
# VS Code: Ctrl+Shift+P → "Tasks: Run Task" → "Start All PaisaPro Services"
# Or run backend and frontend manually
```


## 🌟 Main Features

- User authentication (OTP email verification)
- Expense, budget, savings, and income management
- AI-powered financial insights and chatbot
- Price comparison (Daraz, Alfatah, Imtiaz)
- Smart shopping cart with price optimization
- Market sentiment analysis (FinBERT)
- PDF report generation


## 📋 Prerequisites
- Python 3.12+
- Node.js 18+
- Git


## ⚡ Setup

```powershell
git clone https://github.com/hamzazam2375/PaisaPro.git
cd PaisaPro
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd frontend && npm install && cd ..
python manage.py migrate
```

Start all services using VS Code tasks or manually:
- Backend: Django + FastAPI (ports 8000, 8001, 8002)
- Frontend: React (port 3000)


Copy `.env.example` to `.env` and fill in your credentials (email, API keys, etc).


## 📚 Documentation
- See `PROJECT_STRUCTURE.md` for folder details
- Django Admin: http://127.0.0.1:8000/admin/


## 🎯 Main Pages & Commands
- Dashboard, expense, savings, income, profile, reports, chatbot, price comparison
- Management commands: `python manage.py detect_unusual_expenses`, `python manage.py clearsessions`


## 🔧 Configuration
- Email: Use Gmail App Password in `.env`
- AI: Add OpenAI or Gemini API keys in `.env` (optional)


## 🏗️ Architecture
- React SPA frontend
- Django REST API backend
- FastAPI microservices (AI, scraping)


## 📦 AI Dependencies
Install for FastAPI backend:
```powershell
pip install fastapi uvicorn torch transformers selenium beautifulsoup4 lxml reportlab
```


## 🚀 Deployment
- Use PostgreSQL for production (see `settings.py`)
- Set `DEBUG = False`, configure `ALLOWED_HOSTS`, use environment variables


## 🛠️ Troubleshooting
- Check ports (8000, 8001, 8002, 3000) are free
- Ensure `.env` is configured
- For scraping errors, check ChromeDriver and website anti-bot measures


## 🤝 Contributing
Pull requests welcome!


## 📄 License
MIT License


## 👨‍💻 Author
Hamza Azam ([hamzazam2375](https://github.com/hamzazam2375))

## 📊 Performance Notes

- **Initial Load:** FinBERT model downloads automatically (~400MB, one-time)
- **Chatbot Response:** 2-5 seconds with OpenRouter API
- **Price Comparison:** 30-180 seconds (depends on website speed & anti-bot measures)
- **Sentiment Analysis:** 5-15 seconds (including news scraping)
- **Database:** SQLite suitable for <10K users, PostgreSQL recommended for production

## 🔐 API Keys Setup

### OpenRouter (for Chatbot)
1. Sign up: https://openrouter.ai/
2. Get free API key: https://openrouter.ai/keys
3. Add to `.env`: `OPENROUTER_API_KEY=sk-or-v1-...`
4. **Fallback models configured:** Llama-3.3-70B → Llama-3.1-8B → Gemma-2-9B → Phi-3-Mini

### Google Cloud (for Email)
1. Enable Gmail API or use App Passwords
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Add to `.env`: `EMAIL_HOST_PASSWORD=<16-char-password>`

## 🧪 Testing

### Manual Testing Checklist
- [ ] User registration with OTP verification
- [ ] Login and authentication flow
- [ ] Add income and fixed expenses
- [ ] Add savings goal and track progress
- [ ] Add other expenses with categorization
- [ ] View spending report charts
- [ ] Check budget status and alerts
- [ ] Test chatbot with financial questions
- [ ] Compare prices across 3 platforms
- [ ] Analyze company sentiment with PDF download
- [ ] Profile settings update
- [ ] Password reset with OTP

### Run Unit Tests (if available)
```bash
python manage.py test sda_app
```

## 🚧 Known Limitations

1. **Web Scraping Reliability:** Price comparison depends on external websites; may fail due to:
   - Anti-bot detection (Cloudflare, reCAPTCHA)
   - Website structure changes
   - Network timeouts
   - Rate limiting

2. **FinBERT Language:** Optimized for English financial news only

3. **Real-time Data:** Prices and sentiment are scraped at request time (not cached)

4. **ChromeDriver Dependency:** Requires manual installation and version matching

5. **Single Currency:** USD conversion hardcoded (1 USD = 278 PKR)

## 🛣️ Future Enhancements

- [ ] Add Redis caching for scraped data
- [ ] Implement background Celery tasks for scraping
- [ ] Support multiple currencies with live exchange rates
- [ ] Add Playwright as Selenium alternative
- [ ] Integrate more LLM providers (Claude, Gemini)
- [ ] Add budget forecasting with ML models
- [ ] Implement expense receipt OCR
- [ ] Add social expense sharing features
- [ ] Create mobile app (React Native)
- [ ] Add export to Excel/CSV

## 🙏 Acknowledgments

- **Django** - Backend framework
- **React** - Frontend library
- **FastAPI** - AI services framework
- **Hugging Face** - FinBERT sentiment model
- **OpenRouter** - LLM API aggregator
- **Selenium** - Web automation
- **Chart.js** - Data visualization
- **Vite** - Fast build tool
