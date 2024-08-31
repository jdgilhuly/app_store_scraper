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
        logging.info(f"Starting to scrape {app_type} apps")
        # Find the correct section using the href attribute
        href_pattern = f"/charts/iphone/top-{app_type}-apps/"
        try:
            logging.info(f"Searching for section with href pattern: {href_pattern}")
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
        logging.info("Scrolled section into view")

        # Find all app items within the section
        app_items = section.find_elements(By.CSS_SELECTOR, "li.l-column")
        logging.info(f"Found {len(app_items)} {app_type} app items")

        for index, app in enumerate(app_items[:2], start=1):  # Limit to 100 apps per type
            logging.info(f"Processing app {index} of {app_type} apps")
            try:
                logging.info("Attempting to extract app name")
                name = app.find_element(By.CSS_SELECTOR, "div.we-lockup__title").text.strip()
                logging.info(f"Extracted app name: {name}")

                logging.info("Attempting to extract developer name")
                developer = app.find_element(By.CSS_SELECTOR, "div.we-lockup__subtitle").text.strip()
                logging.info(f"Extracted developer name: {developer}")

                # Click on the app to open its details
                logging.info("Attempting to get app link")
                app_link = app.find_element(By.CSS_SELECTOR, "a.we-lockup").get_attribute('href')
                logging.info(f"Opening app details page: {app_link}")
                driver.execute_script(f"window.open('{app_link}', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])

                logging.info("Waiting for product description to load")
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'section__description')))

                logging.info("Extracting app details")

                # Extract description
                try:
                    description_element = driver.find_element(By.CSS_SELECTOR, 'div.section__description div.we-truncate')
                    description = description_element.text.strip()
                    logging.info(f"Extracted description: {description[:100]}...")  # Log first 100 characters
                except NoSuchElementException:
                    description = "N/A"
                    logging.warning("Description element not found")

                # Extract rating
                try:
                    rating_element = driver.find_element(By.CSS_SELECTOR, 'span.we-customer-ratings__averages__display')
                    rating = rating_element.text.strip()
                    logging.info(f"Extracted rating: {rating}")
                except NoSuchElementException:
                    rating = "N/A"
                    logging.warning("Rating element not found")

                # Extract reviews count
                try:
                    reviews_element = driver.find_element(By.CSS_SELECTOR, 'div.we-customer-ratings__count')
                    reviews = reviews_element.text.strip().split()[0]
                    logging.info(f"Extracted reviews count: {reviews}")
                except NoSuchElementException:
                    reviews = "N/A"
                    logging.warning("Reviews count element not found")

                # Extract price
                try:
                    price_element = driver.find_element(By.CSS_SELECTOR, 'li.inline-list__item--bulleted.app-header__list__item--price')
                    price = price_element.text.strip()
                    logging.info(f"Extracted price: {price}")
                except NoSuchElementException:
                    price = "N/A"
                    logging.warning("Price element not found")

                # Extract category
                try:
                    category_element = driver.find_element(By.CSS_SELECTOR, 'li.inline-list__item.app-header__list__item--genre')
                    category = category_element.text.strip()
                    logging.info(f"Extracted category: {category}")
                except NoSuchElementException:
                    category = "N/A"
                    logging.warning("Category element not found")

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
                logging.info(f"Successfully scraped {app_type} app: {name}")

                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except Exception as e:
                logging.error(f"Error scraping app {index} of {app_type} apps: {str(e)}")
                logging.error(f"Current URL: {driver.current_url}")
                logging.error(f"Page source: {driver.page_source[:500]}...")  # Log first 500 characters of page source

            if len(apps) >= 100:
                logging.info(f"Reached 100 {app_type} apps, moving to next type")
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