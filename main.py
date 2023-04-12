from scraper import *
from constants import *

scraper = Scraper()
for url in PASS_URLS:
    tester = Tester(url, scraper.driver)
    tester.fetch_url(tester.url)
    if not tester.is_right_page():
        break
    tester.are_images_high_quality()
    tester.are_inner_pages_translated()
    print("\n" + tester.result.__str__())
