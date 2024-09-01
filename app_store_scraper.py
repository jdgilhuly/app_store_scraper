import time
import os
import csv
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import openai

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up OpenAI API key
openai.api_key = 'your-api-key-here'

def setup_driver():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)

def summarize_description(description):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes app descriptions."},
                {"role": "user", "content": f"Summarize this app description in 50 words or less: {description}"}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        logging.error(f"Error summarizing description: {str(e)}")
        return description[:100] + "..."  # Return first 100 characters if summarization fails

def scrape_app_store(driver, region):
    # Construct the URL for the App Store charts page
    url = f"https://apps.apple.com/{region}/charts/iphone"
    driver.get(url)
    logging.info(f"Navigated to {url}")

    apps = []
    # Iterate through free and paid app types
    for app_type in ['free', 'paid']:
        logging.info(f"Starting to scrape {app_type} apps")

        # Construct the href pattern to find the correct section
        href_pattern = f"/charts/iphone/top-{app_type}-apps/"
        try:
            # Wait for and find the section link
            logging.info(f"Searching for section with href pattern: {href_pattern}")
            section_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//a[contains(@href, '{href_pattern}')]"))
            )
            # Find the parent section of the link
            section = section_link.find_element(By.XPATH, "./ancestor::section")
            logging.info(f"Found {app_type} apps section")
        except TimeoutException:
            logging.error(f"Timeout waiting for {app_type} apps section")
            continue

        # Scroll the section into view to ensure it's loaded
        driver.execute_script("arguments[0].scrollIntoView();", section)
        time.sleep(2)  # Wait for any dynamic content to load
        logging.info("Scrolled section into view")

        # Implement infinite scroll to load all apps
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to the bottom of the page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Wait for new content to load
            time.sleep(2)
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # If heights are the same, it means no more new content, so exit the loop
                break
            last_height = new_height

        # Wait for and find all app items within the section
        app_items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.l-column"))
        )
        logging.info(f"Found {len(app_items)} {app_type} app items")

        # Iterate through the first 100 apps (or less if fewer are available)
        for index, app in enumerate(app_items[:100], start=1):
            try:
                # Wait for the app name to be visible and extract it
                name_element = WebDriverWait(app, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.we-lockup__title"))
                )
                name = name_element.text.strip()
                logging.info(f"Extracted app name: {name}")

                # Get the link to the app's detail page
                app_link = app.find_element(By.CSS_SELECTOR, "a.we-lockup").get_attribute('href')
                logging.info(f"Opening app details page: {app_link}")

                # Open the app's detail page in a new tab
                driver.execute_script(f"window.open('{app_link}', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])

                # Wait for the app details to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'section__description'))
                )

                # Extract description
                description_element = driver.find_element(By.CSS_SELECTOR, 'div.section__description div.we-truncate')
                description = description_element.text.strip()
                summarized_description = summarize_description(description)
                logging.info(f"Summarized description: {summarized_description[:100]}...")

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

                # Add the extracted app information to the apps list
                apps.append({
                    'Name': name,
                    'Category': category,
                    'Description': summarized_description,
                    'Rating': rating,
                    'Reviews': reviews,
                    'Price': price,
                    'Type': app_type
                })
                logging.info(f"Successfully scraped {app_type} app: {name}")

                # Close the app detail tab and switch back to the main page
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

                # Navigate back to the main page to ensure we're in the correct state for the next app
                driver.get(url)
                time.sleep(2)  # Wait for the page to load

            except (TimeoutException, NoSuchElementException) as e:
                # Log any errors encountered while scraping an individual app
                logging.error(f"Error scraping app {index} of {app_type} apps: {str(e)}")
                logging.error(f"Current URL: {driver.current_url}")
                logging.error(f"Page source: {driver.page_source[:500]}...")
                continue  # Skip to the next app if there's an error

    logging.info(f"Total apps scraped: {len(apps)}")
    return apps

def save_to_csv(apps, region):
    # Get the current date in YYYYMMDD format
    current_date = datetime.now().strftime("%Y%m%d")

    # Construct the filename with the region and date
    filename = f"{region}_apps_{current_date}.csv"

    # Create a 'results' directory if it doesn't exist
    os.makedirs('results', exist_ok=True)

    # Construct the full file path
    filepath = os.path.join('results', filename)

    # Write the apps data to the CSV file
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Name', 'Category', 'Description', 'Rating', 'Reviews', 'Price', 'Type']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header row
        writer.writeheader()

        # Write each app's data as a row
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