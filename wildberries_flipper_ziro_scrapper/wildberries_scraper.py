import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import random
import urllib.parse
import sys
import os

# Set console encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

class WildberriesScraper:
    def __init__(self):
        self.base_url = "https://www.wildberries.ru"
        self.search_api_url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Origin': 'https://www.wildberries.ru',
            'Referer': 'https://www.wildberries.ru/',
        }

    def search_products(self, query):
        # Encode query parameters
        params = {
            'query': query,
            'resultset': 'catalog',
            'limit': 100,
            'sort': 'popular',
            'page': 1,
            'appType': 1,
            'curr': 'rub',
            'dest': -1,
        }
        
        try:
            print(f"Searching for: {query}")
            url = f"{self.search_api_url}?{urllib.parse.urlencode(params)}"
            print(f"API URL: {url}")
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            print(f"Response status: {response.status_code}")
            
            # Save raw response for debugging
            with open('debug_response.json', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("Saved response to debug_response.json")
            
            data = response.json()
            products = []
            
            if 'data' in data and 'products' in data['data']:
                for item in data['data']['products']:
                    try:
                        product = {
                            'title': item.get('name', ''),
                            'brand': item.get('brand', ''),
                            'price': item.get('salePriceU', 0) / 100 if 'salePriceU' in item else 0,  # Convert kopeks to rubles
                            'original_price': item.get('priceU', 0) / 100 if 'priceU' in item else 0,
                            'rating': item.get('rating', 0),
                            'reviews_count': item.get('feedbacks', 0),
                            'supplier': item.get('supplier', ''),
                            'id': item.get('id', ''),
                            'link': f"https://www.wildberries.ru/catalog/{item.get('id', '')}/detail.aspx",
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # Add image URL if pics field exists
                        if 'pics' in item:
                            basket = str(item.get('basket', 0))
                            vol = str(item.get('vol', 0))
                            product_id = str(item['id'])
                            # Only add image if we have all required fields
                            if basket and vol and product_id:
                                product['image'] = f"https://basket-{basket}.wb.ru/vol{vol}/part{product_id[:5]}/{product_id}/images/big/1.jpg"
                        
                        products.append(product)
                        print(f"Found product: {product['title']} - {product['price']} руб.")
                        
                    except Exception as e:
                        print(f"Error processing product: {str(e)}")
                        continue
                
            return products
            
        except requests.RequestException as e:
            print(f"Error fetching data: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Error response: {e.response.text[:500]}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return []

    def save_to_json(self, products, filename='flipper_zero_products.json'):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=4)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving data: {e}")

    def generate_html(self, products, filename='flipper_zero_results.html'):
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Flipper Zero - Wildberries Results</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{ background-color: #f8f9fa; }}
                .card {{ transition: transform 0.2s; margin-bottom: 20px; }}
                .card:hover {{ transform: translateY(-5px); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                .price {{ font-size: 1.5em; color: #dc3545; }}
                .original-price {{ text-decoration: line-through; color: #6c757d; }}
                .timestamp {{ font-size: 0.8em; color: #6c757d; }}
                .product-link {{ text-decoration: none; color: inherit; }}
                .product-link:hover {{ color: inherit; }}
                .navbar {{ background-color: #563d7c !important; }}
                .search-timestamp {{ font-size: 0.9em; color: #6c757d; text-align: center; margin: 20px 0; }}
                .card-img-top {{ height: 200px; object-fit: contain; padding: 1rem; }}
                .rating-stars {{ color: #ffc107; }}
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark mb-4">
                <div class="container">
                    <a class="navbar-brand" href="#">Wildberries Scraper Results</a>
                    <span class="navbar-text">
                        Found {len(products)} products
                    </span>
                </div>
            </nav>
            <div class="container">
                <div class="search-timestamp">
                    Search performed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                <div class="row">
        """

        # Add product cards
        for product in products:
            # Generate rating stars
            rating = float(product.get('rating', 0))
            rating_stars = '★' * int(rating) + '☆' * (5 - int(rating))
            
            # Generate image tag
            image_tag = '<div class="ratio ratio-4x3 card-img-top bg-light"></div>'
            if 'image' in product:
                image_tag = f'<img src="{product["image"]}" class="card-img-top" alt="{product["title"]}" loading="lazy">'

            # Generate supplier badge
            supplier_badge = ''
            if product.get('supplier'):
                supplier_badge = f'<span class="badge bg-info ms-2">{product["supplier"]}</span>'

            # Generate original price block
            original_price_html = ''
            if product.get('original_price', 0) > product.get('price', 0):
                original_price_html = f'<span class="original-price ms-2">{product["original_price"]:,.0f} ₽</span>'

            html_content += f"""
                <div class="col-md-4 col-sm-6">
                    <a href="{product.get('link', '#')}" class="product-link" target="_blank">
                        <div class="card h-100">
                            {image_tag}
                            <div class="card-body">
                                <h5 class="card-title">{product.get('title', 'Без названия')}</h5>
                                <p class="card-text">
                                    <span class="badge bg-secondary">{product.get('brand', 'Бренд не указан')}</span>
                                    {supplier_badge}
                                </p>
                                <div class="price-block">
                                    <span class="price">{product.get('price', 0):,.0f} ₽</span>
                                    {original_price_html}
                                </div>
                                <div class="rating-block mt-2">
                                    <span class="rating-stars">{rating_stars}</span> 
                                    <small>({product.get('reviews_count', 0)} отзывов)</small>
                                </div>
                            </div>
                        </div>
                    </a>
                </div>
            """

        # Close the HTML
        html_content += """
                </div>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """

        # Save the HTML file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Get the absolute path to the HTML file
        abs_path = os.path.abspath(filename)
        print(f"\nResults page generated: {abs_path}")
        print(f"Open this file in Chrome to view the results: file:///{abs_path}")

def main():
    scraper = WildberriesScraper()
    search_query = "Flipper Zero"
    
    print(f"Searching for {search_query} products...")
    products = scraper.search_products(search_query)
    
    if products:
        print(f"\nFound {len(products)} products")
        scraper.save_to_json(products)
        scraper.generate_html(products)
        
        # Print summary of found products
        print("\nProduct Summary:")
        for product in products:
            print(f"- {product['title']} ({product['brand']}) - {product['price']} руб.")
    else:
        print("No products found")

if __name__ == "__main__":
    main()
