from scraper import *
from constants import *
from base_scraping import BaseScraping

tester = Tester()
for url in PASS_URLS:
    tester.url = url
    tester.fetch_url(tester.url)
    if not tester.is_right_page():
        break
    tester.are_images_high_quality()
    tester.are_inner_pages_translated_to_hindi()
    print("\n" + tester.result.__str__())
