
# PaisaPro - Project Structure (2025)

## Main Folders

```
PaisaPro/
│
├── frontend/                # React frontend (UI, pages, components, contexts, services)
│   ├── src/
│   │   ├── pages/           # All React pages (AddExpense, Dashboard, etc.)
│   │   ├── components/      # Reusable components (NotificationBell, ProtectedRoute, etc.)
│   │   ├── contexts/        # React context providers
│   │   ├── services/        # API communication (api.js)
│   │   ├── App.jsx, main.jsx, index.css, etc.
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── ...
│
├── sda_app/                 # Django/FastAPI backend app
│   ├── migrations/          # Database migrations
│   ├── __init__.py
│   ├── admin.py
│   ├── api_urls.py
│   ├── api_views.py
│   ├── apps.py
│   ├── chatbot_service.py
│   ├── email_service.py
│   ├── fastapi_backend.py   # FastAPI backend (price comparison, AI, etc.)
│   ├── financial_analyzer.py
│   ├── forms.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── SDA_Project/             # Django project settings
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── .vscode/                 # VS Code tasks/config (optional)
├── manage.py                # Django CLI
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
├── PROJECT_STRUCTURE.md     # This file
├── start_backend.ps1        # Backend startup script
├── .env.example             # Example environment config
└── ...
```

## Notes
- Do NOT commit `venv/`, `__pycache__/`, or `.env` (add to `.gitignore`).
- All backend code is in `sda_app/` and `SDA_Project/`.
- All frontend code is in `frontend/`.
- Use VS Code tasks for unified startup.

## Clean Separation
- Frontend: React SPA (UI, routing, API calls)
- Backend: Django REST API + FastAPI (business logic, scraping, AI)

## For details, see README.md

## File Organization Rules

### ✅ Frontend (React) - `frontend/` directory
**Everything related to UI and user interface:**
- React components (.jsx files)
- CSS stylesheets (.css files)
- API client code (api.js)
- React contexts and hooks
- Frontend configuration (package.json, vite.config.js)
- Legacy HTML templates (archived in `frontend/legacy/`)

### ✅ Backend (Django) - Root & `backend/` directory
**Everything related to business logic and data:**
- REST API endpoints (api_views.py)
- Database models (models.py)
- Serializers (serializers.py)
- Business logic services (chatbot_service.py, email_service.py, financial_analyzer.py)
- Django admin configuration (admin.py)
- Management commands
- Database migrations
- Django settings (config/settings.py)

## Clean Separation Benefits

1. **Clear Responsibility**: Frontend handles UI, Backend handles data/logic
2. **Independent Development**: Frontend and backend can be developed separately
3. **Easy Deployment**: 
   - Frontend builds to static files
   - Backend serves API endpoints
4. **Modern Architecture**: Industry-standard SPA + REST API pattern
5. **Better Performance**: React handles routing, no page reloads

## How It Works

### Development Mode
```
Frontend (localhost:3000) ← Vite Dev Server
    ↓ HTTP Requests
Backend (localhost:8000) ← Django Server
    ↓
Database (PostgreSQL)
```

### Production Mode
```
Browser → Django (localhost:8000)
    ├─ /api/* → REST API Endpoints
    └─ /* → Serve React Static Files
         ↓
    Database (PostgreSQL)
```

## Key Configuration Files

### Frontend Configuration
- `frontend/package.json` - NPM dependencies & scripts
- `frontend/vite.config.js` - Build configuration, API proxy
- `frontend/src/main.jsx` - React entry point
- `frontend/src/App.jsx` - React Router configuration

### Backend Configuration
- `config/settings.py` - Django settings, CORS, REST framework
- `config/urls.py` - URL routing (admin + API)
- `backend/api_urls.py` - API endpoint definitions
- `backend/api_views.py` - API endpoint implementations

## Environment Variables
All configuration in `.env` file:
- Database credentials
- Email settings
- API keys (Gemini)
- Django secret key

---
 
**Architecture**: React SPA + Django REST API  
**Status**: Clean separation complete ✅