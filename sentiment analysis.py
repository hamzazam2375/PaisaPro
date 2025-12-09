import requests
import yfinance as yf
import xml.etree.ElementTree as ET
from transformers import pipeline
from datetime import datetime, timedelta
import re

class CompanySentimentAnalyzer:
    def __init__(self, api_key="b18d6a7fa41a409eb23a5ec4b657864d"):
        """Initialize FinBERT sentiment analyzer and News API key."""
        self.api_key = api_key
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="yiyanghkust/finbert-tone",
            tokenizer="yiyanghkust/finbert-tone"
        )
        self.session = requests.Session()

    # ========== News Filtering ==========
    def _is_relevant_headline(self, headline, company_name):
        """Filter out irrelevant headlines with context-aware matching."""
        headline_lower = headline.lower()
        company_lower = company_name.lower()
        
        # Filter out spam/promotional content first
        spam_indicators = ['click here', 'subscribe', 'watch now', 'sign up', 'ad:', 'sponsored']
        if any(spam in headline_lower for spam in spam_indicators):
            return False
        
        # Special handling for numeric company names like "3M"
        if company_lower == "3m":
            # Must be followed by specific company indicators, not money/quantity indicators
            company_patterns = [
                r'\b3m\s+company\b',
                r'\b3m\s+co\b',
                r'\b3m\'s\b',
                r'\b3m:\b',
                r'\(mmm\)',  # ticker symbol
                r'\(nyse:mmm\)',
                r'^3m\s+',  # Starting with 3M
                r'\s+3m\s+',  # 3M surrounded by spaces
            ]
            
            # Exclude monetary/quantity references
            exclude_patterns = [
                r'£3m\b',
                r'\$3m\b',
                r'€3m\b',
                r'\b3m\s+(members|people|users|teslas|homes|dollars|pounds)',
                r'nearly\s+3m',
                r'over\s+3m',
                r'about\s+3m',
            ]
            
            # Check exclusions first
            if any(re.search(pattern, headline_lower) for pattern in exclude_patterns):
                return False
            
            # Must match at least one company pattern
            if not any(re.search(pattern, headline_lower) for pattern in company_patterns):
                return False
        else:
            # For multi-word companies, check if ALL words appear (in any order)
            # Also try exact phrase match
            words = company_lower.split()
            
            # Try exact phrase first (with word boundaries)
            exact_pattern = r'\b' + re.escape(company_lower) + r'\b'
            if re.search(exact_pattern, headline_lower):
                return True
            
            # If exact phrase not found, check if all words are present
            # This handles cases like "Apple Inc" when searching "Apple"
            if len(words) == 1:
                # Single word - must match with word boundary
                if not re.search(r'\b' + re.escape(company_lower) + r'\b', headline_lower):
                    return False
            else:
                # Multiple words - all must be present
                if not all(re.search(r'\b' + re.escape(word) + r'\b', headline_lower) for word in words):
                    return False
        
        return True
    
    def _deduplicate_headlines(self, headlines):
        """Remove duplicate or very similar headlines."""
        seen = set()
        unique = []
        
        for headline in headlines:
            # Normalize: remove special chars, lowercase
            normalized = re.sub(r'[^\w\s]', '', headline.lower())
            # Check if substantially different
            if normalized not in seen:
                seen.add(normalized)
                unique.append(headline)
        
        return unique

    # ========== Fetching News ==========
    def _fetch_from_google_news_rss(self, company_name, max_results=10):
        query = company_name.replace(' ', '+')
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")
            headlines = []
            for item in items[:max_results]:
                title_elem = item.find("title")
                pub_date_elem = item.find("pubDate")
                if title_elem is not None and title_elem.text:
                    headlines.append({
                        'title': title_elem.text,
                        'source': 'Google News',
                        'date': pub_date_elem.text if pub_date_elem is not None else None
                    })
            return headlines
        except Exception as e:
            print(f"Google News RSS error: {e}")
            return []

    def _fetch_from_yahoo(self, company_name):
        try:
            ticker = yf.Ticker(company_name)
            news = ticker.news
            if news:
                return [{
                    'title': n.get("title", ""),
                    'source': 'Yahoo Finance',
                    'date': datetime.fromtimestamp(n.get('providerPublishTime', 0)).isoformat() if n.get('providerPublishTime') else None
                } for n in news if n.get("title")]
        except Exception as e:
            print(f"Yahoo Finance error: {e}")
        return []

    def _fetch_from_newsapi(self, company_name):
        try:
            # Get news from last 7 days for relevance
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            url = f"https://newsapi.org/v2/everything?q={company_name}&from={from_date}&sortBy=publishedAt&language=en&apiKey={self.api_key}"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                articles = resp.json().get("articles", [])
                return [{
                    'title': a["title"],
                    'source': 'NewsAPI',
                    'date': a.get('publishedAt')
                } for a in articles if "title" in a]
        except Exception as e:
            print(f"NewsAPI error: {e}")
        return []

    def fetch_company_news(self, company_name, max_headlines=10):
        """Aggregate news from multiple sources with filtering."""
        all_headlines = []
        
        # For known tickers, use ticker symbol for better results
        ticker_map = {
            '3m': 'MMM',
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'google': 'GOOGL',
            'amazon': 'AMZN',
            'tesla': 'TSLA',
        }
        
        search_query = ticker_map.get(company_name.lower(), company_name)
        
        # Collect from all sources
        sources = [
            self._fetch_from_google_news_rss(f"{search_query} stock" if search_query in ticker_map.values() else company_name),
            self._fetch_from_yahoo(search_query),
            self._fetch_from_newsapi(f'"{search_query}" stock OR "{company_name}"'),
        ]
        
        for source_headlines in sources:
            all_headlines.extend(source_headlines)
        
        # Filter for relevance
        relevant_headlines = [
            h for h in all_headlines 
            if self._is_relevant_headline(h['title'], company_name)
        ]
        
        # Deduplicate
        unique_titles = self._deduplicate_headlines([h['title'] for h in relevant_headlines])
        
        # Reconstruct with metadata
        unique_headlines = []
        for title in unique_titles:
            for h in relevant_headlines:
                if h['title'] == title:
                    unique_headlines.append(h)
                    break
        
        return unique_headlines[:max_headlines]

    # ========== Enhanced Sentiment Analysis ==========
    def _adjust_sentiment_with_keywords(self, headline, original_sentiment, original_score):
        """Adjust sentiment based on strong positive/negative keywords."""
        headline_lower = headline.lower()
        
        # Strong negative indicators
        strong_negative = [
            'lawsuit', 'sued', 'litigation', 'controversy', 'scandal', 'fraud',
            'investigation', 'accused', 'allegations', 'trouble', 'crisis', 'collapse',
            'bankruptcy', 'layoffs', 'fired', 'resign', 'quit', 'failure', 'loses',
            'plunge', 'crash', 'slump', 'warning', 'concern', 'worried', 'threat',
            'intimidation', 'cost it billions', 'complicate', 'questions over'
        ]
        
        # Moderate negative indicators
        moderate_negative = [
            'challenge', 'risk', 'uncertain', 'decline', 'drop', 'fall',
            'miss', 'disappoints', 'cuts', 'reduces', 'pressure'
        ]
        
        # Strong positive indicators
        strong_positive = [
            'surge', 'soar', 'rally', 'record', 'breakthrough', 'success',
            'beat expectations', 'exceeds', 'outperforms', 'milestone', 'innovation',
            'revolutionary', 'wins', 'triumph', 'boom', 'hits', 'achievement'
        ]
        
        # Moderate positive indicators
        moderate_positive = [
            'growth', 'gains', 'rises', 'increases', 'improves', 'expansion',
            'deal', 'partnership', 'agreement', 'launches'
        ]
        
        # Count matches
        strong_neg_count = sum(1 for word in strong_negative if word in headline_lower)
        moderate_neg_count = sum(1 for word in moderate_negative if word in headline_lower)
        strong_pos_count = sum(1 for word in strong_positive if word in headline_lower)
        moderate_pos_count = sum(1 for word in moderate_positive if word in headline_lower)
        
        # Override neutral classifications when strong indicators present
        if original_sentiment == "neutral":
            # Strong negative keywords override neutral
            if strong_neg_count >= 1:
                return "negative", max(0.75, original_score)
            elif moderate_neg_count >= 2:
                return "negative", 0.70
            # Strong positive keywords override neutral
            elif strong_pos_count >= 1:
                return "positive", max(0.75, original_score)
            elif moderate_pos_count >= 2:
                return "positive", 0.70
        
        # Boost confidence for already classified sentiments with matching keywords
        elif original_sentiment == "negative":
            if strong_neg_count >= 1 or moderate_neg_count >= 1:
                return "negative", min(1.0, original_score + 0.1)
        elif original_sentiment == "positive":
            if strong_pos_count >= 1 or moderate_pos_count >= 1:
                return "positive", min(1.0, original_score + 0.1)
        
        return original_sentiment, original_score

    def _calculate_weighted_sentiment(self, sentiments):
        """Calculate sentiment with confidence weighting."""
        if not sentiments:
            return 0, "Neutral"
        
        # Weight by confidence score
        weighted_sum = sum(
            s["score"] * (1 if s["sentiment"] == "positive" else -1 if s["sentiment"] == "negative" else 0)
            for s in sentiments
        )
        
        total_confidence = sum(s["score"] for s in sentiments)
        avg_score = weighted_sum / total_confidence if total_confidence > 0 else 0
        
        # More nuanced categories
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

    def analyze_company_sentiment(self, company_name, max_headlines=10):
        """Analyze sentiment with enhanced filtering and weighting."""
        headlines = self.fetch_company_news(company_name, max_headlines)
        
        if not headlines:
            return {
                'overall': "No recent news found",
                'score': 0,
                'details': [],
                'summary': {
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0,
                    'total': 0
                }
            }

        # Extract titles for analysis
        titles = [h['title'] for h in headlines]
        results = self.sentiment_analyzer(titles)
        
        sentiments = []
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for headline, result in zip(headlines, results):
            original_sentiment = result["label"].lower()
            original_score = result["score"]
            
            # Apply keyword-based adjustment
            adjusted_sentiment, adjusted_score = self._adjust_sentiment_with_keywords(
                headline['title'], 
                original_sentiment, 
                original_score
            )
            
            sentiments.append({
                "headline": headline['title'],
                "sentiment": adjusted_sentiment,
                "score": adjusted_score,
                "source": headline['source'],
                "date": headline.get('date', 'Unknown'),
                "original_sentiment": original_sentiment if adjusted_sentiment != original_sentiment else None
            })
            
            sentiment_counts[adjusted_sentiment] += 1
        
        # Calculate weighted overall sentiment
        avg_score, overall = self._calculate_weighted_sentiment(sentiments)
        
        # Sort by confidence (most confident first)
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
            }
        }
    
    def __del__(self):
        """Clean up session on deletion."""
        if hasattr(self, 'session'):
            self.session.close()


