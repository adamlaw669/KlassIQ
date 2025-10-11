import requests
from bs4 import BeautifulSoup
import re

url = "https://nerdc.gov.ng/content_manager/primary/pri1-3_basic_science_intro.pdf"
response = requests.get(url)

with open("basic_science_intro.pdf", "wb") as f:
    f.write(response.content)