import pandas as pd
import numpy as np
import os
import requests
from bs4 import BeautifulSoup
import re

from datetime import datetime
import time
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning) #filters pandas .append futurewarning messages
from selenium import webdriver


#web-scraping extractor for product data
def selenium_bs4_extractor(terms, web_driver_file_location):
    results_df = pd.DataFrame()
    for term in terms:
        url = f'https://www.intel.com/content/www/us/en/search.html?ws=text#q={term}&sort=%40lastmodifieddt%20descending&f:@tabfilter=[Developers]'
        driver = webdriver.Chrome(web_driver_file_location)
        driver.get(url)
        time.sleep(10)
        X_Path_Show_More = '//*[@id="viewFullDescLink"]'
        elements = driver.find_elements_by_xpath(X_Path_Show_More)
        for element in elements:
            driver.execute_script("arguments[0].click();", element)
        X_Path_Next_Page = '//*[@id="result-section"]/div[9]/ul/li[8]/span'
        time.sleep(5)
        soup=BeautifulSoup(driver.page_source,'html.parser')
        page_counter = 1
        try:
            max_page_count_combined = soup.find('li', {'class': 'coveo-pager-total', 'style':'display: inline-block;'}).text
            max_page_count = int(re.sub('of','', str(max_page_count_combined))) + 1
        except:
            max_page_count = 2 #only one page available to pull from
        #intermediate_terms_df = pd.DataFrame() #creating intermediate df for troubleshooting purposes, optional
        while page_counter < max_page_count:
            time.sleep(5)
            soup=BeautifulSoup(driver.page_source,'html.parser')
            elements = driver.find_elements_by_xpath(X_Path_Show_More)
            try:
                for element in elements:
                    driver.execute_script("arguments[0].click();", element)
                all_results = soup.find_all("div", {"class": "mobviewBtn"})
                for item in all_results:
                    version = item.find("span", {"class": "CoveoFieldValue", "data-field": "@version"})  # version field
                    if version is None:
                        version = item.find("span", {"class": "CoveoFieldValue", "data-field": "@allversions"})
                    else:
                        pass
                    version = version.get_text().strip()
                    # version_number = re.findall('\d+\.\d+', str(version))
                    try:
                        version = re.sub('Version: ', '', str(version))
                    except:
                        pass
                    for id_num in item.find_all("span", {"class": "CoveoFieldValue", "data-field": "@docuniqueid"}): #_id field
                        #print(int(s) for s in item.get_text().strip().split() if s.isdigit())
                        item_adjusted = str(id_num.get_text().strip()).replace(" ", "")
                        lists = re.findall('\d+',item_adjusted)
                        for i in lists:
                            if i == "":
                                del i
                            else:
                                id = i
                    try:
                        description = item.find("span", {"class": "CoveoFieldValue", "data-field": "@description","data-html-value": "true"})
                        description = description.get_text().strip()
                    except:
                        #description = item.find("span", {"class": "viewFullDesc"})
                        description = item.find("span", {"class": "fullDesc"})
                        description.a.clear()
                        description = description.get_text().strip()
                    date_raw = item.find("span", {"class": "CoveoFieldValue", "data-field": "@lastmodifieddt","data-helper": "dateFormat"})
                    #print(item.get_text().strip())
                    # searching string
                    match_str = re.search(r'\d{2}/\d{2}/\d{4}', str(date_raw))
                    # computed date
                    # feeding format
                    date = datetime.strptime(match_str.group(), '%m/%d/%Y').date()
                    name = item.find("a", {"class": "CoveoResultLink"})
                    name = name.get_text().strip()
                    try:
                        web_link = item.find("a", {"aria-label": f"{name}", "data-field": "@secondaryurl"})['href']
                        web_link = str('https://intel.com') + str(web_link)
                    except:
                        web_link = ''
                    multiple_coveos_first = item.find("div", {"class":"coveo-result-cell mobile"})
                    next_siblings = multiple_coveos_first.find_next_siblings("div", {"class":"coveo-result-cell mobile"})
                    file_full = next_siblings[0].text.strip()
                    file_adjusted = re.sub('File: ','',file_full)
                    content_type_full = next_siblings[1].text.strip()
                    content_type_adjusted = re.sub('Content Type: ', '', content_type_full)
                    results_dict = {'search_term': term,
                                    'version': version,
                                    '_id': id,
                                    'description': description,
                                    'date': date,
                                    'file': file_adjusted,
                                    'content_type': content_type_adjusted,
                                    'name': name,
                                    'web_link': web_link
                                    }
                    results_df = results_df.append(results_dict, ignore_index=True)
                    #intermediate_terms_df.append(results_dict, ignore_index=True) #optional, intermediate df for troubleshooting
            except:
                print(f'error on page {page_counter} for term {term} encountered')
                pass
            try:
                driver.find_element_by_xpath(X_Path_Next_Page).click()
            except:
                time.sleep(5)
                try:
                    driver.find_element_by_xpath(X_Path_Next_Page).click()
                except:
                    print(f'page_counter at value of {page_counter} with recorded maximum of {max_page_count}')
            time.sleep(5)
            page_counter += 1
            # print(page_counter)

        #intermediate_terms_df.to_csv(INSERT_PATH_HERE_IF_DESIRED, encoding='utf-8') #for troubleshooting, optional
        driver.close()
    return results_df

if __name__ == "__main__":
    # setting up webdriver for scraping
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    # client terms list to loop through
    terms = ["'black%20list'", 'blacklist', "'white%20list'", 'whitelist', 'master', 'slave'] #terms can either be directly added into a list or put into an outside file to load as an argument for automation
    web_driver_file_location = r'C:\Users\insert_file_path_here_for_web_driver'
    results_df = selenium_bs4_extractor(terms, web_driver_file_location)
    output_file_location = r'C:\Users\insert_file_path_here'
    results_df.to_csv(output_file_location, encoding='utf-8')
