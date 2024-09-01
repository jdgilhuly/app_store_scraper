import os
import csv
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from openai import OpenAI, RateLimitError
import asyncio
import aiohttp

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the OpenAI client
client = OpenAI(api_key='')

def setup_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=chrome_options)

async def generate_app_descriptions(apps):
    async def generate_single_description(app):
        max_retries = 5
        base_delay = 1
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {client.api_key}"},
                        json={
                            "model": "gpt-3.5-turbo",
                            "messages": [
                                {"role": "system", "content": "You are a helpful assistant that generates brief app descriptions."},
                                {"role": "user", "content": f"Generate a brief description for an app named '{app['Name']}'."}
                            ]
                        }
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            app['Description'] = data['choices'][0]['message']['content'].strip()
                            return
                        elif response.status == 429:
                            raise RateLimitError("Rate limit exceeded")
            except RateLimitError:
                if attempt == max_retries - 1:
                    app['Description'] = "Failed to generate description due to rate limiting."
                    return
                delay = base_delay * (2 ** attempt)
                logging.warning(f"Rate limit hit for {app['Name']}. Retrying in {delay} seconds.")
                await asyncio.sleep(delay)

    tasks = [asyncio.create_task(generate_single_description(app)) for app in apps]
    await asyncio.gather(*tasks)

def scrape_app_store(driver, region):
    url = f"https://apps.apple.com/{region}/charts/iphone"
    driver.get(url)
    logging.info(f"Navigated to {url}")

    apps = []
    for app_type in ['free', 'paid']:
        logging.info(f"Starting to scrape {app_type} apps")
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

        driver.execute_script("arguments[0].scrollIntoView();", section)
        time.sleep(2)
        logging.info("Scrolled section into view")

        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        app_items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.l-column"))
        )
        logging.info(f"Found {len(app_items)} {app_type} app items")

        for index, app in enumerate(app_items[:100], start=1):
            try:
                name_element = WebDriverWait(app, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.we-lockup__title"))
                )
                name = name_element.text.strip()
                logging.info(f"Extracted app name: {name}")

                app_link = app.find_element(By.CSS_SELECTOR, "a.we-lockup").get_attribute('href')
                logging.info(f"Opening app details page: {app_link}")

                driver.execute_script(f"window.open('{app_link}', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'section__description'))
                )

                # Extract rating
                rating_element = driver.find_element(By.CSS_SELECTOR, 'span.we-customer-ratings__averages__display')
                rating = rating_element.text.strip()
                logging.info(f"Extracted rating: {rating}")

                # Extract reviews count
                reviews_element = driver.find_element(By.CSS_SELECTOR, 'div.we-customer-ratings__count')
                reviews = reviews_element.text.strip().split()[0]
                logging.info(f"Extracted reviews count: {reviews}")

                # Extract price
                price_element = driver.find_element(By.CSS_SELECTOR, 'li.inline-list__item--bulleted.app-header__list__item--price')
                price = price_element.text.strip()
                logging.info(f"Extracted price: {price}")

                # Extract category
                category_element = driver.find_element(By.CSS_SELECTOR, 'li.inline-list__item.app-header__list__item--genre')
                category = category_element.text.strip()
                logging.info(f"Extracted category: {category}")

                apps.append({
                    'Name': name,
                    'Category': category,
                    'Rating': rating,
                    'Reviews': reviews,
                    'Price': price,
                    'Type': app_type
                })
                logging.info(f"Successfully scraped {app_type} app: {name}")

                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                driver.get(url)
                time.sleep(2)

            except (TimeoutException, NoSuchElementException) as e:
                logging.error(f"Error scraping app {index} of {app_type} apps: {str(e)}")
                logging.error(f"Current URL: {driver.current_url}")
                logging.error(f"Page source: {driver.page_source[:500]}...")
                continue

    # Generate descriptions for all apps at once
    asyncio.run(generate_app_descriptions(apps))

    logging.info(f"Total apps scraped: {len(apps)}")
    return apps

def save_to_csv(apps, region):
    current_date = datetime.now().strftime("%Y%m%d")
    filename = f"{region}_apps_{current_date}.csv"
    os.makedirs('results', exist_ok=True)
    filepath = os.path.join('results', filename)

    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Name', 'Category', 'Description', 'Rating', 'Reviews', 'Price', 'Type']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for app in apps:
            writer.writerow(app)

    logging.info(f"Saved {len(apps)} apps to {filename}")

def main():
    regions = ['us']  # For testing, we'll just use the US region
    driver = setup_driver()

    try:
        for region in regions:
            print(f"Scraping apps for region: {region}")
            apps = scrape_app_store(driver, region)
            save_to_csv(apps, region)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()