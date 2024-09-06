# App Store Scraper

This project scrapes the Apple App Store for the top 100 free and paid apps and games across different regions.

## Setup

1. Ensure you have Python 3.8 or higher installed.

2. Install pipenv if you haven't already:
   ```shell
   pip install pipenv
   ```

3. Clone this repository:
   ```shell
   git clone https://github.com/yourusername/app-store-scraper.git
   cd app-store-scraper
   ```

4. Install the required dependencies:
   ```shell
   pipenv install
   ```

## Usage

1. Activate the virtual environment:
   ```shell
   pipenv shell
   ```

2. Run the scraper:
   ```shell
   python src/app_store_scraper.py
   ```

3. The script will create CSV files for each region and app category in a date-stamped results directory.

## What app_store_scraper.py Does

The `app_store_scraper.py` script performs the following tasks:

1. It defines a list of regions to scrape (e.g., US, GB, JP, KR, CN, etc.).
2. The script uses Selenium WebDriver to navigate and extract information from the App Store pages.
3. For each region, it scrapes four categories: free apps, paid apps, free games, and paid games.
4. For each app, it collects data such as:
   - App name
   - App type (free/paid)
   - Rank
5. The script continues scraping until it has collected data for the top 100 apps in each category for each region.
6. As it scrapes, it saves the data to CSV files, creating separate files for each region and category (e.g., results_20230515/us/app_store_top_100_free_apps.csv).
7. The script includes error handling and logging to track the scraping process and handle potential issues.

## Customization

- To modify the regions being scraped, edit the `regions` list in the `main()` function of `app_store_scraper.py`.
- To change the number of apps scraped, modify the slice `app_items[:100]` in the `scrape_app_store()` function.

## Note

Web scraping may be against the terms of service of some websites. Make sure you're allowed to scrape the Apple App Store before using this script. Be respectful of the server by not making too many requests in a short time.

## License

This project is open source and available under the [MIT License](LICENSE).