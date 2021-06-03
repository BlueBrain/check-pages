import time
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)

# Load the URL
driver.get("https://www.google.com")

time.sleep(10)


for request in driver.requests:
    if request.response:
    	print(request.url)
driver.quit()
