import json
import time
import random
import pandas as pd
import urllib.parse
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth

KEYWORDS = ["Dettol", "Durex", "Air Wick", "Vanish", "Enfagrow", "Gaviscon"]
MAX_PAGES = 2

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
]

class BlibliScraper:
    def __init__(self):
        """Initialize SeleniumWire with Undetected ChromeDriver."""
        options = Options()
        options.add_argument("--ignore-certificate-errors")  
        options.add_argument("--ignore-ssl-errors=yes")  
        options.add_argument("--disable-gpu")  
        options.add_argument("--disable-blink-features=AutomationControlled")  # Bypass bot detection
        self.user_agent = random.choice(USER_AGENTS)

        options.add_argument(f"user-agent={self.user_agent}")

        self.driver = uc.Chrome(options=options, use_subprocess=True)
        stealth(
            self.driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win64",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True
        )

        self.cookies = {
            '_cfuvid': '1_h3rZO7Udveks6xmJoG72p9fWG72PmPRVGmqOD6VBw-1739944011237-0.0.1.1-604800000',
            'Blibli-Device-Id': 'U.ba1bf544-1127-453b-8f47-298f0bb4624e',
            'Blibli-User-Id': 'dfe7503e-dba9-46f0-bb48-69883dc2fb02',
            'Blibli-Session-Id': 'a0ce2175-fcc0-4534-b67e-72d6f8708361',
            '_ga': 'GA1.2.1430725636.1739944020',
            'IR_19024': '1739952818902%7C4120732%7C1739952818902%7C%7C',
        }
        


    def get_product_list(self, api_url):
        """Fetch product list from the Blibli API using selenium wire."""
        try:
            self.driver.get(api_url)
            for name, value in self.cookies.items():
                self.driver.add_cookie({'name': name, 'value': value, 'domain': '.blibli.com'})

            WebDriverWait(self.driver, 10).until(
            lambda driver: "application/json" in driver.page_source or "products" in driver.page_source
            )

            raw_response = self.driver.page_source
            json_start = raw_response.find("{") 
            json_end = raw_response.rfind("}")  

            if json_start == -1 or json_end == -1:
                print("[ERROR] No JSON found in page source!")
                return []

            json_text = raw_response[json_start:json_end + 1]  # Extract JSON part

            try:
                json_data = json.loads(json_text)
                if json_data:
                    print("[INFO] Successfully extracted JSON data")
                    return json_data.get('data', {}).get('products', [])
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to parse JSON: {e}")
                print(f"[DEBUG] Raw JSON Response: {json_text}")  # Debugging
                return []

        except Exception as e:
            print(f"[ERROR] WebDriver Exception: {e}")
            return []

    def close_driver(self):
        """Safely close the WebDriver instance."""
        if self.driver:
            try:
                print("[INFO] Closing WebDriver...")
                self.driver.quit()
                self.driver.service.process.wait() 
            except Exception as e:
                print(f"[WARNING] Error while quitting WebDriver: {e}")
            try:
                if hasattr(self.driver, "service") and hasattr(self.driver.service, "process"):
                    self.driver.service.process.kill()
            except Exception as e:
                print(f"[WARNING] Error while force killing WebDriver process: {e}")

            self.driver = None  

def crawl_blibli():
    """Fetch products from Blibli and save to Excel for multiple keywords & pages."""
    start_time = time.time() 
    scraper = BlibliScraper() 
    all_data = [] 

    for keyword in KEYWORDS:
        encoded_keyword = urllib.parse.quote(keyword.lower())
        scraper.close_driver()
        scraper = BlibliScraper() 
        
        for page in range(1, MAX_PAGES + 1):
            print(f"[INFO] Scraping Page {page} for {encoded_keyword}")

            api_url = f"https://www.blibli.com/backend/search/products?searchTerm={encoded_keyword}&page={page}&start=0&merchantSearch=true&multiCategory=true&channelId=mobile-web&showFacet=false&userIdentifier=1739944020.73d98c58-fd7b-4ee1-aab1-1fc58c7f5694&isMobileBCA=false&isOnlyPaginationCall=true&intent=true&isJual=false"
            
            print(f"api_url {api_url}")
            # scraper.driver.delete_all_cookies()
            time.sleep(2)  
            

            product_list = scraper.get_product_list(api_url)

            if not product_list:
                print(f"[WARNING] No products found for {encoded_keyword} on Page {page}. Skipping...")
                break 

            for product_dict in product_list:
                web_pid = product_dict.get('sku', '')
                pdp_title_value = product_dict.get('name', '')
                price_rp = product_dict.get('price', {}).get('strikeThroughPriceDisplay', 0)
                price_sp = product_dict.get('price', {}).get('priceDisplay', 0)
                pdp_desc_value = 0
                pdp_brand = product_dict.get('brand', '')  
                pdp_rating_value = product_dict.get('review', {}).get('rating', 0)
                pdp_review_count = product_dict.get('review', {}).get('count', 0)
                pdp_image_url_list = product_dict.get('images', [])
                pdp_image_url = pdp_image_url_list[0] if pdp_image_url_list else 0
                pdp_image_count = len(pdp_image_url_list)
                pdp_availibility = product_dict.get('status')

                osa = 1 if pdp_availibility == 'AVAILABLE' else 0
                url = product_dict.get('url', '')
                pdp_url = f'https://www.blibli.com{url}' if url else 0  

                all_data.append([ web_pid, pdp_title_value, price_rp, price_sp, pdp_desc_value, pdp_brand,
                                 pdp_rating_value, pdp_review_count, pdp_image_url, pdp_image_count, osa, pdp_url])
                
            time.sleep(random.uniform(3, 6))  

    end_time = time.time()  
    total_execution_time = round(end_time - start_time, 2) 
    df = pd.DataFrame(all_data, columns=[
        "web_pid", "pdp_title_value", "price_rp", "price_sp", "pdp_desc_value", "pdp_brand",
        "pdp_rating_value", "pdp_review_count", "pdp_image_url", "pdp_image_count", "osa", "pdp_url"
    ])
    
    df["execution_time"] = total_execution_time 

    df.to_excel("scral_blibli.xlsx", index=False, engine='openpyxl')
    print("[INFO] Data saved to scral_blibli.xlsx")

    scraper.close_driver()

crawl_blibli()

