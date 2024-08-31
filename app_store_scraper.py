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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
        # Find the correct section using the href attribute
        href_pattern = f"/charts/iphone/top-{app_type}-apps/"
        try:
            section_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//a[contains(@href, '{href_pattern}')]"))
            )
            section = section_link.find_element(By.XPATH, "./ancestor::section")
            logging.info(f"Found {app_type} apps section")
        except TimeoutException:
            logging.error(f"Timeout waiting for {app_type} apps section")
            continue

        # Scroll the section into view
        driver.execute_script("arguments[0].scrollIntoView();", section)
        time.sleep(2)  # Wait for any dynamic content to load

        # Find all app items within the section
        app_items = section.find_elements(By.CSS_SELECTOR, "li.l-column")
        logging.info(f"Found {len(app_items)} {app_type} app items")

        for app in app_items[:100]:  # Limit to 100 apps per type
            try:
                name = app.find_element(By.CSS_SELECTOR, "div.we-lockup__title").text.strip()
                developer = app.find_element(By.CSS_SELECTOR, "div.we-lockup__subtitle").text.strip()

                # Click on the app to open its details
                app_link = app.find_element(By.CSS_SELECTOR, "a.we-lockup").get_attribute('href')
                driver.execute_script(f"window.open('{app_link}', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])

                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'product-hero__subtitle')))

                description = driver.find_element(By.CSS_SELECTOR, 'div.we-truncate.product-hero__subtitle').text.strip()
                rating = driver.find_element(By.CSS_SELECTOR, 'span.we-customer-ratings__averages__display').text.strip()
                reviews = driver.find_element(By.CSS_SELECTOR, 'div.we-customer-ratings__count').text.strip().split()[0]
                price = driver.find_element(By.CSS_SELECTOR, 'li.inline-list__item--bulleted.app-header__list__item--price').text.strip()
                category = driver.find_element(By.CSS_SELECTOR, 'li.inline-list__item.app-header__list__item--genre').text.strip()

                apps.append({
                    'Name': name,
                    'Category': category,
                    'Subcategory': '',
                    'Description': description,
                    'Rating': rating,
                    'Reviews': reviews,
                    'Price': price,
                    'Type': app_type,
                    'Developer': developer
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
        fieldnames = ['Name', 'Category', 'Subcategory', 'Description', 'Rating', 'Reviews', 'Price', 'Type', 'Developer']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for app in apps:
            writer.writerow(app)

def main():
    regions = ['us']  # For testing, we'll just use the US region
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