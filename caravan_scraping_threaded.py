# scrap articles from archived issues of Caravan magazine and store them as PDFs
# uses threads to improve performance
# chromedriver.exe should be in the location as this file
# files will be saved to a folder named downloads (create it if it does not exist) in the same location as this file
# a folder will be created under download for each magazine issue and articles from that issue saved in it

import math
from bs4 import BeautifulSoup, SoupStrainer
import requests
import http
from selenium import webdriver
from sb_cookie_utility import load_cookie
import json
import os
import time
import urllib.parse
from queue import Queue
from threading import Thread
import logging
import urllib
from urllib.request import urlopen


# todo redact name from the downloaded files

logging.basicConfig(level=logging.INFO, format='%(thread)d : %(threadName)s : %(levelname)s : %(message)s')
logger = logging.getLogger(__name__)

# https://stackoverflow.com/questions/56897041/how-to-save-opened-page-as-pdf-in-selenium-python
# https://stackoverflow.com/questions/48880646/python-selenium-use-a-browser-that-is-already-open-and-logged-in-with-login-cre
# https://stackoverflow.com/questions/59877561/selenium-common-exceptions-invalidcookiedomainexception-message-invalid-cookie
# https://stackoverflow.com/questions/54578876/selenium-chrome-save-as-pdf-change-download-folder
# https://www.toptal.com/python/beginners-guide-to-concurrency-and-parallelism-in-python

def download_content(issues):
    # scroll this much of the magazine article at a time
    # this is considered as one page
    # this is the optimum value which can be increased if we want faster processing
    scroll_length = 1080
    # base URL to generate the links for each issue
    base_url = 'https://caravanmagazine.in'
    # list to store all links in a magazine issue
    all_links = []

    # get current directory
    path = os.getcwd()

    # setup chrome options to save webpage as PDF
    chrome_options = webdriver.ChromeOptions()
    settings = {
        "recentDestinations": [{
            "id": "Save as PDF",
            "origin": "local",
            "account": "",
        }],
        "selectedDestinationId": "Save as PDF",
        "version": 2
    }

    # loop through issues
    for issue in issues:
        web_page = base_url + '/magazine/' + issue
        logger.info('Current Issue: %s', web_page)
        # determine the download path for file
        download_path = os.path.join(path, 'downloads')

        # create the folder for current issue
        download_dir = os.path.join(download_path, issue.replace('/', '-'))
        logger.info('Files for this issue will be stored under: %s', download_dir)
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        # set chrome preferences
        prefs = {'printing.print_preview_sticky_settings.appState': json.dumps(settings),
                 'savefile.default_directory': download_dir}
        chrome_options.add_experimental_option('prefs', prefs)
        # required to prevent chrome crashing
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--kiosk-printing')
        CHROMEDRIVER_PATH = os.path.join(path, 'chromedriver.exe')
        driver = webdriver.Chrome(options=chrome_options, executable_path=CHROMEDRIVER_PATH)
        driver.set_script_timeout(60)

        # call the same webpage for which the cookie was initialized in sb_initialize_session.py
        # and then load the cookie
        driver.get(base_url)
        load_cookie(driver, os.path.join(path, 'saved_cookie/cookie.txt'))

        # for current issue, get links to all articles
        page = requests.get(web_page)
        data = page.text
        soup = BeautifulSoup(data, features="html.parser")
        # all article links are within div class 'media'
        # if the Caravan page design changes, this might change
        data = soup.findAll('div', attrs={'class': 'media'})

        # clear the list
        del all_links[:]

        for div in data:
            links = div.findAll('a')
            for link in links:
                # encode special characters in URL
                url = base_url + urllib.parse.quote(link.get('href').encode('UTF-8'))
                all_links.append(url)
        logger.info('Articles in this issue:')
        logger.info('--------------------')
        for article in all_links:
            logger.info('%s', article)
        logger.info('--------------------')

        # for each link, convert content into PDF and print to save the file
        for current_link in all_links:
            driver.get(current_link)
            # find length of each article
            lenOfPage = driver.execute_script("return document.body.scrollHeight")
            number_of_scrolls = math.ceil(lenOfPage / scroll_length)
            logger.info('Current Article: %s. Number of pages in the article: %s', current_link, number_of_scrolls)

            # uncomment the below section if you want to skip long articles
            # number of scrolls is equal to number of pages
            #if number_of_scrolls > 2:
            #    continue
                
            # scroll along the article one page at a time to allow images to load
            for i in range(0, number_of_scrolls):
                scroll_to = scroll_length * (i + 1)
                driver.execute_script("window.scrollTo(0, arguments[0])", scroll_to)
                # wait for 2 seconds for images to load, can be reduced to speed up processing
                time.sleep(2)
            # print page as PDF
            driver.execute_script('window.print();')
        driver.quit()
# fetch and process jobs from queue
class downloadworker(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # get the work from the queue and expand the tuple
            issues = self.queue.get()
            try:
                logger.info('Processing this batch: %s', issues)
                download_content(issues)
            finally:
                self.queue.task_done()
                logger.info('%s completed ', self.name)

# chunks a list into n parts
def chunked_list(input_list, n):
    # yield successive chunks from list
    for i in range(0, n):
        yield input_list[i::n]


def main():
    # provide the starting/ending years and months
    # magazine issues within this period will be scraped
    start_year = '2020'
    start_month = '12'

    end_year = '2020'
    end_month = '12'

    # define the number of workers
    number_of_workers = 3

    # lists used to generate a part of the URLs for each issue
    list_months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    issues = []

    # find the index of the start_month in list_months
    start_month_index = list_months.index(start_month)

    # generate the last part of the URL for each archived issue
    # starting from the start_month and ending at end_month
    for year in range(int(start_year), int(end_year) + 1):
        for idx in range(start_month_index, 12):
            month = list_months[idx]
            issue = str(year) + '/' + month
            issues.append(issue)
            # break if this is the enc issue to fetch
            if issue == end_year + '/' + end_month:
                break
        # break if this is the enc issue to fetch
        if issue == end_year + '/' + end_month:
            break
        start_month_index = 0
    logger.info('Magazine issues to be fetched: %s', issues)

    # create a queue to communicate with the worker threads
    queue = Queue()

    # break total magazine issues into separate chunks, each chunk is a task
    # put the tasks into the queue as a tuple
    for i in chunked_list(issues, number_of_workers):
        logger.info('Queueing {}'.format(i))
        queue.put((i))

    # create number_of_workers worker threads
    for x in range(number_of_workers):
        worker = downloadworker(queue)
        # setting daemon to True will let the main thread exit even though the workers are blocking
        worker.daemon = True
        worker.start()
        # causes the main thread to wait for the queue to finish processing all the tasks
    queue.join()

if __name__ == '__main__':
    main()