# Enhanced usage example
if __name__ == "__main__":
    analyzer = CompanySentimentAnalyzer()
    
    company = "OpenAI"
    result = analyzer.analyze_company_sentiment(company)
    
    print(f"\n{'='*60}")
    print(f"SENTIMENT ANALYSIS FOR: {company}")
    print(f"{'='*60}")
    print(f"\nOverall Sentiment: {result['overall']} (Score: {result['score']})")
    print(f"\nSummary:")
    print(f"  ✓ Positive: {result['summary']['positive']}")
    print(f"  ✗ Negative: {result['summary']['negative']}")
    print(f"  ○ Neutral:  {result['summary']['neutral']}")
    print(f"  Avg Confidence: {result['summary']['avg_confidence']}")
    
    print(f"\n{'─'*60}")
    print("Detailed Analysis (sorted by confidence):")
    print(f"{'─'*60}\n")
    
    for i, s in enumerate(result['details'], 1):
        sentiment_emoji = "📈" if s['sentiment'] == "positive" else "📉" if s['sentiment'] == "negative" else "➡️"
        adjustment_note = f" (adjusted from {s['original_sentiment']})" if s.get('original_sentiment') else ""
        print(f"{i}. {sentiment_emoji} [{s['sentiment'].upper()}] {s['score']:.2f} confidence{adjustment_note}")
        print(f"   {s['headline']}")
        print(f"   Source: {s['source']} | Date: {s['date']}")
        print()