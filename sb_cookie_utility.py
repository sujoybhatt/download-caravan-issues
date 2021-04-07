import pickle
import os
def save_cookie(driver, path):
    #Delete the cookie if it exists
    try:
        os.remove(path)
        print('Cookie already exists. Deleting it.')
    except OSError:
        pass

    with open(path, 'wb') as filehandler:
        pickle.dump(driver.get_cookies(), filehandler)
        #print('Creating cookie file.')
        print (driver.get_cookies())

def load_cookie(driver, path):
     #print('Loading saved cookie.')
     with open(path, 'rb') as cookiesfile:
         cookies = pickle.load(cookiesfile)
         for cookie in cookies:
             driver.add_cookie(cookie)