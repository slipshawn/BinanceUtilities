# -*- coding: utf-8 -*-
"""
Created on Sat Feb  3 14:31:32 2024

Binance Delisting Checker.

Scrapes the binance new listings anouncements page to get spot & margin trading pairs newly listed.

@author: ander
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
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



def get_all_new_listing_symbols(driver, retries: int=10) -> list:
    hrefs = get_link_hrefs(driver, retries)
    all_new_list_symbols = []
    
    for href in hrefs:
        #print(href)
            
        # Selecting announcements for specific cryptos and avoiding general news and navigation pages.
        if ("/announcement/" in href) and ("navId" not in href):
            driver.get(href)
            driver.implicitly_wait(8)
        
            # 2 formats for spot or future trading pairs.
            if "notice-on-new-trading-pairs" in href:
                # Example text from a new spot pairs listing announcement.
                # text = "Binance will open trading for the BLUR/FDUSD, DYDX/TRY, SUPER/FDUSD, USTC/FDUSD and USTC/TRY spot trading pairs at 2023-11-30 08:00 (UTC)."
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                # Splitting by open trading announcement since random news pair daily % gains will be on page.
                text = page_text.split("Binance will open trading")[-1]
                pattern = re.compile(r'\b[A-Z]{2,5}\/[A-Z]{2,5}\b')
                # Splitting by UTC indicator for times since some symbols the listing type (spot, grid, bots, etc.)
                # are before or after. The UTC listing time should separate them well enough.
                utc_splits = text.split("(UTC).")
                
                for text_split in utc_splits:
                    if "spot trading pairs" in text_split.lower():
                        symbols = pattern.findall(text_split)
                        # Appending symbols with the respective asset type indicator in parentheses.
                        symbols = [x+" (spot)" for x in symbols]
                    
            elif "perpetual-contract" in href:
                # Example text from a new perp futures listing announcement.
                # text = "Binance Futures will launch the USDⓈ-M ZETA Perpetual Contract at 2024-02-02 08:30 (UTC), with up to 50x leverage. "
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                text = page_text.split("Binance Futures will launch")[-1]
                # Assumes search pattern is any symbol combined of uppercase letters.
                pattern = re.compile(r'USDⓈ-M (\w+) Perpetual Contract')
                symbols = pattern.findall(text)
                symbols = [x+" (perp)" for x in symbols]
            
            else:
                # Other announcement types not yet supported.
                continue
                
            all_new_list_symbols.extend(symbols)
            
    # Convert to set back to list so duplicates are removed.
    return list(set(all_new_list_symbols))



if __name__ == "__main__":
    # Storage directory
    directory =  os.environ['BINANCE_NEW_LISTINGS']
    
    # Set the url
    new_listing_url = "https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48"

    # Set up the Chrome WebDriver
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')  # Run in headless mode (no browser UI)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Navigate to the page
    driver.get(new_listing_url)

    # Wait for the page to load, you might need to adjust the time
    driver.implicitly_wait(10)
    retries = 8
    
    # Get all the delisting symbols
    all_new_list_symbols = get_all_new_listing_symbols(driver, retries)
    
    # Write to .txt file in directory with date naming convention
    today = str(datetime.now()).split(" ")[0]
    with open(f"{directory}/new-listings_{today}.txt", "w") as fp:
        for symbol in all_new_list_symbols:
            fp.write(f"{symbol}\n")
    
    # Close the driver
    driver.quit()

