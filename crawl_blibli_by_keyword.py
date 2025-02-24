import json
import time
import random
import pandas as pd
import urllib.parse
import cloudscraper

KEYWORDS = ['Dettol', 'Durex' , 'Air Wick', 'Vanish', 'Enfagrow', 'Gaviscon']  
MAX_PAGES = 2

class BlibliScraper:
    def __init__(self):
        """Initialize Cloudscraper for Cloudflare bypass."""
        self.scraper = cloudscraper.create_scraper()

    def get_product_list(self, api_url):
        """Fetch product list from the Blibli API using Cloudscraper."""
        try:
            print(f"[INFO] Fetching API: {api_url}")
            time.sleep(2)
            response = self.scraper.get(api_url)

            if response.status_code != 200:
                print(f"[ERROR] API request failed with status code {response.status_code}")
                return []

            json_data = response.json()
            if json_data:
                print("[INFO] Successfully extracted JSON data")
                return json_data.get('data', {}).get('products', [])
            else:
                print("[WARNING] No product data found in JSON response")
                return []

        except Exception as e:
            print(f"[ERROR] Exception while fetching API: {e}")
            return []

def crawl_blibli():
    """Fetch products from Blibli and save to Excel for multiple keywords & pages."""
    start_time = time.time()
    all_data = []  
    for keyword in KEYWORDS:
        encoded_keyword = urllib.parse.quote(keyword.lower())
        print(f"\n[INFO] Scraping keyword: {keyword} (Encoded: {encoded_keyword})")

        scraper = BlibliScraper() 

        for page in range(1, MAX_PAGES + 1):
            print(f"[INFO] Scraping Page {page} for {keyword}")

            api_url = f"https://www.blibli.com/backend/search/products?searchTerm={encoded_keyword}&page={page}"
            
            product_list = scraper.get_product_list(api_url)
            if not product_list:
                print(f"[WARNING] No products found for {keyword} on Page {page}. Skipping...")
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
    total_script_time = round(end_time - start_time,2)
    df = pd.DataFrame(all_data, columns=[
        "web_pid", "pdp_title_value", "price_rp", "price_sp", "pdp_desc_value", "pdp_brand",
        "pdp_rating_value", "pdp_review_count", "pdp_image_url", "pdp_image_count", "osa", "pdp_url"
    ])
    df['total_time_script_run'] = total_script_time
    df.to_excel("crawl_blibli.xlsx", index=False, engine='openpyxl')
    print("[INFO] Data saved to crawl_blibli.xlsx")

crawl_blibli()
