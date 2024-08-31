import requests
from bs4 import BeautifulSoup
import csv
import time
import os
import logging

logging.basicConfig(level=logging.INFO)

def scrape_app_store(region, app_type):
    url = f"https://apps.apple.com/{region}/charts/iphone/{app_type}-apps"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    logging.info(f"Response status code: {response.status_code}")
    soup = BeautifulSoup(response.content, 'html.parser')

    apps = []
    app_items = soup.find_all('div', class_='we-product-collection__item')
    logging.info(f"Found {len(app_items)} app items")

    for app in app_items:
        try:
            name = app.find('h3', class_='we-product-collection__item__product-name').text.strip()
            category = app.find('p', class_='we-product-collection__item__product-category').text.strip()

            # Get app details page
            app_url = app.find('a', class_='we-product-collection__item__link')['href']
            app_response = requests.get(f"https://apps.apple.com{app_url}", headers=headers)
            app_soup = BeautifulSoup(app_response.content, 'html.parser')

            description = app_soup.find('div', class_='we-truncate product-hero__subtitle').text.strip()
            rating = app_soup.find('span', class_='we-customer-ratings__averages__display').text.strip()
            reviews = app_soup.find('div', class_='we-customer-ratings__count').text.strip().split()[0]
            price = app_soup.find('li', class_='inline-list__item inline-list__item--bulleted app-header__list__item--price').text.strip()

            apps.append({
                'Name': name,
                'Category': category,
                'Subcategory': '',
                'Description': description,
                'Rating': rating,
                'Reviews': reviews,
                'Price': price
            })
            logging.info(f"Scraped app: {name}")
        except Exception as e:
            logging.error(f"Error scraping app: {str(e)}")

        if len(apps) >= 100:
            break

        time.sleep(1)

    logging.info(f"Total apps scraped: {len(apps)}")
    return apps

def save_to_csv(apps, filename):
    os.makedirs('results', exist_ok=True)
    filepath = os.path.join('results', filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Name', 'Category', 'Subcategory', 'Description', 'Rating', 'Reviews', 'Price']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for app in apps:
            writer.writerow(app)

def main():
    regions = ['us', 'gb', 'jp', 'kr', 'cn', 'de', 'fr', 'es', 'it', 'ru']  # Add more regions as needed
    app_types = ['free', 'paid']

    for region in regions:
        for app_type in app_types:
            print(f"Scraping {app_type} apps for region: {region}")
            apps = scrape_app_store(region, app_type)
            save_to_csv(apps, f"{region}_{app_type}_apps.csv")
            print(f"Saved {len(apps)} apps to {region}_{app_type}_apps.csv")

if __name__ == "__main__":
    main()