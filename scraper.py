from io import BytesIO
from re import sub
from ssl import OPENSSL_VERSION_NUMBER
from typing import KeysView, List
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from urllib.parse import urlparse
import numpy as np
import cv2
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from constants import *
import random
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import *
import requests
from PIL import Image
from langdetect import detect


class Scraper:
    def __init__(self):
        self.driver = None
        self.load_driver()

    def load_driver(self):
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )


class Result:
    def __init__(self, url: str, note: str = "", isPass: bool = True):
        self.note = note
        self.isPass = isPass
        self.url = url

    def __str__(self):
        return f"{self.url}: \n{'Pass' if self.isPass else 'Fail'}: {self.note}"


class Tester:
    def __init__(self, url, driver: webdriver.Chrome):
        self.url = url
        self.result = Result(url)
        self.driver = driver
        self.wait = WebDriverWait(self.driver, WAIT_TIME)

    def fetch_url(self, url):
        self.driver.get(url)

    def scroll_down_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def switch_to_main_window(self):
        self.driver.switch_to.window(self.driver.window_handles[0])

    def wait_until_page_fully_loaded(self):
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )

    def get_all_inner_pages(self):
        links = []
        for element in self.driver.find_elements_by_xpath("//a[@href]"):
            if element.is_displayed():
                link = element.get_attribute("href")
                parsed_url = urlparse(self.driver.current_url)
                base_url = parsed_url.scheme + "://" + parsed_url.netloc
                if (
                    link is not None
                    and len(link) > 0
                    and link not in links
                    and base_url in link
                ):
                    links.append(link)
        return links

    def are_inner_pages_translated(self):
        links = self.get_all_inner_pages()
        if len(links) > 5:
            links = random.sample(self.get_all_inner_pages(), 5)
        self.open_link_in_new_tab(links[0])
        for link in links[1:]:
            self.fetch_url(link)
            if not self.is_current_page_translated():
                self.result.note += ", inner pages not translated"
                self.result.isPass = False
                print("This inner page is not translated:" + self.driver.current_url)
                self.close_current_tab_and_switch_to_first_tab()
                return False
        self.close_current_tab_and_switch_to_first_tab()
        self.result.note += ", inner pages are translated"
        return True

    def close_current_tab_and_switch_to_first_tab(self):
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def is_current_page_translated(self):
        text = self.wait.until(
            EC.presence_of_element_located(
                (
                    By.TAG_NAME,
                    "body",
                )
            )
        ).text
        return detect(text) == "hi"

    def open_link_in_new_tab(self, link):
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(link)

    def is_right_page(self):
        # doc: don't wait unnecessarily if the page is wrong. Wait until page's fully loaded then check if elemnt exists
        self.wait_until_page_fully_loaded()
        try:
            self.driver.find_element(
                By.XPATH,
                CLASS_CENTRAL_XPATH,
            )
            self.result.note += "Right Website"
            return True
        except NoSuchElementException:
            self.result.note += "Wrong website"
            self.result.isPass = False
            return False

    def are_images_high_quality(self):
        img_elements = self.wait.until(
            EC.visibility_of_all_elements_located(
                (
                    By.XPATH,
                    "//*[@class='width-100 border-box padding-small large-up-width-1-2 border-box']",
                )
            )
        )
        valid_img_elements = img_elements
        for img_element in valid_img_elements:
            screenshot = img_element.screenshot_as_png
            img = Image.open(BytesIO(screenshot))
            # img.show()
            if self.is_image_blurry(img):
                self.result.note += ", images not high resolution"
                self.result.isPass = False
                return False
        self.result.note += ", images have a high resolution"
        return True

    def has_image(self, image_url):
        try:
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            img.save("img1.png", "PNG")
            img.format
            return img
        except:
            return None

    def is_image_blurry(self, img):
        rgba_image = img.convert("RGBA")
        gray_image = rgba_image.convert("L")
        gray_array = np.array(gray_image)
        laplacian = cv2.Laplacian(gray_array, cv2.CV_64F)

        variance = np.var(laplacian)
        threshold = 100
        if variance < threshold:
            return True
        else:
            return False
