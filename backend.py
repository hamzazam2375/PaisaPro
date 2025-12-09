from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import requests
import yfinance as yf
import xml.etree.ElementTree as ET
from transformers import pipeline
import re
import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
import logging
import uvicorn
import time
from urllib.parse import quote_plus

# Selenium / scraping imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class HeadlineDetail(BaseModel):
    headline: str
    sentiment: str
    score: float
    source: str
    date: str
    original_sentiment: Optional[str] = None


class SentimentSummary(BaseModel):
    positive: int
    negative: int
    neutral: int
    total: int
    avg_confidence: float


class SentimentAnalysisResponse(BaseModel):
    overall: str
    score: float
    details: List[HeadlineDetail]
    summary: SentimentSummary
    company_name: str
    analysis_date: str


class ProductOut(BaseModel):
    name: str
    price_pkr: float
    price_usd: float
    url: str
    source: str


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    history: List[Dict[str, str]]


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str
    error: str = None


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class NewsArticle:
    """Represents a news article"""
    title: str
    source: str
    date: Optional[str] = None


@dataclass
class AnalyzerConfig:
    """Configuration for sentiment analyzer"""
    api_key: str = "b18d6a7fa41a409eb23a5ec4b657864d"
    max_headlines: int = 10
    request_timeout: int = 10
    days_back: int = 7
    model_name: str = "yiyanghkust/finbert-tone"


@dataclass
class ScraperConfig:
    """Configuration for scrapers"""
    exchange_rate: float = 280.0
    headless: bool = True
    timeout: int = 30
    max_results: int = 20
    scroll_count: int = 3
    scroll_delay: int = 2
    max_workers: int = 3
    sort_by_price: bool = True


# ============================================================================
# INTERFACES
# ============================================================================

class INewsSource(ABC):
    """Interface for news sources"""
    
    @abstractmethod
    def fetch_news(self, company_name: str, max_results: int) -> List[NewsArticle]:
        """Fetch news from the source"""
        pass


class IHeadlineFilter(ABC):
    """Interface for headline filtering"""
    
    @abstractmethod
    def is_relevant(self, headline: str, company_name: str) -> bool:
        """Check if headline is relevant to company"""
        pass


class ISentimentAnalyzer(ABC):
    """Interface for sentiment analysis"""
    
    @abstractmethod
    def analyze(self, headlines: List[str]) -> List[Dict[str, Any]]:
        """Analyze sentiment of headlines"""
        pass


class IReportGenerator(ABC):
    """Interface for report generation"""
    
    @abstractmethod
    def generate(self, analysis_result: Dict[str, Any]) -> bytes:
        """Generate report from analysis results"""
        pass


class IProductScraper(ABC):
    """Interface for product scrapers"""
    
    @abstractmethod
    def scrape(self, query: str, sort_by_price: bool = True) -> List[Dict[str, Any]]:
        """Scrape products for a given query"""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of the scraping source"""
        pass


class IOutputHandler(ABC):
    """Interface for output handling"""
    @abstractmethod
    def write(self, message: str):
        pass


class ISortingStrategy(ABC):
    """Interface for sorting strategies"""
    @abstractmethod
    def sort(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass


class MessageStrategy(ABC):
    """Strategy pattern for message validation"""
    
    @abstractmethod
    def validate_message(self, message: str) -> bool:
        pass
    
    @abstractmethod
    def preprocess_message(self, message: str) -> str:
        pass


class LLMRepository(ABC):
    """
    Repository Pattern - abstracts LLM API access
    SOLID: Open/Closed, Liskov Substitution
    """
    
    @abstractmethod
    def get_completion(self, message: str, history: List[Dict[str, str]]) -> str:
        pass


# ============================================================================
# CONCRETE IMPLEMENTATIONS - NEWS SOURCES
# ============================================================================

class GoogleNewsRSSSource(INewsSource):
    """Fetches news from Google News RSS"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
    
    def fetch_news(self, company_name: str, max_results: int) -> List[NewsArticle]:
        query = company_name.replace(' ', '+')
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")
            
            articles = []
            for item in items[:max_results]:
                title_elem = item.find("title")
                pub_date_elem = item.find("pubDate")
                if title_elem is not None and title_elem.text:
                    articles.append(NewsArticle(
                        title=title_elem.text,
                        source='Google News',
                        date=pub_date_elem.text if pub_date_elem is not None else None
                    ))
            return articles
        except Exception as e:
            print(f"Google News RSS error: {e}")
            return []


class YahooFinanceSource(INewsSource):
    """Fetches news from Yahoo Finance"""
    
    def fetch_news(self, company_name: str, max_results: int) -> List[NewsArticle]:
        try:
            ticker = yf.Ticker(company_name)
            news = ticker.news
            if news:
                return [NewsArticle(
                    title=n.get("title", ""),
                    source='Yahoo Finance',
                    date=datetime.fromtimestamp(n.get('providerPublishTime', 0)).isoformat() 
                         if n.get('providerPublishTime') else None
                ) for n in news[:max_results] if n.get("title")]
        except Exception as e:
            print(f"Yahoo Finance error: {e}")
        return []


