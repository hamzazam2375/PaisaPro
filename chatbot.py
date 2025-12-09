# backend.py - Complete Backend with OOP, SOLID Principles & Design Patterns

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from abc import ABC, abstractmethod
from dataclasses import dataclass
import requests
import json
import logging
import uvicorn


# ============================================
# CONFIGURATION - Single Responsibility
# ============================================
@dataclass
class Settings:
    """Configuration settings"""
    API_KEY: str = "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"
    MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"
    API_URL: str = "https://openrouter.ai/api/v1/chat/completions"
    
    SYSTEM_PROMPT: str = """
Role:
- You are a helpful financial assistant

Instructions:
- Provide accurate and concise financial advice
- Assist with budgeting, saving, and investment strategies
- If user asks some financial calculations, provide step-by-step explanations
- If user asks financial definitions, provide clear and simple explanations

Important:
- Don't answer questions outside of financial topics

Examples:
- User: How much should I save per month to build a $12,000 emergency fund in 12 months?
  Assistant: To save $12,000 in 12 months, divide 12,000 by 12 months: $12,000 ÷ 12 = $1,000 per month. You should save $1,000 each month.

- User: What is a 401(k)?
  Assistant: A 401(k) is a retirement savings plan offered by employers in the U.S. It lets you save and invest money for retirement, often with tax benefits and sometimes employer matching.

- User: What is day today?
  Assistant: I'm sorry, but I can only assist with financial topics. Please ask me a question related to finance.

- User: How can I create a monthly budget?
  Assistant: Start by listing all income and fixed expenses. Allocate a portion to savings, and then plan spending for variable expenses. Track each month and adjust as needed.
"""


# ============================================
# LOGGER - Singleton Pattern
# ============================================
class Logger:
    """Singleton logger instance"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        self.logger = logging.getLogger("FinancialAssistant")
        self.logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str):
        self.logger.error(message)


# ============================================
# STRATEGY PATTERN - Message Processing
# ============================================
class MessageStrategy(ABC):
    """Strategy pattern for message validation"""
    
    @abstractmethod
    def validate_message(self, message: str) -> bool:
        pass
    
    @abstractmethod
    def preprocess_message(self, message: str) -> str:
        pass


class FinancialMessageStrategy(MessageStrategy):
    """Concrete strategy for financial messages"""
    
    def validate_message(self, message: str) -> bool:
        """Validate message is not empty"""
        return message and message.strip()
    
    def preprocess_message(self, message: str) -> str:
        """Clean and preprocess message"""
        return message.strip()


# ============================================
# REPOSITORY PATTERN - Data Access Layer
# ============================================
class LLMRepository(ABC):
    """
    Repository Pattern - abstracts LLM API access
    SOLID: Open/Closed, Liskov Substitution
    """
    
    @abstractmethod
    def get_completion(self, message: str, history: List[Dict[str, str]]) -> str:
        pass


class OpenRouterLLMRepository(LLMRepository):
    """Concrete implementation for OpenRouter API"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = Logger()
    
    def get_completion(self, message: str, history: List[Dict[str, str]]) -> str:
        """Get completion from OpenRouter API"""
        
        messages = history + [{"role": "user", "content": message}]
        
        payload = {
            "model": self.settings.MODEL,
            "messages": messages
        }
        
        headers = {
            "Authorization": f"Bearer {self.settings.API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Financial Assistant"
        }
        
        try:
            self.logger.info(f"Sending request to LLM API")
            response = requests.post(
                self.settings.API_URL, 
                json=payload, 
                headers=headers,
                timeout=30
            )
            
            data = response.json()
            
            if "error" in data:
                self.logger.error(f"API Error: {data['error']}")
                raise Exception(f"API Error: {data['error']}")
            
            if "choices" not in data:
                self.logger.error("Unexpected API response format")
                raise Exception("Unexpected API response format")
            
            bot_response = data["choices"][0]["message"]["content"]
            self.logger.info("Successfully received response from LLM")
            return bot_response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error: {str(e)}")
            raise Exception(f"Network error: {str(e)}")
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON response from API")
            raise Exception("Invalid JSON response from API")


