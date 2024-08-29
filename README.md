# App Store Scraper

This project scrapes the Apple App Store for the top 100 free and paid apps across different regions.

## Setup

1. Ensure you have Python 3.8 or higher installed.

2. Install pipenv if you haven't already:
   ````
   pip install pipenv
   ```

3. Clone this repository:
   ````
   git clone https://github.com/yourusername/app-store-scraper.git
   cd app-store-scraper
   ```

4. Install the required dependencies:
   ````
   pipenv install
   ```

## Usage

1. Activate the virtual environment:
   ````
   pipenv shell
   ```

2. Run the scraper:
   ````
   python app_store_scraper.py
   ```

3. The script will create CSV files for each region and app type (free/paid) in the current directory.

## Customization

- To modify the regions being scraped, edit the `regions` list in the `main()` function of `app_store_scraper.py`.
- To change the number of apps scraped, modify the condition `if len(apps) >= 100:` in the `scrape_app_store()` function.

## Note

Web scraping may be against the terms of service of some websites. Make sure you're allowed to scrape the Apple App Store before using this script. Be respectful of the server by not making too many requests in a short time.

## License

This project is open source and available under the [MIT License](LICENSE).