class NewsAPISource(INewsSource):
    """Fetches news from NewsAPI"""
    
    def __init__(self, api_key: str, timeout: int = 10, days_back: int = 7):
        self.api_key = api_key
        self.timeout = timeout
        self.days_back = days_back
        self.session = requests.Session()
    
    def fetch_news(self, company_name: str, max_results: int) -> List[NewsArticle]:
        try:
            from_date = (datetime.now() - timedelta(days=self.days_back)).strftime('%Y-%m-%d')
            url = f"https://newsapi.org/v2/everything?q={company_name}&from={from_date}&sortBy=publishedAt&language=en&apiKey={self.api_key}"
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                articles = resp.json().get("articles", [])
                return [NewsArticle(
                    title=a["title"],
                    source='NewsAPI',
                    date=a.get('publishedAt')
                ) for a in articles[:max_results] if "title" in a]
        except Exception as e:
            print(f"NewsAPI error: {e}")
        return []


# ============================================================================
# HEADLINE FILTERING
# ============================================================================

class RelevanceHeadlineFilter(IHeadlineFilter):
    """Filters headlines for relevance using pattern matching"""
    
    def is_relevant(self, headline: str, company_name: str) -> bool:
        headline_lower = headline.lower()
        company_lower = company_name.lower()
        
        # Filter spam
        spam_indicators = ['click here', 'subscribe', 'watch now', 'sign up', 'ad:', 'sponsored']
        if any(spam in headline_lower for spam in spam_indicators):
            return False
        
        # Special handling for numeric company names
        if company_lower == "3m":
            company_patterns = [
                r'\b3m\s+company\b', r'\b3m\s+co\b', r'\b3m\'s\b', r'\b3m:\b',
                r'\(mmm\)', r'\(nyse:mmm\)', r'^3m\s+', r'\s+3m\s+',
            ]
            exclude_patterns = [
                r'£3m\b', r'\$3m\b', r'€3m\b',
                r'\b3m\s+(members|people|users|teslas|homes|dollars|pounds)',
                r'nearly\s+3m', r'over\s+3m', r'about\s+3m',
            ]
            
            if any(re.search(pattern, headline_lower) for pattern in exclude_patterns):
                return False
            if not any(re.search(pattern, headline_lower) for pattern in company_patterns):
                return False
        else:
            words = company_lower.split()
            exact_pattern = r'\b' + re.escape(company_lower) + r'\b'
            if re.search(exact_pattern, headline_lower):
                return True
            
            if len(words) == 1:
                if not re.search(r'\b' + re.escape(company_lower) + r'\b', headline_lower):
                    return False
            else:
                if not all(re.search(r'\b' + re.escape(word) + r'\b', headline_lower) for word in words):
                    return False
        
        return True


class DuplicateHeadlineFilter:
    """Removes duplicate headlines"""
    
    @staticmethod
    def deduplicate(headlines: List[str]) -> List[str]:
        seen = set()
        unique = []
        
        for headline in headlines:
            normalized = re.sub(r'[^\w\s]', '', headline.lower())
            if normalized not in seen:
                seen.add(normalized)
                unique.append(headline)
        
        return unique


# ============================================================================
# SENTIMENT ANALYSIS
# ============================================================================

class FinBERTSentimentAnalyzer(ISentimentAnalyzer):
    """Sentiment analyzer using FinBERT"""
    
    def __init__(self, model_name: str = "yiyanghkust/finbert-tone"):
        self.pipeline = pipeline(
            "sentiment-analysis",
            model=model_name,
            tokenizer=model_name
        )
    
    def analyze(self, headlines: List[str]) -> List[Dict[str, Any]]:
        if not headlines:
            return []
        return self.pipeline(headlines)


class KeywordSentimentAdjuster:
    """Adjusts sentiment based on keywords (Strategy Pattern)"""
    
    STRONG_NEGATIVE = [
        'lawsuit', 'sued', 'litigation', 'controversy', 'scandal', 'fraud',
        'investigation', 'accused', 'allegations', 'trouble', 'crisis', 'collapse',
        'bankruptcy', 'layoffs', 'fired', 'resign', 'quit', 'failure', 'loses',
        'plunge', 'crash', 'slump', 'warning', 'concern', 'worried', 'threat'
    ]
    
    MODERATE_NEGATIVE = [
        'challenge', 'risk', 'uncertain', 'decline', 'drop', 'fall',
        'miss', 'disappoints', 'cuts', 'reduces', 'pressure'
    ]
    
    STRONG_POSITIVE = [
        'surge', 'soar', 'rally', 'record', 'breakthrough', 'success',
        'beat expectations', 'exceeds', 'outperforms', 'milestone', 'innovation',
        'revolutionary', 'wins', 'triumph', 'boom', 'hits', 'achievement'
    ]
    
    MODERATE_POSITIVE = [
        'growth', 'gains', 'rises', 'increases', 'improves', 'expansion',
        'deal', 'partnership', 'agreement', 'launches'
    ]
    
    @classmethod
    def adjust(cls, headline: str, sentiment: str, score: float) -> tuple[str, float]:
        headline_lower = headline.lower()
        
        strong_neg = sum(1 for word in cls.STRONG_NEGATIVE if word in headline_lower)
        moderate_neg = sum(1 for word in cls.MODERATE_NEGATIVE if word in headline_lower)
        strong_pos = sum(1 for word in cls.STRONG_POSITIVE if word in headline_lower)
        moderate_pos = sum(1 for word in cls.MODERATE_POSITIVE if word in headline_lower)
        
        if sentiment == "neutral":
            if strong_neg >= 1:
                return "negative", max(0.75, score)
            elif moderate_neg >= 2:
                return "negative", 0.70
            elif strong_pos >= 1:
                return "positive", max(0.75, score)
            elif moderate_pos >= 2:
                return "positive", 0.70
        elif sentiment == "negative" and (strong_neg >= 1 or moderate_neg >= 1):
            return "negative", min(1.0, score + 0.1)
        elif sentiment == "positive" and (strong_pos >= 1 or moderate_pos >= 1):
            return "positive", min(1.0, score + 0.1)
        
        return sentiment, score


