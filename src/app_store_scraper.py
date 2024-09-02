import time
import csv
import os
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import logging
from regions import REGIONS

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver():
    """Set up and return a Chrome WebDriver instance."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    return webdriver.Chrome(options=options)

def ensure_directory(directory):
    """Create the directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_results_directory():
    """Get the results directory name with current date."""
    today = date.today().strftime("%Y%m%d")
    return f"results_{today}"

def scrape_app_store(driver, region):
    """
    Scrape app data from the App Store for a given region.

    Args:
    driver (WebDriver): Selenium WebDriver instance.
    region (str): Region code to scrape.

    Returns:
    tuple: List of app data for each section and list of section names.
    """
    url = f"https://apps.apple.com/{region}/charts/iphone"
    driver.get(url)
    logger.info(f"Navigated to {url}")

    time.sleep(5)  # Wait for page to load

    links = driver.find_elements(By.XPATH, "//a[contains(@class, 'section__headline-link')]")

    sections = [
        ("free_apps", 'free', links[0]),
        ("paid_apps", 'paid', links[1]),
        ("free_games", 'free', links[2]),
        ("paid_games", 'paid', links[3]),
    ]


    for category, type, selector in sections:
        try:
            apps = []
            selector.click()
            logger.info(f"Clicked on {category} link")

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

            save_to_csv(apps, region, category)
            driver.back()
            time.sleep(5)

        except NoSuchElementException:
            logger.error(f"Could not find {name} link")
            break



def save_to_csv(apps, region, type):
    results_dir = get_results_directory()
    region_dir = os.path.join(results_dir, region)
    ensure_directory(region_dir)
    filename = os.path.join(region_dir, f"app_store_top_100_{type}.csv")
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['name', 'type', 'rank'])
        writer.writeheader()
        writer.writerows(apps)
    logger.info(f"Saved data to {filename}")



def main():
    """Main function to run the App Store scraper."""

    driver = setup_driver()

    try:
        for region in REGIONS:
            logger.info(f"Scraping apps for region: {region}")
            scrape_app_store(driver, region)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()