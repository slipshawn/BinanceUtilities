from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
import re
from datetime import datetime


def get_link_hrefs(driver, retries: int=10) -> list:
    for _ in range(retries):
        try:
            # Attempt to find all <a> elements on the page and extract hrefs
            links = driver.find_elements(By.TAG_NAME, 'a')
            hrefs = [link.get_attribute('href') for link in links if link.get_attribute('href')]
        except StaleElementReferenceException:
            # Wait a bit for the page to stabilize
            time.sleep(1)
            continue  # Try finding the elements again
    return hrefs


def get_all_delisting_symbols(driver, retries: int=10) -> list:
    hrefs = get_link_hrefs(driver, retries)
    all_delist_symbols = []
    
    for href in hrefs:
        #print(href)
            
        # Check if it contains "notice-of-removal" exact string since those contain the pairs being delisted
        # in an easy to scrape format.
        # Other links have weird explanations and formatting and pairs are not uniformly described by symbol.
        if "notice-of-removal" in href:
            driver.get(href)
            driver.implicitly_wait(8)
            
            # Two different listing formats if removing spot or margin pairs.
            if "spot-trading" in href:
                # Example of line from spot trading announcement.
                #text = "At 2023-12-29 02:00 (UTC): APE/BNB, APE/EUR, ARPA/ETH, BETA/ETH, CVX/BTC, ENS/BNB, EOS/EUR, ETC/EUR, KAVA/BNB, PAXG/BNB"
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                # Splitting page by indicator of when delisted pairs are named so that it doesnt get random sponsored/news
                # pairs at top of page.
                text = page_text.split("cease trading on the following spot trading pairs:")[-1]
                # Compile the regex pattern and find all matches in the text
                pattern = re.compile(r'\b[A-Z]{2,5}\/[A-Z]{2,5}\b')
                symbols = pattern.findall(text)
                # Appending symbols with the respective asset type indicator in parentheses.
                symbols = [x+" (spot)" for x in symbols]
            
            if "margin-trading" in href:
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                text = page_text.split("Binance Margin will delist the ")[-1]
                pattern = re.compile(r'\b[A-Z]{2,5}\/[A-Z]{2,5}\b')
                symbols = pattern.findall(text)
                symbols = [x+" (margin)" for x in symbols]
            
            all_delist_symbols.extend(symbols)
    
    return all_delist_symbols


if __name__ == "__main__":
    # Storage directory
    directory = os.environ['BINANCE_DELISTINGS']
    
    # Set the url
    delisting_url = "https://www.binance.com/en/support/announcement/delisting?c=161&navId=161"

    # Set up the Chrome WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode (no browser UI)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Navigate to the page
    driver.get(delisting_url)

    # Wait for the page to load, you might need to adjust the time
    driver.implicitly_wait(10)
    retries = 8
    
    # Get all the delisting symbols
    all_delist_symbols = get_all_delisting_symbols(driver, retries)
    
    # Write to .txt file in directory with date naming convention
    today = str(datetime.now()).split(" ")[0]
    with open(f"{directory}/Delistings_{today}.txt", "w") as fp:
        for symbol in all_delist_symbols:
            fp.write(f"{symbol}\n")
    
    # Close the driver
    driver.quit()