class WeightedSentimentCalculator:
    """Calculates weighted sentiment scores"""
    
    @staticmethod
    def calculate(sentiments: List[Dict[str, Any]]) -> tuple[float, str]:
        if not sentiments:
            return 0, "Neutral"
        
        weighted_sum = sum(
            s["score"] * (1 if s["sentiment"] == "positive" else -1 if s["sentiment"] == "negative" else 0)
            for s in sentiments
        )
        
        total_confidence = sum(s["score"] for s in sentiments)
        avg_score = weighted_sum / total_confidence if total_confidence > 0 else 0
        
        if avg_score > 0.3:
            overall = "Strongly Positive"
        elif avg_score > 0.1:
            overall = "Positive"
        elif avg_score > -0.1:
            overall = "Neutral"
        elif avg_score > -0.3:
            overall = "Negative"
        else:
            overall = "Strongly Negative"
        
        return avg_score, overall


# ============================================================================
# NEWS AGGREGATOR (Facade Pattern)
# ============================================================================

class NewsAggregator:
    """Aggregates news from multiple sources"""
    
    TICKER_MAP = {
        '3m': 'MMM', 'apple': 'AAPL', 'microsoft': 'MSFT',
        'google': 'GOOGL', 'amazon': 'AMZN', 'tesla': 'TSLA',
    }
    
    def __init__(self, sources: List[INewsSource], relevance_filter: IHeadlineFilter):
        self.sources = sources
        self.relevance_filter = relevance_filter
    
    def fetch_all(self, company_name: str, max_headlines: int) -> List[NewsArticle]:
        search_query = self.TICKER_MAP.get(company_name.lower(), company_name)
        
        all_articles = []
        for source in self.sources:
            articles = source.fetch_news(search_query, max_headlines)
            all_articles.extend(articles)
        
        # Filter for relevance
        relevant = [
            article for article in all_articles
            if self.relevance_filter.is_relevant(article.title, company_name)
        ]
        
        # Deduplicate
        unique_titles = DuplicateHeadlineFilter.deduplicate([a.title for a in relevant])
        
        unique_articles = []
        for title in unique_titles:
            for article in relevant:
                if article.title == title:
                    unique_articles.append(article)
                    break
        
        return unique_articles[:max_headlines]


# ============================================================================
# REPORT GENERATION
# ============================================================================

