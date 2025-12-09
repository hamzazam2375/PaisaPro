"""
PaisaPro Shopping Cart Backend - FastAPI Service
Integrates with Django PostgreSQL database for shopping list management and price comparison
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from contextlib import asynccontextmanager
import os
import time
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import uvicorn
from contextlib import contextmanager
from dotenv import load_dotenv
import random
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from urllib.parse import quote_plus
import requests

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
    """Manages PostgreSQL connections - integrates with Django database"""
    
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
            raise e
        finally:
            conn.close()
    
    def initialize_db(self):
        """Create required tables for shopping cart"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Shopping lists table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS shopping_lists (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL REFERENCES sda_app_user(id) ON DELETE CASCADE,
                            name VARCHAR(255) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Shopping list items table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS shopping_list_items (
                            id SERIAL PRIMARY KEY,
                            list_id INTEGER NOT NULL REFERENCES shopping_lists(id) ON DELETE CASCADE,
                            product_name VARCHAR(500) NOT NULL,
                            quantity INTEGER DEFAULT 1,
                            status VARCHAR(50) DEFAULT 'pending',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Price cache table (stores top 3 recommendations per item)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS price_recommendations (
                            id SERIAL PRIMARY KEY,
                            list_item_id INTEGER NOT NULL REFERENCES shopping_list_items(id) ON DELETE CASCADE,
                            product_name VARCHAR(500) NOT NULL,
                            source VARCHAR(100) NOT NULL,
                            price_pkr DECIMAL(10, 2) NOT NULL,
                            price_usd DECIMAL(10, 2) NOT NULL,
                            url TEXT,
                            rank INTEGER NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            is_fresh BOOLEAN DEFAULT TRUE
                        )
                    """)
                    
                    # Create indexes for performance
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_shopping_lists_user 
                        ON shopping_lists(user_id)
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_list_items_list 
                        ON shopping_list_items(list_id)
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_price_recs_item 
                        ON price_recommendations(list_item_id)
                    """)
            
            logger.info("✅ Shopping cart database tables initialized successfully!")
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
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        return None


class WebDriverFactory:
    """Factory for creating WebDriver instances"""
    
    @staticmethod
    def create_driver(headless: bool = True) -> webdriver.Chrome:
        options = Options()
        
        if headless:
            options.add_argument("--headless")
        
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
                futures = {executor.submit(self._scrape_source, source, query): source for source in sources}
                for future in as_completed(futures):
                    all_products.extend(future.result())
        else:
            for source in sources:
                all_products.extend(self._scrape_source(source, query))
        
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
# SHOPPING CART SERVICE
# ============================================================================

