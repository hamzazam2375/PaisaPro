from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time
import re
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

class ProductOut(BaseModel):
    name: str
    price_pkr: float
    price_usd: float
    url: str
    source: str


# ============================================================================
# DATA MODELS
# ============================================================================

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
# UTILITY SERVICES
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


class IOutputHandler(ABC):
    """Interface for output handling"""
    @abstractmethod
    def write(self, message: str):
        pass


class ConsoleOutputHandler(IOutputHandler):
    """Console output handler"""
    def write(self, message: str):
        print(message)


# ============================================================================
# SORTING STRATEGIES
# ============================================================================

class ISortingStrategy(ABC):
    """Interface for sorting strategies"""
    @abstractmethod
    def sort(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass


class PriceSortAscending(ISortingStrategy):
    """Sort products by price in ascending order"""
    def sort(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(products, key=lambda p: p['price_pkr'])


class NoSorting(ISortingStrategy):
    """No sorting - return products as-is"""
    def sort(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return products


# ============================================================================
# SCRAPER INTERFACE
# ============================================================================

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
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(title="Price Comparison API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_CONFIG = ScraperConfig()

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Price Comparison API",
        "version": "2.0",
        "endpoints": {
            "compare": "/api/compare",
            "sources": "/api/sources"
        }
    }

@app.get("/api/sources")
def get_sources():
    """Get available scraper sources"""
    return {
        "sources": ScraperFactory.get_available_scrapers()
    }

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
    
    output = ConsoleOutputHandler()
    service = PriceComparisonService(DEFAULT_CONFIG, output)
    
    products = service.find_products(
        query=query,
        sources=source_list,
        top_n=top_n,
        sort_by_price=sort,
        equal_distribution=equal_distribution,
        parallel=parallel
    )
    
    return [ProductOut(**p) for p in products]


# ============================================================================
# RUN WITH: uvicorn main:app --reload
# ============================================================================