class PDFReportGenerator(IReportGenerator):
    """Generates PDF reports using ReportLab"""
    
    def generate(self, analysis_result: Dict[str, Any]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#9333ea'),
            spaceAfter=30,
        )
        elements.append(Paragraph(f"Sentiment Analysis Report", title_style))
        elements.append(Paragraph(f"Company: {analysis_result['company_name']}", styles['Heading2']))
        elements.append(Paragraph(f"Date: {analysis_result['analysis_date']}", styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Overall Sentiment
        overall_text = f"<b>Overall Sentiment:</b> {analysis_result['overall']} (Score: {analysis_result['score']})"
        elements.append(Paragraph(overall_text, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary Table
        summary = analysis_result['summary']
        summary_data = [
            ['Metric', 'Value'],
            ['Positive', str(summary['positive'])],
            ['Negative', str(summary['negative'])],
            ['Neutral', str(summary['neutral'])],
            ['Total', str(summary['total'])],
            ['Avg Confidence', f"{summary['avg_confidence']:.3f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9333ea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Headlines
        elements.append(Paragraph("<b>Detailed Analysis:</b>", styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        for i, detail in enumerate(analysis_result['details'], 1):
            emoji = "📈" if detail['sentiment'] == "positive" else "📉" if detail['sentiment'] == "negative" else "➡️"
            headline_text = f"{i}. {emoji} <b>[{detail['sentiment'].upper()}]</b> Confidence: {detail['score']:.2f}"
            elements.append(Paragraph(headline_text, styles['Normal']))
            elements.append(Paragraph(f"   {detail['headline']}", styles['Normal']))
            elements.append(Paragraph(f"   <i>Source: {detail['source']} | Date: {detail['date']}</i>", styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


# ============================================================================
# MAIN SERVICE (Facade Pattern)
# ============================================================================

class CompanySentimentService:
    """Main service for sentiment analysis"""
    
    def __init__(self, config: AnalyzerConfig):
        self.config = config
        
        # Initialize components
        google_source = GoogleNewsRSSSource(timeout=config.request_timeout)
        yahoo_source = YahooFinanceSource()
        newsapi_source = NewsAPISource(config.api_key, config.request_timeout, config.days_back)
        
        self.news_aggregator = NewsAggregator(
            sources=[google_source, yahoo_source, newsapi_source],
            relevance_filter=RelevanceHeadlineFilter()
        )
        
        self.sentiment_analyzer = FinBERTSentimentAnalyzer(config.model_name)
        self.report_generator = PDFReportGenerator()
    
    def analyze(self, company_name: str, max_headlines: int = None) -> Dict[str, Any]:
        max_headlines = max_headlines or self.config.max_headlines
        
        # Fetch news
        articles = self.news_aggregator.fetch_all(company_name, max_headlines)
        
        if not articles:
            return {
                'overall': "No recent news found",
                'score': 0,
                'details': [],
                'summary': {
                    'positive': 0, 'negative': 0, 'neutral': 0,
                    'total': 0, 'avg_confidence': 0
                },
                'company_name': company_name,
                'analysis_date': datetime.now().isoformat()
            }
        
        # Analyze sentiment
        titles = [a.title for a in articles]
        results = self.sentiment_analyzer.analyze(titles)
        
        sentiments = []
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for article, result in zip(articles, results):
            original_sentiment = result["label"].lower()
            original_score = result["score"]
            
            adjusted_sentiment, adjusted_score = KeywordSentimentAdjuster.adjust(
                article.title, original_sentiment, original_score
            )
            
            sentiments.append({
                "headline": article.title,
                "sentiment": adjusted_sentiment,
                "score": adjusted_score,
                "source": article.source,
                "date": article.date or 'Unknown',
                "original_sentiment": original_sentiment if adjusted_sentiment != original_sentiment else None
            })
            
            sentiment_counts[adjusted_sentiment] += 1
        
        # Calculate overall
        avg_score, overall = WeightedSentimentCalculator.calculate(sentiments)
        sentiments.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'overall': overall,
            'score': round(avg_score, 3),
            'details': sentiments,
            'summary': {
                'positive': sentiment_counts['positive'],
                'negative': sentiment_counts['negative'],
                'neutral': sentiment_counts['neutral'],
                'total': len(sentiments),
                'avg_confidence': round(sum(s['score'] for s in sentiments) / len(sentiments), 3)
            },
            'company_name': company_name,
            'analysis_date': datetime.now().isoformat()
        }
    
    def generate_report(self, analysis_result: Dict[str, Any]) -> bytes:
        return self.report_generator.generate(analysis_result)


# ============================================================================
# UTILITY SERVICES FOR PRICE COMPARISON
# ============================================================================

class CurrencyConverter:
    """Handles currency conversion operations"""
    
    def __init__(self, exchange_rate: float = 280.0):
        self._exchange_rate = exchange_rate
    
    def pkr_to_usd(self, pkr: float) -> float:
        """Convert PKR to USD"""
        return round(pkr / self._exchange_rate, 2)
    
    @property
    def exchange_rate(self) -> float:
        return self._exchange_rate


class PriceExtractor:
    """Extracts price from text using various patterns"""
    
    PRICE_PATTERNS = [
        r"Rs\.?\s*([\d,]+)",
        r"PKR\.?\s*([\d,]+)",
        r"₨\.?\s*([\d,]+)",
        r"\b([\d,]+)\s*Rs",
        r"\b([\d,]+)\s*PKR"
    ]
    
    @staticmethod
    def extract(text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not text:
            return None
        
        for pattern in PriceExtractor.PRICE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(",", ""))
                except (ValueError, AttributeError):
                    continue
        return None


class WebDriverFactory:
    """Factory for creating WebDriver instances"""
    
    @staticmethod
    def create_driver(headless: bool = True) -> webdriver.Chrome:
        """Create a configured Chrome WebDriver"""
        options = Options()
        
        if headless:
            options.add_argument("--headless=new")
        
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        return webdriver.Chrome(options=options)


class ConsoleOutputHandler(IOutputHandler):
    """Console output handler"""
    def write(self, message: str):
        print(message)


# ============================================================================
# SORTING STRATEGIES
# ============================================================================

class PriceSortAscending(ISortingStrategy):
    """Sort products by price in ascending order"""
    def sort(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(products, key=lambda p: p['price_pkr'])


class NoSorting(ISortingStrategy):
    """No sorting - return products as-is"""
    def sort(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return products


# ============================================================================
# BASE SCRAPER (Template Method Pattern)
# ============================================================================

class BaseProductScraper(IProductScraper):
    """Base scraper implementing common workflow"""
    
    def __init__(self, config: ScraperConfig, output: IOutputHandler):
        self.config = config
        self.output = output
        self.currency_converter = CurrencyConverter(config.exchange_rate)
        self.price_extractor = PriceExtractor()
        self._driver: Optional[webdriver.Chrome] = None
    
    def scrape(self, query: str, sort_by_price: bool = True) -> List[Dict[str, Any]]:
        """Template method defining the scraping workflow"""
        try:
            self._initialize_driver()
            self._navigate_to_search(query)
            self._wait_for_page_load()
            self._scroll_page()
            raw_data = self._extract_products()
            products = self._parse_products(raw_data)
            return self._sort_products(products, sort_by_price)
        except Exception as e:
            self.output.write(f"Error in {self.get_source_name()}: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            self._cleanup()
    
    # Template methods to be implemented by subclasses
    @abstractmethod
    def _navigate_to_search(self, query: str):
        """Navigate to search page"""
        pass
    
    @abstractmethod
    def _extract_products(self) -> List[Any]:
        """Extract raw product data"""
        pass
    
    @abstractmethod
    def _parse_products(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        """Parse raw data into Product objects"""
        pass
    
    # Common implementations
    def _initialize_driver(self):
        """Initialize WebDriver"""
        self._driver = WebDriverFactory.create_driver(self.config.headless)
    
    def _wait_for_page_load(self):
        """Wait for initial page load"""
        time.sleep(5)
    
    def _scroll_page(self):
        """Scroll page to load lazy content"""
        for _ in range(self.config.scroll_count):
            if self._driver:
                self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(self.config.scroll_delay)
    
    def _sort_products(self, products: List[Dict[str, Any]], sort_by_price: bool = True) -> List[Dict[str, Any]]:
        """Sort products by price (optional)"""
        if sort_by_price:
            return sorted(products, key=lambda p: p['price_pkr'])
        return products
    
    def _cleanup(self):
        """Clean up resources"""
        if self._driver:
            try:
                self._driver.quit()
            except:
                pass


# ============================================================================
# CONCRETE SCRAPERS
# ============================================================================

class AlfatahScraper(BaseProductScraper):
    """Scraper for Alfatah.pk"""
    
    def get_source_name(self) -> str:
        return "Alfatah"
    
    def _navigate_to_search(self, query: str):
        encoded_query = quote_plus(query)
        url = f"https://alfatah.pk/search?q={encoded_query}"
        if self._driver:
            self._driver.get(url)
    
    def _extract_products(self) -> List[Any]:
        if not self._driver:
            return []
        
        soup = BeautifulSoup(self._driver.page_source, "html.parser")
        
        container_patterns = [
            "div.card-wrapper",
            "div.product-item",
            "article.card",
            "li.grid__item",
            "div.product-card",
        ]
        
        containers = []
        for pattern in container_patterns:
            containers = soup.select(pattern)
            if containers:
                self.output.write(f"   📦 Using selector: {pattern} ({len(containers)} found)")
                break
        
        return containers[:self.config.max_results]
    
    def _parse_products(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        products = []
        
        for container in raw_data:
            title = self._extract_title(container)
            if not title:
                continue
            
            link = self._extract_link(container)
            price_pkr = self._extract_price(container)
            if not price_pkr:
                continue
            
            price_usd = self.currency_converter.pkr_to_usd(price_pkr)
            
            products.append({
                "name": title,
                "price_pkr": float(price_pkr),
                "price_usd": price_usd,
                "url": link or "N/A",
                "source": self.get_source_name()
            })
        
        return products
    
    def _extract_title(self, container) -> Optional[str]:
        selectors = [
            "a.product-title-ellipsis",
            "h3 a",
            "div.card__heading a",
            ".card__content a"
        ]
        
        for selector in selectors:
            elem = container.select_one(selector)
            if elem and elem.text.strip():
                return elem.text.strip()
        return None
    
    def _extract_link(self, container) -> Optional[str]:
        link_elem = container.select_one("a[href*='/products/']")
        if link_elem and link_elem.get('href'):
            href = link_elem['href']
            return href if href.startswith('http') else f"https://alfatah.pk{href}"
        return None
    
    def _extract_price(self, container) -> Optional[float]:
        price_elements = container.select("span, div, p")
        for elem in price_elements:
            elem_class = ' '.join(elem.get('class', []))
            if 'price' in elem_class.lower():
                price = self.price_extractor.extract(elem.text)
                if price:
                    return price
        
        all_text = container.get_text()
        return self.price_extractor.extract(all_text)


class DarazScraper(BaseProductScraper):
    """Scraper for Daraz.pk"""
    
    def get_source_name(self) -> str:
        return "Daraz"
    
    def _navigate_to_search(self, query: str):
        url = f"https://www.daraz.pk/catalog/?q={query}"
        if self._driver:
            self._driver.get(url)
    
    def _extract_products(self) -> List[Any]:
        if not self._driver:
            return []
        
        soup = BeautifulSoup(self._driver.page_source, "lxml")
        
        items = soup.select(".Ms6aG")
        if not items:
            items = soup.select("[data-qa-locator='product-item']")
        if not items:
            items = soup.select(".gridItem")
        
        return items[:self.config.max_results]
    
    def _parse_products(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        products = []
        
        for item in raw_data:
            title_tag = item.select_one(".RfADt a")
            if not title_tag:
                title_tag = item.select_one("a[title]")
            
            price_tag = item.select_one(".ooOxS")
            if not price_tag:
                price_tag = item.select_one(".price")
            
            if not (title_tag and price_tag):
                continue
            
            title = title_tag.text.strip()
            href = title_tag.get("href")
            link = "https:" + href if href and href.startswith("//") else (href or "N/A")
            
            price_pkr = self.price_extractor.extract(price_tag.text)
            if not price_pkr:
                continue
            
            price_usd = self.currency_converter.pkr_to_usd(price_pkr)
            
            products.append({
                "name": title,
                "price_pkr": float(price_pkr),
                "price_usd": price_usd,
                "url": link,
                "source": self.get_source_name()
            })
        
        return products


class ImtiazScraper(BaseProductScraper):
    """Scraper for Imtiaz.pk"""
    
    def __init__(self, config: ScraperConfig, output: IOutputHandler, city: str = "Askari 1"):
        super().__init__(config, output)
        self.city = city
    
    def get_source_name(self) -> str:
        return "Imtiaz"
    
    def _initialize_driver(self):
        super()._initialize_driver()
        self.output.write(f"   🌐 Loading Imtiaz website...")
        if self._driver:
            self._driver.get("https://shop.imtiaz.com.pk/")
            time.sleep(5)
            self._handle_location_modal()
    
    def _handle_location_modal(self):
        if not self._driver:
            return
        
        wait = WebDriverWait(self._driver, 30)
        
        try:
            time.sleep(3)
            self.output.write(f"   🔄 Handling location modal...")
            
            # Click EXPRESS
            express_selectors = [
                "//button[text()='EXPRESS']",
                "//button[contains(text(), 'EXPRESS')]",
            ]
            
            for selector in express_selectors:
                try:
                    express_btn = self._driver.find_element(By.XPATH, selector)
                    self._driver.execute_script("arguments[0].click();", express_btn)
                    self.output.write(f"   ✅ EXPRESS clicked")
                    time.sleep(3)
                    break
                except:
                    continue
            
            # Enter area
            try:
                inputs = self._driver.find_elements(By.XPATH, "//input[@type='text']")
                for inp in inputs:
                    if not inp.is_displayed():
                        continue
                    
                    value = inp.get_attribute('value') or ''
                    if value.lower() in ['karachi', 'lahore', 'islamabad']:
                        continue
                    
                    inp.clear()
                    time.sleep(0.5)
                    inp.send_keys(self.city)
                    time.sleep(2)
                    inp.send_keys(Keys.ARROW_DOWN)
                    time.sleep(1)
                    inp.send_keys(Keys.ENTER)
                    self.output.write(f"   ✅ Area entered and selected")
                    time.sleep(2)
                    break
            except Exception as e:
                self.output.write(f"   ⚠️ Area entry: {str(e)[:100]}")
            
            # Click Select button
            select_selectors = [
                "//button[text()='Select']",
                "//button[contains(text(), 'Select')]",
            ]
            
            for selector in select_selectors:
                try:
                    select_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    self._driver.execute_script("arguments[0].click();", select_btn)
                    self.output.write(f"   ✅ Select button clicked")
                    time.sleep(5)
                    break
                except:
                    continue
                
        except Exception as e:
            self.output.write(f"   ❌ Error in location modal: {e}")
    
    def _navigate_to_search(self, query: str):
        if not self._driver:
            return
        
        self.output.write(f"   🔍 Searching for '{query}'...")
        try:
            search_input = WebDriverWait(self._driver, 30).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'input[placeholder*="search" i], input[type="search"]')
                )
            )
            search_input.clear()
            search_input.send_keys(query)
            search_input.send_keys(Keys.ENTER)
            self.output.write(f"   ✅ Search executed")
            time.sleep(8)
        except:
            self._driver.get(f"https://shop.imtiaz.com.pk/search?q={query}")
            time.sleep(8)
    
    def _scroll_page(self):
        if not self._driver:
            return
        
        for i in range(5):
            self._driver.execute_script(f"window.scrollTo(0, {i * 400});")
            time.sleep(1)
    
    def _extract_products(self) -> List[Any]:
        if not self._driver:
            return []
        
        selectors = [
            ('div[class*="ProductCard"]', 'ProductCard'),
            ('div[class*="product"]', 'product class'),
            ('article', 'article'),
        ]
        
        elements = []
        for selector, name in selectors:
            elements = self._driver.find_elements(By.CSS_SELECTOR, selector)
            if len(elements) > 5:
                self.output.write(f"   📦 Using selector: {name} ({len(elements)} found)")
                break
        
        return elements[:self.config.max_results]
    
    def _parse_products(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        products = []
        
        for element in raw_data:
            try:
                text = element.text.strip()
                if not text or len(text) < 15:
                    continue
                
                price_pkr = self.price_extractor.extract(text)
                if not price_pkr:
                    continue
                
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                name = None
                for line in lines:
                    if len(line) > 8 and 'Rs' not in line and 'PKR' not in line:
                        name = line
                        break
                
                if not name or any(p['name'] == name for p in products):
                    continue
                
                price_usd = self.currency_converter.pkr_to_usd(price_pkr)
                
                products.append({
                    "name": name,
                    "price_pkr": float(price_pkr),
                    "price_usd": price_usd,
                    "url": "N/A",
                    "source": self.get_source_name()
                })
                
            except:
                continue
        
        return products


# ============================================================================
# SCRAPER FACTORY
# ============================================================================

class ScraperFactory:
    """Factory for creating scraper instances"""
    
    _registry: Dict[str, type] = {}
    
    @classmethod
    def register(cls, key: str, scraper_cls):
        """Register a scraper class"""
        cls._registry[key.lower()] = scraper_cls
    
    @classmethod
    def create_scraper(cls, key: str, config: ScraperConfig, output: IOutputHandler, **kwargs) -> IProductScraper:
        """Create a scraper instance"""
        scraper_cls = cls._registry.get(key.lower())
        if not scraper_cls:
            raise ValueError(f"Unknown scraper: {key}")
        
        # Pass city parameter to Imtiaz scraper
        if key.lower() == 'imtiaz' and 'city' in kwargs:
            return scraper_cls(config, output, city=kwargs['city'])
        return scraper_cls(config, output)
    
    @classmethod
    def get_available_scrapers(cls) -> List[str]:
        """Get list of available scraper keys"""
        return list(cls._registry.keys())


# Register all scrapers
ScraperFactory.register('alfatah', AlfatahScraper)
ScraperFactory.register('daraz', DarazScraper)
ScraperFactory.register('imtiaz', ImtiazScraper)


# ============================================================================
# PRICE COMPARISON SERVICE
# ============================================================================

class PriceComparisonService:
    """High-level service for comparing prices"""
    
    def __init__(self, config: ScraperConfig, output: IOutputHandler):
        self.config = config
        self.output = output
        self._print_lock = Lock()
    
    def _thread_safe_print(self, message: str):
        with self._print_lock:
            self.output.write(message)
    
    def _scrape_single_source(self, source: str, query: str, sort_by_price: bool) -> List[Dict[str, Any]]:
        """Scrape a single source with optional sorting"""
        try:
            self._thread_safe_print(f"\n{'='*60}")
            self._thread_safe_print(f"📦 Scraping {source.upper()}")
            self._thread_safe_print(f"{'='*60}")
            
            kwargs = {}
            if source == 'imtiaz':
                kwargs['city'] = 'Askari 1'
            
            scraper = ScraperFactory.create_scraper(source, self.config, self.output, **kwargs)
            products = scraper.scrape(query, sort_by_price=sort_by_price)
            
            self._thread_safe_print(f"   ✅ Found {len(products)} products from {source}")
            return products
            
        except Exception as e:
            self._thread_safe_print(f"   ❌ Error scraping {source}: {e}")
            return []
    
    def find_products(
        self, 
        query: str, 
        sources: Optional[List[str]] = None,
        top_n: int = 10,
        sort_by_price: bool = True,
        equal_distribution: bool = False,
        parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find products across sources with optional price sorting
        
        Args:
            query: Product search query
            sources: List of source names
            top_n: Number of products to return
            sort_by_price: Sort results by price (default: True)
            equal_distribution: Get equal number of products from each source
            parallel: Execute scrapers in parallel
        """
        if sources is None:
            sources = ScraperFactory.get_available_scrapers()
        
        self.output.write(f"🔍 Searching for '{query}' across {len(sources)} sources...")
        self.output.write(f"📊 Sort by price: {'YES' if sort_by_price else 'NO'}")
        self.output.write(f"📊 Equal distribution: {'YES' if equal_distribution else 'NO'}")
        
        if parallel:
            self.output.write(f"⚡ Running {len(sources)} scrapers in PARALLEL\n")
        else:
            self.output.write(f"⏳ Running {len(sources)} scrapers SEQUENTIALLY\n")
        
        start_time = time.time()
        all_products = []
        products_by_source = {}
        
        if parallel:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_source = {
                    executor.submit(self._scrape_single_source, source, query, sort_by_price): source
                    for source in sources
                }
                
                for future in as_completed(future_to_source):
                    source = future_to_source[future]
                    try:
                        products = future.result()
                        products_by_source[source] = products
                        all_products.extend(products)
                    except Exception as e:
                        self._thread_safe_print(f"❌ Exception for {source}: {e}")
                        products_by_source[source] = []
        else:
            for source in sources:
                products = self._scrape_single_source(source, query, sort_by_price)
                products_by_source[source] = products
                all_products.extend(products)
        
        elapsed_time = time.time() - start_time
        
        # Handle equal distribution or regular sorting
        if equal_distribution and not sort_by_price:
            per_source = top_n // len(sources)
            remainder = top_n % len(sources)
            
            result = []
            for i, source in enumerate(sources):
                count = per_source + (1 if i < remainder else 0)
                result.extend(products_by_source.get(source, [])[:count])
            
            all_products = result
            
        elif sort_by_price:
            all_products.sort(key=lambda p: p['price_pkr'])
        
        self.output.write(f"\n{'='*80}")
        self.output.write(f"✅ Total products found: {len(all_products)}")
        self.output.write(f"⏱️  Total time: {elapsed_time:.2f} seconds")
        
        if equal_distribution and not sort_by_price:
            self.output.write(f"🏆 Returning {top_n} products (equal distribution from each source)")
        else:
            self.output.write(f"🏆 Returning top {top_n} {'cheapest ' if sort_by_price else ''}products")
        
        self.output.write(f"{'='*80}\n")
        
        return all_products[:top_n]


# ============================================================================
# FINANCIAL ASSISTANT SERVICES
# ============================================================================

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


class FinancialMessageStrategy(MessageStrategy):
    """Concrete strategy for financial messages"""
    
    def validate_message(self, message: str) -> bool:
        """Validate message is not empty"""
        return message and message.strip()
    
    def preprocess_message(self, message: str) -> str:
        """Clean and preprocess message"""
        return message.strip()


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


class LLMFactory:
    """Factory pattern for creating LLM repositories"""
    
    @staticmethod
    def create_llm(settings: Settings) -> LLMRepository:
        """Factory method to create LLM repository"""
        # Can easily extend to support other LLM providers
        # e.g., OpenAI, Anthropic, etc.
        return OpenRouterLLMRepository(settings)


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


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Multi-Service API",
    description="Combined API for Sentiment Analysis, Price Comparison, and Financial Assistant",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
sentiment_config = AnalyzerConfig()
sentiment_service = CompanySentimentService(sentiment_config)

scraper_config = ScraperConfig()
price_output = ConsoleOutputHandler()
price_service = PriceComparisonService(scraper_config, price_output)

financial_settings = Settings()
chatbot_service = ChatbotService(financial_settings)
logger = Logger()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Multi-Service API",
        "version": "3.0.0",
        "services": {
            "sentiment_analysis": "/api/analyze",
            "price_comparison": "/api/compare", 
            "financial_assistant": "/api/chat",
            "health": "/health"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Multi-Service API",
        "version": "3.0.0"
    }

# Sentiment Analysis Endpoints
@app.get("/api/analyze", response_model=SentimentAnalysisResponse)
def analyze_sentiment(
    company: str = Query(..., description="Company name to analyze"),
    max_headlines: int = Query(10, ge=5, le=50, description="Maximum headlines to analyze")
):
    """Analyze sentiment for a company"""
    if not company.strip():
        raise HTTPException(status_code=400, detail="Company name is required")
    
    try:
        result = sentiment_service.analyze(company, max_headlines)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/report")
def download_report(
    company: str = Query(..., description="Company name to analyze"),
    max_headlines: int = Query(10, ge=5, le=50, description="Maximum headlines to analyze")
):
    """Generate and download PDF report"""
    if not company.strip():
        raise HTTPException(status_code=400, detail="Company name is required")
    
    try:
        result = sentiment_service.analyze(company, max_headlines)
        pdf_bytes = sentiment_service.generate_report(result)
        
        filename = f"sentiment_report_{company.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

# Price Comparison Endpoints
@app.get("/api/compare", response_model=List[ProductOut])
def compare(
    query: str = Query(..., description="Product search query"),
    sources: Optional[str] = Query(None, description="Comma-separated source names (alfatah,daraz,imtiaz)"),
    top_n: int = Query(10, ge=1, le=100, description="Number of products to return"),
    sort: bool = Query(True, description="Sort by price"),
    equal_distribution: bool = Query(False, description="Get equal products from each source"),
    parallel: bool = Query(True, description="Run scrapers in parallel")
):
    """
    Compare product prices across multiple sources
    
    - **query**: Product to search for (required)
    - **sources**: Comma-separated list of sources (default: all)
    - **top_n**: Number of products to return (1-100)
    - **sort**: Sort by price ascending (default: true)
    - **equal_distribution**: Get equal number from each source (default: false)
    - **parallel**: Run scrapers in parallel (default: true)
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query parameter is required")
    
    # Parse sources
    source_list = None
    if sources:
        source_list = [s.strip() for s in sources.split(',') if s.strip()]
        available = ScraperFactory.get_available_scrapers()
        invalid = [s for s in source_list if s not in available]
        if invalid:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid sources: {', '.join(invalid)}. Available: {', '.join(available)}"
            )
    
    products = price_service.find_products(
        query=query,
        sources=source_list,
        top_n=top_n,
        sort_by_price=sort,
        equal_distribution=equal_distribution,
        parallel=parallel
    )
    
    return [ProductOut(**p) for p in products]

@app.get("/api/sources")
def get_sources():
    """Get available scraper sources"""
    return {
        "sources": ScraperFactory.get_available_scrapers()
    }

# Financial Assistant Endpoints
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


# ============================================================================
# MAIN - Application Entry Point
# ============================================================================
if __name__ == "__main__":
    logger.info("Starting Multi-Service API...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )