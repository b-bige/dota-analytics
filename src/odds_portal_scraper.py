import httpx
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
import pandas as pd
import numpy as np
import time
import random

import logging
from basic_logger import setup_logger
setup_logger('logs/oddsportal_scraper.log')

def main():
    driver = webdriver.Firefox()
    base = 'https://www.oddsportal.com'
    driver.get(f'{base}/results/#esports')
    wait = WebDriverWait(driver, timeout=5)
    wait.until(EC.element_to_be_clickable((By.TAG_NAME, 'ul')))
    count = wait_for_stable_count(driver, '[data-testid="results-country-tournament-section"]', interval=1)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    wait = WebDriverWait(driver, timeout=10)
    match_data = []
    dota_tourneys = soup.find_all('ul', attrs={'data-testid': 'results-country-tournament-section'})[1]
    original_window = driver.current_window_handle
    for idx, a in enumerate(dota_tourneys.find_all('a')):
        href = a.get('href')
        time.sleep(random.randint(1, 3))
        driver.get(f'{base}{href}')
        # year_selector = '.flex.flex-wrap.gap-2.py-3.text-xs.max-mm\\:flex-nowrap.max-mm\\:overflow-x-auto.max-mm\\:overflow-hidden.max-md\\:mx-3.max-sm\\:!hidden.no-scrollbar'
        # wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, year_selector)))
        tourney_soup = BeautifulSoup(driver.page_source, 'html.parser')
        years = tourney_soup.find(
            'div', 
            class_='flex flex-wrap gap-2 py-3 text-xs max-mm:flex-nowrap max-mm:overflow-x-auto max-mm:overflow-hidden max-md:mx-3 max-sm:!hidden no-scrollbar'
        ).find_all('a')
        for year in years:
            year_href = year.get('href')
            if year_href != driver.current_url:
                time.sleep(random.randint(1, 2))
                driver.get(year_href)
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                count = wait_for_stable_count(driver, '.eventRow.flex.w-full.flex-col.text-xs', interval=2.5)
            except TimeoutException:
                logging.info(f'Finished with {href}')
                continue
            time.sleep(1)
            try:
                pagination = driver.find_element(By.CSS_SELECTOR, '.pagination.my-7.flex.items-center.justify-center')
            except:
                pass
            while True:
                year_soup = BeautifulSoup(driver.page_source, 'html.parser')
                match_divs = year_soup.find_all('div', class_='eventRow flex w-full flex-col text-xs')
                for match_div in match_divs:
                    odds_data = {}
                    date = match_div.find('div', class_='flex w-full min-w-0 border-l border-r border-black-borders bg-gray-light')
                    if date:
                        current_date = date.find('div').get_text()
                    data = match_div.find('div', class_='border-black-borders border-b border-l border-r hover:bg-[#f9e9cc]').find_all('p')
                    odds_data['date'] = current_date
                    odds_data['time'] = data[0].get_text()
                    odds_data['home_team'] = data[1].get_text()
                    odds_data['away_team'] = data[2].get_text()
                    home_odds = data[3].get_text()
                    away_odds = data[4].get_text()
                    if home_odds == '-' or away_odds == '-':
                        match_a = match_div.find('a', class_='next-m:flex next-m:!mt-0 ml-2 min-h-[32px] w-full hover:cursor-pointer')
                        match_href = match_a.get('href')
                        driver.switch_to.new_window('tab')
                        driver.get(f'{base}{match_href}')
                        count = wait_for_stable_count(driver, 'div.flex.flex-col[data-v-925bcd68]', interval=1.5)
                        match_soup = BeautifulSoup(driver.page_source, 'html.parser')
                        bookmaker_row = match_soup.find('div', attrs={'data-testid': 'over-under-expanded-row'})
                        odds = bookmaker_row.find_all('p', class_='odds-text line-through')
                        home_odds = odds[0].get_text()
                        away_odds = odds[1].get_text()
                        time.sleep(random.randint(1, 3))
                        driver.close()
                        driver.switch_to.window(original_window)
                    odds_data['home_odds'] = home_odds
                    odds_data['away_odds'] = away_odds
                    match_data.append(odds_data)
                try:
                    driver.execute_script("arguments[0].scrollIntoView();", pagination)
                    pagination.find_element(By.XPATH, '//a[text()="Next"]').click()
                    count = wait_for_stable_count(driver, '.eventRow.flex.w-full.flex-col.text-xs', interval=1.5)
                except Exception as e:
                    print(f'Error with pagination: {e}')
                    ##Cannot find next page button - pages finished
                    break
        if idx == 1:
            print(pd.DataFrame(match_data))
            break
    pd.DataFrame(match_data).to_csv('data/historical_odds.csv')


def wait_for_stable_count(driver, css_selector, timeout=10, interval=0.5):
    """Wait until element count stops changing."""
    deadline = time.time() + timeout
    prev_count = 0
    while time.time() < deadline:
        current_count = len(driver.find_elements(By.CSS_SELECTOR, css_selector))
        if current_count == prev_count and current_count > 0:
            return current_count
        prev_count = current_count
        time.sleep(interval)
    return prev_count

if __name__ == '__main__':
    main()