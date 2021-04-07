# run this first to open a session and save the cookie
# this is to ensure that the bot does not have to do a login
# once the browser window opens, login to to the site and press enter (one or more times) on the terminal
# you can close the browser window after the script completes
# chromedriver.exe should be in the same location as this file
# a folder named saved_cookie should exist in the same location as this file
# dependent on sb_cookie_utility.py
from selenium import webdriver
from sb_cookie_utility import save_cookie
import os
web_page = 'https://caravanmagazine.in'
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
path = os.getcwd()
CHROMEDRIVER_PATH = os.path.join(path, 'chromedriver.exe')
driver = webdriver.Chrome(options=chrome_options, executable_path=CHROMEDRIVER_PATH)
driver.get(web_page)
print('Press the enter key to continue')
foo = input()
save_cookie(driver, os.path.join(path, 'saved_cookie/cookie.txt'))