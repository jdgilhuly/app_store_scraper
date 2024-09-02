import time
import csv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, TimeoutException
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    return webdriver.Chrome(options=options)

def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def scrape_app_store(driver, region):
    url = f"https://apps.apple.com/{region}/charts/iphone"
    driver.get(url)
    logger.info(f"Navigated to {url}")



    # Wait for 5 seconds
    time.sleep(5)

    links = driver.find_elements(By.XPATH, "//a[contains(@class, 'section__headline-link')]")

    sections = [
        ("Top Free Apps", 'free', links[0]),
        ("Top Paid Apps", 'paid', links[1]),
        ("Top Free Games", 'free', links[2]),
        ("Top Paid Games", 'paid', links[3]),
    ]


    for name, type, selector in sections:
        try:
            apps = []
            selector.click()
            logger.info(f"Clicked on {name} link")

            app_items = driver.find_elements(By.CSS_SELECTOR, ".we-lockup")
            logger.info(f"Found {len(app_items)} app items")

            for app in app_items[:100]:
                try:
                    rank = app.find_element(By.CSS_SELECTOR, ".we-lockup__rank").text
                    name = app.find_element(By.CSS_SELECTOR, ".we-lockup__title .we-clamp").text
                    apps.append({'name': name, 'type': type, 'rank': int(rank)})
                    logger.info(f"Scraped app: {name} - Rank: {rank} - Type: {type}")
                except NoSuchElementException:
                    logger.warning(f"Failed to scrape an app")
                except ValueError:
                    logger.warning(f"Failed to parse rank for app: {name}")

            save_to_csv(apps, region, type)
            driver.back()
            time.sleep(5)

        except NoSuchElementException:
            logger.error(f"Could not find {name} link")
            break



def save_to_csv(apps, region, type):
    ensure_directory("results")
    filename = f"results/app_store_top_100_{region}_{type}.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['name', 'type', 'rank'])
        writer.writeheader()
        writer.writerows(apps)
    logger.info(f"Saved data to {filename}")

def main():
    regions = ['us', 'gb', 'jp', 'kr', 'cn', 'hk', 'tw', 'th', 'sg', 'my', 'ph', 'id', 'in', 'ru']  # Add more regions as needed
    driver = setup_driver()

    try:
        for region in regions:
            logger.info(f"Scraping apps for region: {region}")
            apps = scrape_app_store(driver, region)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()