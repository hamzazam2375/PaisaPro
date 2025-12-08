from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager
from dotenv import load_dotenv
import logging
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re
from urllib.parse import quote_plus

# Scheduler imports
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Selenium / scraping imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

class DatabaseManager:
    """Manages PostgreSQL connections"""
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("Database URL not provided")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(self.db_url)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def initialize_db(self):
        """Create required tables"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS shopping_lists (
                            id SERIAL PRIMARY KEY,
                            user_id VARCHAR(255) NOT NULL,
                            name VARCHAR(255) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(user_id, name)
                        )
                    """)
                    
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS shopping_list_items (
                            id SERIAL PRIMARY KEY,
                            list_id INTEGER NOT NULL REFERENCES shopping_lists(id) ON DELETE CASCADE,
                            product_name VARCHAR(255) NOT NULL,
                            quantity INTEGER DEFAULT 1,
                            status VARCHAR(50) DEFAULT 'pending',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(list_id, product_name)
                        )
                    """)
                    
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS product_recommendations (
                            id SERIAL PRIMARY KEY,
                            list_item_id INTEGER NOT NULL REFERENCES shopping_list_items(id) ON DELETE CASCADE,
                            product_name VARCHAR(255) NOT NULL,
                            source VARCHAR(100) NOT NULL,
                            price_pkr FLOAT NOT NULL,
                            price_usd FLOAT NOT NULL,
                            url TEXT,
                            rank INTEGER,
                            is_current BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP
                        )
                    """)
                    
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_recommendations_current 
                        ON product_recommendations(list_item_id, is_current)
                    """)
                    
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_recommendations_expires
                        ON product_recommendations(expires_at)
                    """)
                    
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS price_history (
                            id SERIAL PRIMARY KEY,
                            product_name VARCHAR(255) NOT NULL,
                            source VARCHAR(100) NOT NULL,
                            price_pkr FLOAT NOT NULL,
                            price_usd FLOAT NOT NULL,
                            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_price_history_product
                        ON price_history(product_name, recorded_at DESC)
                    """)
            
            logger.info("✅ Database initialized successfully!")
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}")
            raise

# ============================================================================
# UTILITY SERVICES
# ============================================================================

class CurrencyConverter:
    """Handles currency conversion"""
    
    def __init__(self, exchange_rate: float = 280.0):
        self._exchange_rate = exchange_rate
    
    def pkr_to_usd(self, pkr: float) -> float:
        return round(pkr / self._exchange_rate, 2)
    
    @property
    def exchange_rate(self) -> float:
        return self._exchange_rate


class PriceExtractor:
    """Extracts price from text"""
    
    PRICE_PATTERNS = [
        r"Rs\.?\s*([\d,]+)",
        r"PKR\.?\s*([\d,]+)",
        r"₨\.?\s*([\d,]+)",
        r"\b([\d,]+)\s*Rs",
        r"\b([\d,]+)\s*PKR"
    ]
    
    @staticmethod
    def extract(text: str) -> Optional[float]:
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


# ============================================================================
# SCRAPER CONFIG & MODELS
# ============================================================================

from dataclasses import dataclass

@dataclass
class ScraperConfig:
    exchange_rate: float = 280.0
    headless: bool = True
    timeout: int = 30
    max_results: int = 20
    scroll_count: int = 3
    scroll_delay: int = 2
    max_workers: int = 3
    sort_by_price: bool = True
    top_n_recommendations: int = 3


# ============================================================================
# CONCRETE SCRAPERS
# ============================================================================

class BaseProductScraper:
    """Base scraper"""
    
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.currency_converter = CurrencyConverter(config.exchange_rate)
        self.price_extractor = PriceExtractor()
        self._driver: Optional[webdriver.Chrome] = None
    
    def scrape(self, query: str, sort_by_price: bool = True) -> List[Dict[str, Any]]:
        try:
            self._initialize_driver()
            self._navigate_to_search(query)
            self._wait_for_page_load()
            self._scroll_page()
            raw_data = self._extract_products()
            products = self._parse_products(raw_data)
            return self._sort_products(products, sort_by_price)
        except Exception as e:
            logger.error(f"Error in {self.get_source_name()}: {e}")
            return []
        finally:
            self._cleanup()
    
    def _initialize_driver(self):
        self._driver = WebDriverFactory.create_driver(self.config.headless)
    
    def _wait_for_page_load(self):
        time.sleep(5)
    
    def _scroll_page(self):
        for _ in range(self.config.scroll_count):
            if self._driver:
                self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(self.config.scroll_delay)
    
    def _sort_products(self, products: List[Dict[str, Any]], sort_by_price: bool = True) -> List[Dict[str, Any]]:
        if sort_by_price:
            return sorted(products, key=lambda p: p['price_pkr'])
        return products
    
    def _cleanup(self):
        if self._driver:
            try:
                self._driver.quit()
            except:
                pass
    
    def get_source_name(self) -> str:
        raise NotImplementedError
    
    def _navigate_to_search(self, query: str):
        raise NotImplementedError
    
    def _extract_products(self) -> List[Any]:
        raise NotImplementedError
    
    def _parse_products(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        raise NotImplementedError


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
        selectors = ["a.product-title-ellipsis", "h3 a", "div.card__heading a", ".card__content a"]
        
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


# ============================================================================
# PRICE COMPARISON SERVICE
# ============================================================================

class PriceComparisonService:
    """Main price comparison service"""
    
    def __init__(self, config: ScraperConfig):
        self.config = config
        self._print_lock = Lock()
        self.scrapers = {
            'daraz': DarazScraper(config),
            'alfatah': AlfatahScraper(config),
        }
    
    def find_products(
        self, 
        query: str, 
        sources: Optional[List[str]] = None,
        top_n: int = 10,
        sort_by_price: bool = True,
        parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """Find products across sources"""
        
        if sources is None:
            sources = list(self.scrapers.keys())
        
        logger.info(f"🔍 Searching for '{query}' across {len(sources)} sources...")
        
        all_products = []
        
        if parallel:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_source = {
                    executor.submit(self._scrape_source, source, query): source
                    for source in sources if source in self.scrapers
                }
                
                for future in as_completed(future_to_source):
                    try:
                        products = future.result()
                        all_products.extend(products)
                    except Exception as e:
                        logger.error(f"Error scraping: {e}")
        else:
            for source in sources:
                if source in self.scrapers:
                    products = self._scrape_source(source, query)
                    all_products.extend(products)
        
        if sort_by_price:
            all_products.sort(key=lambda p: p['price_pkr'])
        
        return all_products[:top_n]
    
    def _scrape_source(self, source: str, query: str) -> List[Dict[str, Any]]:
        """Scrape a single source"""
        try:
            scraper = self.scrapers.get(source)
            if not scraper:
                return []
            
            logger.info(f"   📦 Scraping {source}...")
            products = scraper.scrape(query)
            logger.info(f"   ✅ Found {len(products)} products from {source}")
            return products
        except Exception as e:
            logger.error(f"   ❌ Error scraping {source}: {e}")
            return []

# ============================================================================
# BACKGROUND SCHEDULER SETUP
# ============================================================================

scheduler = BackgroundScheduler()

def refresh_all_stale_prices():
    """Refresh prices for all stale items across all shopping lists"""
    try:
        logger.info("🔄 Starting scheduled price refresh for all stale items...")
        
        cart_service = ShoppingCartService(db, price_service)
        
        # Find all stale items across all lists
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT 
                        sli.id as item_id, 
                        sli.product_name,
                        sl.id as list_id,
                        sl.name as list_name,
                        sl.user_id,
                        MAX(pr.created_at) as last_updated
                    FROM shopping_list_items sli
                    JOIN shopping_lists sl ON sli.list_id = sl.id
                    LEFT JOIN product_recommendations pr ON sli.id = pr.list_item_id AND pr.is_current = TRUE
                    WHERE sli.status = 'pending'
                    AND (
                        pr.id IS NULL  -- No current recommendations
                        OR pr.created_at < NOW() - INTERVAL '6 hours'  -- Stale recommendations
                    )
                    GROUP BY sli.id, sli.product_name, sl.id, sl.name, sl.user_id
                    ORDER BY last_updated NULLS FIRST
                """)
                stale_items = cur.fetchall()
        
        if not stale_items:
            logger.info("✅ No stale items found for refresh")
            return
        
        logger.info(f"📦 Found {len(stale_items)} stale items to refresh")
        
        refreshed_count = 0
        failed_count = 0
        
        for item in stale_items:
            item_id, product_name, list_id, list_name, user_id, last_updated = item
            
            try:
                logger.info(f"   🔍 Refreshing prices for '{product_name}' (List: {list_name})")
                
                # Fetch new prices
                products = price_service.find_products(
                    query=product_name, 
                    top_n=20,
                    parallel=True
                )
                
                if products:
                    # Cache the new recommendations
                    cart_service.cache_product_recommendations(item_id, product_name, products, 3)
                    refreshed_count += 1
                    logger.info(f"   ✅ Refreshed {len(products)} prices for '{product_name}'")
                else:
                    logger.warning(f"   ⚠️  No prices found for '{product_name}'")
                    failed_count += 1
                    
                # Small delay to be respectful to websites
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"   ❌ Failed to refresh '{product_name}': {e}")
                failed_count += 1
        
        logger.info(f"🎉 Scheduled refresh completed: {refreshed_count} updated, {failed_count} failed")
        
    except Exception as e:
        logger.error(f"💥 Critical error in scheduled price refresh: {e}")