# ============================================
# FACTORY PATTERN - Object Creation
# ============================================
class LLMFactory:
    """Factory pattern for creating LLM repositories"""
    
    @staticmethod
    def create_llm(settings: Settings) -> LLMRepository:
        """Factory method to create LLM repository"""
        # Can easily extend to support other LLM providers
        # e.g., OpenAI, Anthropic, etc.
        return OpenRouterLLMRepository(settings)


# ============================================
# SERVICE LAYER - Business Logic
# ============================================
class ChatbotService:
    """
    Service Layer - Orchestrates business logic
    SOLID: Single Responsibility, Dependency Inversion
    Design Pattern: Strategy, Dependency Injection
    """
    
    def __init__(self, settings: Settings):
        # Dependency Injection
        self.settings = settings
        self.llm_repository: LLMRepository = LLMFactory.create_llm(settings)
        self.message_strategy: MessageStrategy = FinancialMessageStrategy()
        self.logger = Logger()
    
    def process_message(self, message: str, history: List[Dict[str, str]]) -> str:
        """Process user message and return bot response"""
        
        # Strategy Pattern: validate and preprocess message
        if not self.message_strategy.validate_message(message):
            return "Please provide a valid message."
        
        preprocessed_message = self.message_strategy.preprocess_message(message)
        
        # Build conversation history
        formatted_history = self._build_history(history)
        
        # Repository Pattern: get response from LLM
        self.logger.info(f"Processing message: {preprocessed_message[:50]}...")
        response = self.llm_repository.get_completion(preprocessed_message, formatted_history)
        
        return response
    
    def _build_history(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Build conversation history with system prompt"""
        return [
            {"role": "system", "content": self.settings.SYSTEM_PROMPT}
        ] + history


# ============================================
# API MODELS - Data Transfer Objects
# ============================================
class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    history: List[Dict[str, str]]


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str
    error: str = None


# ============================================
# FASTAPI APPLICATION
# ============================================
app = FastAPI(
    title="Financial Assistant API",
    description="AI-powered financial chatbot with OOP and SOLID principles",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency Injection - Initialize services
settings = Settings()
chatbot_service = ChatbotService(settings)
logger = Logger()


# ============================================
# API ENDPOINTS
# ============================================
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint
    Processes user messages and returns AI responses
    """
    try:
        logger.info(f"Received chat request")
        response = chatbot_service.process_message(
            request.message, 
            request.history
        )
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return ChatResponse(response="", error=str(e))


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Financial Assistant API",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Financial Assistant API",
        "docs": "/docs",
        "health": "/health"
    }


# ============================================
# MAIN - Application Entry Point
# ============================================
if __name__ == "__main__":
    logger.info("Starting Financial Assistant API...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )


"""
============================================
DESIGN PATTERNS IMPLEMENTED:
============================================

1. SINGLETON PATTERN
   - Logger class ensures single instance

2. STRATEGY PATTERN
   - MessageStrategy for flexible message processing
   - Easy to add new validation strategies

3. FACTORY PATTERN
   - LLMFactory creates appropriate LLM repositories
   - Easy to add new LLM providers

4. REPOSITORY PATTERN
   - LLMRepository abstracts data access
   - Separates business logic from data access

5. DEPENDENCY INJECTION
   - Services receive dependencies via constructor
   - Promotes loose coupling

============================================
SOLID PRINCIPLES:
============================================

1. SINGLE RESPONSIBILITY
   - Settings: Configuration only
   - ChatbotService: Business logic
   - LLMRepository: API communication
   - Logger: Logging only

2. OPEN/CLOSED
   - Open for extension (new LLM providers)
   - Closed for modification (existing code)

3. LISKOV SUBSTITUTION
   - Any LLMRepository implementation works
   - Can swap OpenRouter with OpenAI, etc.

4. INTERFACE SEGREGATION
   - Small, focused interfaces (ABC classes)
   - No client forced to depend on unused methods

5. DEPENDENCY INVERSION
   - High-level modules depend on abstractions
   - Not on concrete implementations

============================================
INSTALLATION & USAGE:
============================================

1. Install dependencies:
   pip install fastapi uvicorn pydantic requests

2. Run the server:
   python backend.py

3. API will be available at:
   - http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

4. Connect from React frontend at:
   http://localhost:8000/api/chat
"""