import requests
from bs4 import BeautifulSoup
import csv
import time

def scrape_app_store(region, app_type):
    url = f"https://apps.apple.com/{region}/charts/iphone/{app_type}-apps"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    apps = []
    for app in soup.find_all('div', class_='we-product-collection__item'):
        name = app.find('h3', class_='we-product-collection__item__product-name').text.strip()
        category = app.find('p', class_='we-product-collection__item__product-category').text.strip()
        
        # Get app details page
        app_url = app.find('a', class_='we-product-collection__item__link')['href']
        app_response = requests.get(f"https://apps.apple.com{app_url}")
        app_soup = BeautifulSoup(app_response.content, 'html.parser')
        
        description = app_soup.find('div', class_='we-truncate product-hero__subtitle').text.strip()
        rating = app_soup.find('span', class_='we-customer-ratings__averages__display').text.strip()
        reviews = app_soup.find('div', class_='we-customer-ratings__count').text.strip().split()[0]
        price = app_soup.find('li', class_='inline-list__item inline-list__item--bulleted app-header__list__item--price').text.strip()
        
        apps.append({
            'Name': name,
            'Category': category,
            'Subcategory': '',  # Subcategory is not easily available on the main page
            'Description': description,
            'Rating': rating,
            'Reviews': reviews,
            'Price': price
        })
        
        if len(apps) >= 100:
            break
        
        time.sleep(1)  # To avoid overwhelming the server
    
    return apps

def save_to_csv(apps, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
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