def refresh_specific_list_prices(list_id: int):
    """Refresh prices for a specific shopping list"""
    try:
        cart_service = ShoppingCartService(db, price_service)
        
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, product_name 
                    FROM shopping_list_items 
                    WHERE list_id = %s AND status = 'pending'
                """, (list_id,))
                items = cur.fetchall()
        
        for item_id, product_name in items:
            try:
                products = price_service.find_products(query=product_name, top_n=20)
                if products:
                    cart_service.cache_product_recommendations(item_id, product_name, products, 3)
            except Exception as e:
                logger.error(f"Error refreshing {product_name}: {e}")
        
        logger.info(f"✅ Refreshed {len(items)} items in list {list_id}")
    except Exception as e:
        logger.error(f"Error refreshing list {list_id}: {e}")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ItemStatus(str, Enum):
    PENDING = "pending"
    PURCHASED = "purchased"

class PriceRecommendation(BaseModel):
    product_name: str
    source: str
    price_pkr: float
    price_usd: float
    url: str
    rank: int
    created_at: datetime
    is_fresh: bool = True

class OptimizedCartItem(BaseModel):
    item_id: int
    product_name: str
    quantity: int
    recommendations: List[PriceRecommendation]
    cheapest_option: PriceRecommendation
    total_cost_pkr: float
    total_cost_usd: float
    potential_savings_pkr: float = 0.0

class ShoppingListResponse(BaseModel):
    list_id: int
    list_name: str
    user_id: str
    items: List[OptimizedCartItem]
    total_cart_cost_pkr: float
    total_cart_cost_usd: float
    total_potential_savings_pkr: float
    optimization_timestamp: datetime
    prices_last_updated: Optional[datetime] = None

class CreateShoppingListRequest(BaseModel):
    user_id: str
    list_name: str
    items: List[Dict[str, Any]] = Field(..., description="List of items with 'product_name' and 'quantity'")

class UpdateItemRequest(BaseModel):
    product_name: str
    quantity: int = Field(ge=1)

class UpdateItemQuantityRequest(BaseModel):
    quantity: int = Field(ge=1)

# ============================================================================
# PRICE STALENESS MANAGER
# ============================================================================

class PriceStalnessManager:
    """Manages price freshness"""
    
    PRICE_CACHE_HOURS = 6
    STALE_THRESHOLD_HOURS = 12
    
    @staticmethod
    def is_price_fresh(created_at: datetime) -> bool:
        age = datetime.now() - created_at
        return age.total_seconds() < (PriceStalnessManager.PRICE_CACHE_HOURS * 3600)
    
    @staticmethod
    def get_refresh_needed_items(db: DatabaseManager, list_id: int) -> List[int]:
        """Get items that need price refresh"""
        with db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT DISTINCT sli.id
                    FROM shopping_list_items sli
                    WHERE sli.list_id = %s
                    AND sli.status = %s
                    AND (
                        NOT EXISTS (
                            SELECT 1 FROM product_recommendations pr 
                            WHERE pr.list_item_id = sli.id 
                            AND pr.is_current = TRUE
                        )
                        OR EXISTS (
                            SELECT 1 FROM product_recommendations pr 
                            WHERE pr.list_item_id = sli.id 
                            AND pr.is_current = TRUE
                            AND pr.created_at < NOW() - INTERVAL '6 hours'
                        )
                    )
                """, (list_id, ItemStatus.PENDING.value))
                return [row['id'] for row in cur.fetchall()]