class ShoppingCartService:
    def __init__(self, db: DatabaseManager, price_service: PriceComparisonService):
        self.db = db
        self.price_service = price_service
        self.top_n = price_service.config.top_n_recommendations
    
    def create_shopping_list(self, user_id: int, list_name: str, items: List[Dict[str, Any]]) -> int:
        """Create new shopping list and fetch prices"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Create list
                cur.execute(
                    "INSERT INTO shopping_lists (user_id, name) VALUES (%s, %s) RETURNING id",
                    (user_id, list_name)
                )
                list_id = cur.fetchone()[0]
                
                # Add items
                item_ids = []
                for item in items:
                    if item.get('product_name'):
                        cur.execute(
                            "INSERT INTO shopping_list_items (list_id, product_name, quantity) VALUES (%s, %s, %s) RETURNING id",
                            (list_id, item['product_name'], item.get('quantity', 1))
                        )
                        item_id = cur.fetchone()[0]
                        item_ids.append((item_id, item['product_name']))
        
        # Fetch prices for each item
        logger.info(f"📊 Fetching prices for {len(item_ids)} items in list {list_id}")
        for item_id, product_name in item_ids:
            try:
                products = self.price_service.find_products(product_name, top_n=20, parallel=True)
                if products:
                    self.cache_product_recommendations(item_id, product_name, products, self.top_n)
            except Exception as e:
                logger.error(f"Error fetching prices for {product_name}: {e}")
        
        logger.info(f"✅ Created shopping list {list_id} with {len(item_ids)} items")
        return list_id
    
    def add_item_to_list(self, list_id: int, product_name: str, quantity: int = 1):
        """Add item to existing list and fetch prices"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO shopping_list_items (list_id, product_name, quantity) VALUES (%s, %s, %s) RETURNING id",
                    (list_id, product_name, quantity)
                )
                item_id = cur.fetchone()[0]
        
        try:
            products = self.price_service.find_products(product_name, top_n=20, parallel=True)
            if products:
                self.cache_product_recommendations(item_id, product_name, products, self.top_n)
        except Exception as e:
            logger.error(f"Error fetching prices for {product_name}: {e}")
    
    def update_item_quantity(self, item_id: int, quantity: int):
        """Update quantity of an existing item"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE shopping_list_items SET quantity = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (quantity, item_id)
                )
    
    def remove_item_from_list(self, item_id: int):
        """Remove item from list"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM shopping_list_items WHERE id = %s", (item_id,))
    
    def cache_product_recommendations(self, list_item_id: int, product_name: str, products: List[Dict[str, Any]], top_n: int = 3):
        """Cache top N cheapest products"""
        sorted_products = sorted(products, key=lambda p: p['price_pkr'])[:top_n]
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Delete old recommendations
                cur.execute("DELETE FROM price_recommendations WHERE list_item_id = %s", (list_item_id,))
                
                # Insert new recommendations
                for rank, product in enumerate(sorted_products, 1):
                    cur.execute("""
                        INSERT INTO price_recommendations 
                        (list_item_id, product_name, source, price_pkr, price_usd, url, rank)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        list_item_id,
                        product_name,
                        product['source'],
                        product['price_pkr'],
                        product['price_usd'],
                        product['url'],
                        rank
                    ))
        
        logger.info(f"💾 Cached {len(sorted_products)} recommendations for item {list_item_id}")
    
    def get_optimized_cart(self, list_id: int, refresh_prices: bool = False):
        """Get optimized cart with best prices"""
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get list info
                cur.execute("SELECT * FROM shopping_lists WHERE id = %s", (list_id,))
                list_info = cur.fetchone()
                
                if not list_info:
                    raise HTTPException(status_code=404, detail="List not found")
                
                # Get all items in list
                cur.execute("""
                    SELECT id, product_name, quantity, status 
                    FROM shopping_list_items 
                    WHERE list_id = %s
                    ORDER BY created_at
                """, (list_id,))
                items = cur.fetchall()
        
        optimized_items = []
        total_cart_pkr = 0
        total_cart_usd = 0
        total_savings = 0
        prices_last_updated = None
        
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for item in items:
                    # Get recommendations for this item
                    cur.execute("""
                        SELECT * FROM price_recommendations 
                        WHERE list_item_id = %s 
                        ORDER BY rank
                    """, (item['id'],))
                    recommendations = cur.fetchall()
                    
                    if not recommendations:
                        continue
                    
                    # Convert to list of dicts
                    recs_list = []
                    for rec in recommendations:
                        recs_list.append({
                            'product_name': rec['product_name'],
                            'source': rec['source'],
                            'price_pkr': float(rec['price_pkr']),
                            'price_usd': float(rec['price_usd']),
                            'url': rec['url'],
                            'rank': rec['rank'],
                            'created_at': rec['created_at'].isoformat(),
                            'is_fresh': rec['is_fresh']
                        })
                    
                    cheapest = recs_list[0]
                    item_total_pkr = cheapest['price_pkr'] * item['quantity']
                    item_total_usd = cheapest['price_usd'] * item['quantity']
                    
                    # Calculate potential savings (difference between cheapest and most expensive in top 3)
                    if len(recs_list) > 1:
                        most_expensive = max(recs_list, key=lambda x: x['price_pkr'])
                        potential_savings = (most_expensive['price_pkr'] - cheapest['price_pkr']) * item['quantity']
                    else:
                        potential_savings = 0
                    
                    optimized_items.append({
                        'item_id': item['id'],
                        'product_name': item['product_name'],
                        'quantity': item['quantity'],
                        'status': item['status'],
                        'recommendations': recs_list,
                        'cheapest_option': cheapest,
                        'total_cost_pkr': round(item_total_pkr, 2),
                        'total_cost_usd': round(item_total_usd, 2),
                        'potential_savings_pkr': round(potential_savings, 2)
                    })
                    
                    total_cart_pkr += item_total_pkr
                    total_cart_usd += item_total_usd
                    total_savings += potential_savings
                    
                    if not prices_last_updated or recommendations[0]['created_at'] > prices_last_updated:
                        prices_last_updated = recommendations[0]['created_at']
        
        return {
            'list_id': list_id,
            'list_name': list_info['name'],
            'user_id': list_info['user_id'],
            'items': optimized_items,
            'total_cart_cost_pkr': round(total_cart_pkr, 2),
            'total_cart_cost_usd': round(total_cart_usd, 2),
            'total_potential_savings_pkr': round(total_savings, 2),
            'optimization_timestamp': datetime.now().isoformat(),
            'prices_last_updated': prices_last_updated.isoformat() if prices_last_updated else None
        }
    
    def mark_item_purchased(self, item_id: int):
        """Mark item as purchased"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE shopping_list_items SET status = 'purchased', updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (item_id,)
                )
    
    def mark_all_purchased(self, list_id: int, user_id: int):
        """Mark all items in a list as purchased"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Verify ownership
                cur.execute("SELECT user_id FROM shopping_lists WHERE id = %s", (list_id,))
                result = cur.fetchone()
                if not result or result[0] != user_id:
                    raise HTTPException(status_code=404, detail="List not found or access denied")
                
                # Mark all items as purchased
                cur.execute("""
                    UPDATE shopping_list_items 
                    SET status = 'purchased', updated_at = CURRENT_TIMESTAMP 
                    WHERE list_id = %s
                """, (list_id,))
                
                # Update list timestamp
                cur.execute("""
                    UPDATE shopping_lists 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (list_id,))
                
                logger.info(f"✅ Marked all items as purchased in list {list_id}")
    
    def get_expense_data_for_list(self, list_id: int) -> Dict:
        """Get total cost for creating expense (for all items with price recommendations)"""
        cart_data = self.get_optimized_cart(list_id)
        
        # Calculate total for all items with recommendations (regardless of purchase status)
        total_usd = cart_data.get('total_cart_cost_usd', 0)
        total_pkr = cart_data.get('total_cart_cost_pkr', 0)
        
        return {
            "amount": round(total_usd, 2),
            "amount_usd": round(total_usd, 2),
            "amount_pkr": round(total_pkr, 2),
            "description": f"Shopping: {cart_data.get('list_name', 'List')}"
        }
    
    def get_user_lists(self, user_id: int) -> List[Dict]:
        """Get all shopping lists for a user, including total price in USD"""
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
                lists = cur.fetchall()
                result = []
                for l in lists:
                    # Calculate total price in USD for the list
                    cur.execute("""
                        SELECT SUM(pr.price_usd * sli.quantity) AS total_price_usd
                        FROM shopping_list_items sli
                        LEFT JOIN price_recommendations pr ON sli.id = pr.list_item_id AND pr.rank = 1
                        WHERE sli.list_id = %s
                    """, (l['id'],))
                    price_row = cur.fetchone()
                    total_price_usd = price_row['total_price_usd'] if price_row and price_row['total_price_usd'] is not None else 0.0
                    result.append({
                        'id': l['id'],
                        'name': l['name'],
                        'created_at': l['created_at'].isoformat(),
                        'updated_at': l['updated_at'].isoformat(),
                        'item_count': l['item_count'],
                        'purchased_count': l['purchased_count'],
                        'total_price_usd': float(total_price_usd)
                    })
                return result
    
    def add_items_to_list(self, list_id: int, user_id: int, items: List[Dict]):
        """Add items to an existing shopping list"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Verify ownership
                cur.execute("SELECT user_id FROM shopping_lists WHERE id = %s", (list_id,))
                result = cur.fetchone()
                if not result or result[0] != user_id:
                    raise HTTPException(status_code=404, detail="List not found or access denied")
                
                # Add items and get recommendations
                for item in items:
                    # Insert item
                    cur.execute("""
                        INSERT INTO shopping_list_items (list_id, product_name, quantity)
                        VALUES (%s, %s, %s) RETURNING id
                    """, (list_id, item['product_name'], item.get('quantity', 1)))
                    item_id = cur.fetchone()[0]
                    
                    # Get price recommendations
                    logger.info(f"🔍 Searching for '{item['product_name']}' across {len(self.sources)} sources...")
                    products = self.price_service.find_products(
                        query=item['product_name'],
                        top_n=3,
                        parallel=True
                    )
                    
                    # Cache top 3 recommendations
                    for rank, product in enumerate(products[:3], 1):
                        cur.execute("""
                            INSERT INTO price_recommendations 
                            (list_item_id, product_name, source, price_pkr, price_usd, url, rank)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            item_id,
                            product.product_name,
                            product.source,
                            product.price_pkr,
                            product.price_usd,
                            product.url,
                            rank
                        ))
                    
                    logger.info(f"💾 Cached {len(products[:3])} recommendations for item {item_id}")
                
                # Update list's updated_at timestamp
                cur.execute("""
                    UPDATE shopping_lists 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (list_id,))
                
                logger.info(f"✅ Added {len(items)} items to list {list_id}")
    
    def delete_shopping_list(self, list_id: int, user_id: int):
        """Delete a shopping list"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Verify ownership
                cur.execute("SELECT user_id FROM shopping_lists WHERE id = %s", (list_id,))
                result = cur.fetchone()
                if not result or result[0] != user_id:
                    raise HTTPException(status_code=404, detail="List not found or access denied")
                
                cur.execute("DELETE FROM shopping_lists WHERE id = %s", (list_id,))


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CreateShoppingListRequest(BaseModel):
    user_id: int
    list_name: str
    items: List[Dict[str, Any]] = Field(..., description="List of items with 'product_name' and 'quantity'")


class UpdateItemQuantityRequest(BaseModel):
    quantity: int = Field(ge=1)


# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

# Build database URL from environment variables (same as Django)
DB_NAME = os.getenv("DB_NAME", "paisapro_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "20242024")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
db = DatabaseManager(db_url)
config = ScraperConfig(headless=True, top_n_recommendations=3)
price_service = PriceComparisonService(config)
cart_service = ShoppingCartService(db, price_service)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        db.initialize_db()
        logger.info("✅ FastAPI Shopping Cart service started successfully!")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    yield
    # Shutdown
    logger.info("Shopping Cart service shutting down...")

app = FastAPI(
    title="PaisaPro Shopping Cart API", 
    version="1.0",
    description="Smart shopping cart with price comparison integration",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "message": "🛒 PaisaPro Shopping Cart API",
        "version": "1.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# ============================================================================
# SHOPPING LIST ENDPOINTS
# ============================================================================

@app.post("/api/cart/create")
def create_cart(request: CreateShoppingListRequest):
    """Create a new shopping list with automatic price fetching"""
    try:
        list_id = cart_service.create_shopping_list(
            request.user_id,
            request.list_name,
            request.items
        )
        return {
            "success": True,
            "list_id": list_id,
            "message": "Shopping list created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating list: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/cart/{list_id}/add-item")
def add_cart_item(
    list_id: int,
    product_name: str = Query(...),
    quantity: int = Query(1, ge=1)
):
    """Add an item to an existing shopping list"""
    try:
        cart_service.add_item_to_list(list_id, product_name, quantity)
        return {"success": True, "message": "Item added successfully"}
    except Exception as e:
        logger.error(f"Error adding item: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/cart/item/{item_id}/quantity")
def update_item_quantity_endpoint(item_id: int, request: UpdateItemQuantityRequest):
    """Update quantity of an existing item"""
    try:
        cart_service.update_item_quantity(item_id, request.quantity)
        return {"success": True, "message": "Quantity updated"}
    except Exception as e:
        logger.error(f"Error updating quantity: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/cart/item/{item_id}")
def remove_cart_item(item_id: int):
    """Remove an item from shopping list"""
    try:
        cart_service.remove_item_from_list(item_id)
        return {"success": True, "message": "Item removed"}
    except Exception as e:
        logger.error(f"Error removing item: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/cart/{list_id}/optimized")
def get_optimized_cart_endpoint(
    list_id: int,
    refresh_prices: bool = Query(False)
):
    """Get optimized cart with best prices (top 3 cheapest per item)"""
    try:
        cart_data = cart_service.get_optimized_cart(list_id, refresh_prices)
        return {"success": True, **cart_data}
    except Exception as e:
        logger.error(f"Error getting cart: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/cart/item/{item_id}/purchased")
def mark_purchased(item_id: int):
    """Mark an item as purchased"""
    try:
        cart_service.mark_item_purchased(item_id)
        return {"success": True, "message": "Item marked as purchased"}
    except Exception as e:
        logger.error(f"Error marking purchased: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/cart/{list_id}/purchase-all")
def mark_all_purchased(
    list_id: int,
    user_id: int = Query(...)
):
    """Mark all items in a list as purchased"""
    try:
        cart_service.mark_all_purchased(list_id, user_id)
        return {"success": True, "message": "All items marked as purchased"}
    except Exception as e:
        logger.error(f"Error marking all purchased: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/cart/{list_id}/expense-data")
def get_expense_data(list_id: int):
    """Get expense data for creating Django expense"""
    try:
        expense_data = cart_service.get_expense_data_for_list(list_id)
        return {"success": True, **expense_data}
    except Exception as e:
        logger.error(f"Error getting expense data: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/user/{user_id}/lists")
def get_user_lists_endpoint(user_id: int):
    """Get all shopping lists for a user"""
    try:
        lists = cart_service.get_user_lists(user_id)
        return {"success": True, "lists": lists}
    except Exception as e:
        logger.error(f"Error getting lists: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/cart/{list_id}/items")
def add_items_to_cart(
    list_id: int,
    request: CreateShoppingListRequest
):
    """Add items to an existing shopping list"""
    try:
        cart_service.add_items_to_list(list_id, request.user_id, request.items)
        return {"success": True, "message": f"Added {len(request.items)} items to list"}
    except Exception as e:
        logger.error(f"Error adding items: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/cart/{list_id}")
def delete_cart(
    list_id: int,
    user_id: int = Query(...)
):
    """Delete a shopping list"""
    try:
        cart_service.delete_shopping_list(list_id, user_id)
        return {"success": True, "message": "List deleted"}
    except Exception as e:
        logger.error(f"Error deleting list: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PRICE COMPARISON ENDPOINT
# ============================================================================

@app.get("/api/compare")
def compare_prices(
    query: str = Query(...),
    top_n: int = Query(10, ge=1, le=100),
    sort: bool = Query(True),
    parallel: bool = Query(True)
):
    """Direct price comparison (without saving to cart)"""
    try:
        products = price_service.find_products(
            query=query,
            top_n=top_n,
            sort_by_price=sort,
            parallel=parallel
        )
        return products
    except Exception as e:
        logger.error(f"Error comparing prices: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    # Run on port 8002 to avoid conflict with Django (8000) and FastAPI (8001)
    uvicorn.run("shopping_cart_backend:app", host="0.0.0.0", port=8002, reload=True)
