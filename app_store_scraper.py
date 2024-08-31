import time
import os
import csv
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)

def scrape_app_store(driver, region):
    url = f"https://apps.apple.com/{region}/charts/iphone"
    driver.get(url)
    logging.info(f"Navigated to {url}")

    apps = []
    for app_type in ['free', 'paid']:
        # Click on the appropriate tab
        tab_selector = f"#charts-{app_type}-tab"
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, tab_selector)))
        driver.find_element(By.CSS_SELECTOR, tab_selector).click()
        logging.info(f"Clicked on {app_type} apps tab")

        # Wait for the content to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".we-product-collection")))

        # Parse the page content
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        app_items = soup.find_all('div', class_='we-product-collection__item')
        logging.info(f"Found {len(app_items)} {app_type} app items")

        for app in app_items[:100]:  # Limit to 100 apps per type
            try:
                name = app.find('h3', class_='we-product-collection__item__product-name').text.strip()
                category = app.find('p', class_='we-product-collection__item__product-category').text.strip()

                # Click on the app to open its details
                app_link = app.find('a', class_='we-product-collection__item__link')['href']
                driver.execute_script(f"window.open('{app_link}', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])

                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'product-hero__subtitle')))
                app_soup = BeautifulSoup(driver.page_source, 'html.parser')

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
                    'Price': price,
                    'Type': app_type
                })
                logging.info(f"Scraped {app_type} app: {name}")

                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except Exception as e:
                logging.error(f"Error scraping app: {str(e)}")

            if len(apps) >= 100:
                break

    logging.info(f"Total apps scraped: {len(apps)}")
    return apps

def save_to_csv(apps, filename):
    os.makedirs('results', exist_ok=True)
    filepath = os.path.join('results', filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Name', 'Category', 'Subcategory', 'Description', 'Rating', 'Reviews', 'Price', 'Type']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for app in apps:
            writer.writerow(app)

def main():
    regions = ['us', 'gb', 'jp', 'kr', 'cn', 'de', 'fr', 'es', 'it', 'ru']
    driver = setup_driver()

    try:
        for region in regions:
            print(f"Scraping apps for region: {region}")
            apps = scrape_app_store(driver, region)
            save_to_csv(apps, f"{region}_apps.csv")
            print(f"Saved {len(apps)} apps to {region}_apps.csv")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()