# ============================================================================
# SHOPPING CART SERVICE
# ============================================================================

class ShoppingCartService:
    def __init__(self, db: DatabaseManager, price_service: PriceComparisonService):
        self.db = db
        self.price_service = price_service
        self.staleness_manager = PriceStalnessManager()
        self.top_n = price_service.config.top_n_recommendations
    
    def create_shopping_list(self, user_id: str, list_name: str, items: List[Dict[str, Any]]) -> int:
        """Create new shopping list and fetch prices"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM shopping_lists 
                    WHERE user_id = %s AND name = %s
                """, (user_id, list_name))
                
                existing = cur.fetchone()
                if existing:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Shopping list '{list_name}' already exists for this user"
                    )
                
                cur.execute("""
                    INSERT INTO shopping_lists (user_id, name)
                    VALUES (%s, %s)
                    RETURNING id
                """, (user_id, list_name))
                list_id = cur.fetchone()[0]
                
                item_ids = []
                for item in items:
                    product_name = item.get('product_name')
                    quantity = item.get('quantity', 1)
                    
                    if not product_name:
                        continue
                    
                    cur.execute("""
                        INSERT INTO shopping_list_items (list_id, product_name, quantity)
                        VALUES (%s, %s, %s)
                        RETURNING id
                    """, (list_id, product_name, quantity))
                    item_ids.append((cur.fetchone()[0], product_name))
        
        logger.info(f"📊 Fetching prices for {len(item_ids)} items in list {list_id}")
        for item_id, product_name in item_ids:
            try:
                products = self.price_service.find_products(query=product_name, top_n=20)
                if products:
                    self.cache_product_recommendations(item_id, product_name, products, self.top_n)
            except Exception as e:
                logger.error(f"❌ Error fetching prices for '{product_name}': {e}")
        
        logger.info(f"✅ Created shopping list {list_id} with {len(item_ids)} items")
        return list_id
    
    def add_item_to_list(self, list_id: int, product_name: str, quantity: int = 1):
        """Add item to existing list and fetch prices"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM shopping_lists WHERE id = %s", (list_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Shopping list not found")
                
                cur.execute("""
                    INSERT INTO shopping_list_items (list_id, product_name, quantity)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (list_id, product_name) 
                    DO UPDATE SET quantity = shopping_list_items.quantity + EXCLUDED.quantity
                    RETURNING id
                """, (list_id, product_name, quantity))
                item_id = cur.fetchone()[0]
                
                cur.execute("""
                    UPDATE shopping_lists 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (list_id,))
        
        try:
            products = self.price_service.find_products(query=product_name, top_n=20)
            if products:
                self.cache_product_recommendations(item_id, product_name, products, self.top_n)
        except Exception as e:
            logger.error(f"Error fetching prices for '{product_name}': {e}")
    
    def update_item_quantity(self, item_id: int, quantity: int):
        """Update quantity of an existing item"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE shopping_list_items
                    SET quantity = %s
                    WHERE id = %s
                    RETURNING list_id
                """, (quantity, item_id))
                
                result = cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="Item not found")
                
                list_id = result[0]
                
                cur.execute("""
                    UPDATE shopping_lists 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (list_id,))
    
    def remove_item_from_list(self, item_id: int):
        """Remove item from list"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM shopping_list_items
                    WHERE id = %s
                    RETURNING list_id
                """, (item_id,))
                
                result = cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="Item not found")
                
                list_id = result[0]
                
                cur.execute("""
                    UPDATE shopping_lists 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (list_id,))
    
    def cache_product_recommendations(self, list_item_id: int, product_name: str, products: List[Dict[str, Any]], top_n: int = 3):
        """Cache top N cheapest products"""
        sorted_products = sorted(products, key=lambda p: p['price_pkr'])[:top_n]
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE product_recommendations
                    SET is_current = FALSE
                    WHERE list_item_id = %s AND is_current = TRUE
                """, (list_item_id,))
                
                expires_at = datetime.now() + timedelta(hours=PriceStalnessManager.PRICE_CACHE_HOURS)
                
                for rank, product in enumerate(sorted_products, 1):
                    cur.execute("""
                        INSERT INTO product_recommendations 
                        (list_item_id, product_name, source, price_pkr, price_usd, url, rank, is_current, expires_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s)
                    """, (
                        list_item_id, product_name, product['source'], product['price_pkr'], 
                        product['price_usd'], product.get('url', 'N/A'), rank, expires_at
                    ))
                    
                    cur.execute("""
                        INSERT INTO price_history 
                        (product_name, source, price_pkr, price_usd)
                        VALUES (%s, %s, %s, %s)
                    """, (product_name, product['source'], product['price_pkr'], product['price_usd']))
        
        logger.info(f"💾 Cached {len(sorted_products)} recommendations for item {list_item_id}")
    
    def get_optimized_cart(self, list_id: int, refresh_prices: bool = False) -> ShoppingListResponse:
        """Get optimized cart with best prices"""
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, user_id, updated_at 
                    FROM shopping_lists 
                    WHERE id = %s
                """, (list_id,))
                list_info = cur.fetchone()
                if not list_info:
                    raise HTTPException(status_code=404, detail="Shopping list not found")
                
                cur.execute("""
                    SELECT id, product_name, quantity, status
                    FROM shopping_list_items
                    WHERE list_id = %s
                    ORDER BY created_at
                """, (list_id,))
                items = cur.fetchall()
        
        items_needing_refresh = []
        if refresh_prices:
            items_needing_refresh = self.staleness_manager.get_refresh_needed_items(self.db, list_id)
            logger.info(f"🔄 Refreshing prices for {len(items_needing_refresh)} items")
        
        for item in items:
            if refresh_prices and item['id'] in items_needing_refresh:
                try:
                    products = self.price_service.find_products(query=item['product_name'], top_n=20)
                    if products:
                        self.cache_product_recommendations(item['id'], item['product_name'], products, self.top_n)
                except Exception as e:
                    logger.error(f"Error refreshing prices for '{item['product_name']}': {e}")
        
        optimized_items = []
        total_cart_pkr = 0
        total_cart_usd = 0
        total_savings = 0
        prices_last_updated = None
        
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for item in items:
                    cur.execute("""
                        SELECT product_name, source, price_pkr, price_usd, url, rank, created_at
                        FROM product_recommendations
                        WHERE list_item_id = %s
                        AND is_current = TRUE
                        ORDER BY rank ASC
                    """, (item['id'],))
                    
                    recommendations_data = cur.fetchall()
                    
                    if not recommendations_data:
                        try:
                            logger.info(f"🔍 No cached prices for '{item['product_name']}', fetching now...")
                            products = self.price_service.find_products(query=item['product_name'], top_n=20)
                            if products:
                                self.cache_product_recommendations(item['id'], item['product_name'], products, self.top_n)
                                cur.execute("""
                                    SELECT product_name, source, price_pkr, price_usd, url, rank, created_at
                                    FROM product_recommendations
                                    WHERE list_item_id = %s
                                    AND is_current = TRUE
                                    ORDER BY rank ASC
                                """, (item['id'],))
                                recommendations_data = cur.fetchall()
                        except Exception as e:
                            logger.error(f"Error fetching prices for '{item['product_name']}': {e}")
                    
                    recommendations = []
                    for rec in recommendations_data:
                        is_fresh = self.staleness_manager.is_price_fresh(rec['created_at'])
                        recommendations.append(PriceRecommendation(
                            product_name=rec['product_name'],
                            source=rec['source'],
                            price_pkr=rec['price_pkr'],
                            price_usd=rec['price_usd'],
                            url=rec['url'],
                            rank=rec['rank'],
                            created_at=rec['created_at'],
                            is_fresh=is_fresh
                        ))
                        
                        if prices_last_updated is None or rec['created_at'] > prices_last_updated:
                            prices_last_updated = rec['created_at']
                    
                    if recommendations:
                        cheapest = recommendations[0]
                        total_item_pkr = cheapest.price_pkr * item['quantity']
                        total_item_usd = cheapest.price_usd * item['quantity']
                        
                        potential_savings = 0
                        if len(recommendations) > 1:
                            second_cheapest = recommendations[1]
                            potential_savings = (second_cheapest.price_pkr - cheapest.price_pkr) * item['quantity']
                        
                        total_cart_pkr += total_item_pkr
                        total_cart_usd += total_item_usd
                        total_savings += potential_savings
                        
                        optimized_items.append(OptimizedCartItem(
                            item_id=item['id'],
                            product_name=item['product_name'],
                            quantity=item['quantity'],
                            recommendations=recommendations,
                            cheapest_option=cheapest,
                            total_cost_pkr=round(total_item_pkr, 2),
                            total_cost_usd=round(total_item_usd, 2),
                            potential_savings_pkr=round(potential_savings, 2)
                        ))
                    else:
                        logger.warning(f"⚠️  No prices available for '{item['product_name']}'")
        
        return ShoppingListResponse(
            list_id=list_id,
            list_name=list_info['name'],
            user_id=list_info['user_id'],
            items=optimized_items,
            total_cart_cost_pkr=round(total_cart_pkr, 2),
            total_cart_cost_usd=round(total_cart_usd, 2),
            total_potential_savings_pkr=round(total_savings, 2),
            optimization_timestamp=datetime.now(),
            prices_last_updated=prices_last_updated
        )
    
    def mark_item_purchased(self, item_id: int):
        """Mark item as purchased"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE shopping_list_items
                    SET status = %s
                    WHERE id = %s
                    RETURNING list_id
                """, (ItemStatus.PURCHASED.value, item_id))
                
                result = cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="Item not found")
                
                list_id = result[0]
                
                cur.execute("""
                    UPDATE shopping_lists 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (list_id,))
    
    def get_price_history(self, product_name: str, days: int = 30) -> List[Dict]:
        """Get price history for a product"""
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT source, price_pkr, price_usd, recorded_at
                    FROM price_history
                    WHERE product_name = %s
                    AND recorded_at > NOW() - INTERVAL '%s days'
                    ORDER BY recorded_at DESC
                """, (product_name, days))
                return cur.fetchall()
    
    def get_user_lists(self, user_id: str) -> List[Dict]:
        """Get all shopping lists for a user"""
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        sl.id, 
                        sl.name, 
                        sl.created_at, 
                        sl.updated_at,
                        COUNT(sli.id) as item_count,
                        COUNT(CASE WHEN sli.status = 'purchased' THEN 1 END) as purchased_count
                    FROM shopping_lists sl
                    LEFT JOIN shopping_list_items sli ON sl.id = sli.list_id
                    WHERE sl.user_id = %s
                    GROUP BY sl.id, sl.name, sl.created_at, sl.updated_at
                    ORDER BY sl.updated_at DESC
                """, (user_id,))
                return cur.fetchall()
    
    def delete_shopping_list(self, list_id: int, user_id: str):
        """Delete a shopping list"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM shopping_lists 
                    WHERE id = %s AND user_id = %s
                """, (list_id, user_id))
                
                if not cur.fetchone():
                    raise HTTPException(
                        status_code=404, 
                        detail="Shopping list not found or you don't have permission"
                    )
                
                cur.execute("""
                    DELETE FROM shopping_lists WHERE id = %s
                """, (list_id,))

# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

db_url = os.getenv("DATABASE_URL", "postgresql://postgres:warda@localhost:5432/paisapro_db")
db = DatabaseManager(db_url)
config = ScraperConfig(headless=True, top_n_recommendations=3)
price_service = PriceComparisonService(config)

app = FastAPI(
    title="PaisaPro Shopping Cart Optimizer API", 
    version="2.0",
    description="Smart shopping cart with automated price comparison and background price updates"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    try:
        # Initialize database
        db.initialize_db()
        
        # Start background scheduler if not already running
        if not scheduler.running:
            # Schedule price refresh every 6 hours
            scheduler.add_job(
                refresh_all_stale_prices,
                trigger=IntervalTrigger(hours=6),
                id='price_refresh',
                replace_existing=True,
                name='Refresh stale prices every 6 hours'
            )
            
            # Optional: Also run a quick refresh 1 minute after startup
            scheduler.add_job(
                refresh_all_stale_prices,
                trigger='interval',
                minutes=1,
                id='initial_refresh',
                replace_existing=True,
                name='Initial price refresh after startup'
            )
            
            scheduler.start()
            logger.info("✅ Background price scheduler started!")
            logger.info("   - Will refresh stale prices every 6 hours")
            logger.info("   - Initial refresh in 1 minute")
            
            # Print scheduled jobs
            jobs = scheduler.get_jobs()
            for job in jobs:
                logger.info(f"   📅 Scheduled: {job.name} (next: {job.next_run_time})")
                
        logger.info("✅ Application started successfully!")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise

@app.on_event("shutdown")
def shutdown():
    """Shutdown scheduler gracefully"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("✅ Background scheduler stopped")

@app.get("/")
def read_root():
    return {
        "message": "🛒 PaisaPro Shopping Cart Optimizer API",
        "version": "2.0",
        "status": "running",
        "features": [
            "Create shopping lists with auto price comparison",
            "Track top 3 cheapest options per item",
            "Update items and quantities",
            "Automatic background price updates every 6 hours",
            "Manual price refresh options",
            "Multiple carts per user"
        ],
        "background_workers": {
            "price_refresh": "Every 6 hours",
            "initial_refresh": "1 minute after startup"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        
        scheduler_status = "running" if scheduler.running else "stopped"
        job_count = len(scheduler.get_jobs()) if scheduler.running else 0
        
        return {
            "status": "healthy", 
            "database": "connected",
            "scheduler": scheduler_status,
            "active_jobs": job_count
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# ============================================================================
# SCHEDULER MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/scheduler/status")
def get_scheduler_status():
    """Get current scheduler status and jobs"""
    jobs_info = []
    for job in scheduler.get_jobs():
        jobs_info.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time,
            "trigger": str(job.trigger)
        })
    
    return {
        "scheduler_running": scheduler.running,
        "job_count": len(jobs_info),
        "jobs": jobs_info
    }

@app.post("/api/scheduler/refresh-now")
def trigger_immediate_refresh(background_tasks: BackgroundTasks):
    """Trigger an immediate price refresh (can run in background)"""
    background_tasks.add_task(refresh_all_stale_prices)
    
    return {
        "success": True,
        "message": "Immediate price refresh started in background",
        "note": "Check logs for progress"
    }

@app.post("/api/scheduler/refresh-list/{list_id}")
def trigger_list_refresh(list_id: int, background_tasks: BackgroundTasks):
    """Trigger refresh for a specific list"""
    background_tasks.add_task(refresh_specific_list_prices, list_id)
    
    return {
        "success": True,
        "message": f"Price refresh for list {list_id} started in background"
    }

# ============================================================================
# SHOPPING LIST ENDPOINTS
# ============================================================================

@app.post("/api/cart/create")
def create_cart(request: CreateShoppingListRequest):
    """Create a new shopping list with automatic price fetching"""
    try:
        cart_service = ShoppingCartService(db, price_service)
        list_id = cart_service.create_shopping_list(
            user_id=request.user_id,
            list_name=request.list_name,
            items=request.items
        )
        return {
            "success": True,
            "list_id": list_id,
            "message": f"Shopping list '{request.list_name}' created successfully",
            "item_count": len(request.items),
            "note": "Prices fetched automatically for all items"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating cart: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/cart/{list_id}/add-item")
def add_cart_item(
    list_id: int,
    product_name: str = Query(..., description="Product name to add"),
    quantity: int = Query(1, ge=1, description="Quantity to add")
):
    """Add an item to an existing shopping list"""
    try:
        cart_service = ShoppingCartService(db, price_service)
        cart_service.add_item_to_list(list_id, product_name, quantity)
        return {
            "success": True,
            "message": f"Added {quantity}x '{product_name}' to list",
            "note": "Prices fetched automatically"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding item: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/cart/item/{item_id}/quantity")
def update_item_quantity_endpoint(item_id: int, request: UpdateItemQuantityRequest):
    """Update quantity of an existing item"""
    try:
        cart_service = ShoppingCartService(db, price_service)
        cart_service.update_item_quantity(item_id, request.quantity)
        return {
            "success": True,
            "message": f"Updated item quantity to {request.quantity}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating quantity: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/cart/item/{item_id}")
def remove_cart_item(item_id: int):
    """Remove an item from shopping list"""
    try:
        cart_service = ShoppingCartService(db, price_service)
        cart_service.remove_item_from_list(item_id)
        return {
            "success": True,
            "message": "Item removed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing item: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/cart/{list_id}/optimized", response_model=ShoppingListResponse)
def get_optimized_cart_endpoint(
    list_id: int,
    refresh_prices: bool = Query(False, description="Force refresh all prices")
):
    """Get optimized cart with best prices (top 3 cheapest per item)"""
    try:
        cart_service = ShoppingCartService(db, price_service)
        return cart_service.get_optimized_cart(list_id, refresh_prices)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cart: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/cart/item/{item_id}/purchased")
def mark_purchased(item_id: int):
    """Mark an item as purchased"""
    try:
        cart_service = ShoppingCartService(db, price_service)
        cart_service.mark_item_purchased(item_id)
        return {
            "success": True,
            "message": "Item marked as purchased"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking purchased: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/user/{user_id}/lists")
def get_user_lists_endpoint(user_id: str):
    """Get all shopping lists for a user"""
    try:
        cart_service = ShoppingCartService(db, price_service)
        lists = cart_service.get_user_lists(user_id)
        return {
            "success": True,
            "user_id": user_id,
            "list_count": len(lists),
            "lists": lists
        }
    except Exception as e:
        logger.error(f"Error fetching lists: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/cart/{list_id}")
def delete_cart(
    list_id: int,
    user_id: str = Query(..., description="User ID for verification")
):
    """Delete a shopping list"""
    try:
        cart_service = ShoppingCartService(db, price_service)
        cart_service.delete_shopping_list(list_id, user_id)
        return {
            "success": True,
            "message": "Shopping list deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting list: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# PRICE & HISTORY ENDPOINTS
# ============================================================================

@app.get("/api/price-history/{product_name}")
def price_history(
    product_name: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of history")
):
    """Get price history for a product"""
    try:
        cart_service = ShoppingCartService(db, price_service)
        history = cart_service.get_price_history(product_name, days)
        return {
            "success": True,
            "product": product_name,
            "history": history,
            "days": days,
            "record_count": len(history)
        }
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/compare")
def compare_prices(
    query: str = Query(..., description="Product to search for"),
    top_n: int = Query(10, ge=1, le=100, description="Number of results"),
    sort: bool = Query(True, description="Sort by price"),
    parallel: bool = Query(True, description="Use parallel scraping")
):
    """Direct price comparison (without saving to cart)"""
    try:
        products = price_service.find_products(
            query=query,
            top_n=top_n,
            sort_by_price=sort,
            parallel=parallel
        )
        return {
            "success": True,
            "query": query,
            "count": len(products),
            "products": products
        }
    except Exception as e:
        logger.error(f"Error in comparison: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

@app.post("/api/cart/{list_id}/refresh-prices")
async def refresh_prices_background(list_id: int, background_tasks: BackgroundTasks):
    """Trigger background price refresh for a shopping list with enhanced info"""
    try:
        # Check if list exists and get item count
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT sl.name, COUNT(sli.id) as item_count
                    FROM shopping_lists sl
                    LEFT JOIN shopping_list_items sli ON sl.id = sli.list_id AND sli.status = 'pending'
                    WHERE sl.id = %s
                    GROUP BY sl.id, sl.name
                """, (list_id,))
                result = cur.fetchone()
                
                if not result:
                    raise HTTPException(status_code=404, detail="Shopping list not found")
                
                list_name, item_count = result
        
        background_tasks.add_task(refresh_specific_list_prices, list_id)
        
        return {
            "success": True,
            "message": "Price refresh started in background",
            "list_id": list_id,
            "list_name": list_name,
            "pending_items": item_count,
            "note": "Prices will be updated within a few minutes"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting background refresh: {e}")
        raise HTTPException(status_code=400, detail=str(e))

def refresh_cart_prices(list_id: int, cart_service: ShoppingCartService):
    """Background task to refresh prices for a specific cart"""
    try:
        logger.info(f"🔄 Starting background price refresh for list {list_id}")
        refresh_specific_list_prices(list_id)
        logger.info(f"✅ Background price refresh completed for list {list_id}")
    except Exception as e:
        logger.error(f"❌ Background refresh failed for list {list_id}: {e}")

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)