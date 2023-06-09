from io import BytesIO
from selenium.webdriver.support.ui import Select
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
from base_scraper import BaseScraper


class Tester(BaseScraper):
    def __init__(self):
        super().__init__()
        self.wait = WebDriverWait(self.driver, WAIT_TIME)

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url):
        self._url = url
        self.result = Result(url)

    def are_inner_pages_translated_to_hindi(self):
        links = self.get_links_one_level_deep()
        if len(links) > 3:
            links = random.sample(self.get_links_one_level_deep(), 3)
        self.open_link_in_new_tab(links[0])
        for link in links[1:]:
            if not self.fetch_url(link):
                self.result.note += "Page is down"
                return
            if not self.is_current_page_translated_to_hindi():
                self.result.note += ", inner pages not translated"
                self.result.isPass = False
                print("This inner page is not translated:" + self.driver.current_url)
                self.close_current_tab_and_switch_to_first_tab()
                return False
        self.close_current_tab_and_switch_to_first_tab()
        self.result.note += ", inner pages are translated"
        return True

    def is_current_page_translated_to_hindi(self):
        text = self.wait.until(
            EC.visibility_of_element_located(
                (
                    By.TAG_NAME,
                    "body",
                )
            )
        ).text
        return detect(text) == "hi"

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
        try:
            img_elements = self.wait.until(
                EC.visibility_of_all_elements_located(
                    (
                        By.XPATH,
                        "//*[@class='width-100 border-box padding-small large-up-width-1-2 border-box']",
                    )
                )
            )
        except TimeoutException:
            self.result.isPass = False
            self.result.note += "No images on wesbites"
            return
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

    def is_dropdown_working_correctly(self):
        dropdown = self.driver.find_element(
            By.XPATH,
            '//button[@class="hidden weight-semi large-up-block text-1 color-charcoal padding-right-small"]',
        )
        actions = ActionChains(self.driver)
        actions.move_to_element(dropdown)
        actions.perform()
        dropdown_element = self.driver.find_element(
            By.XPATH,
            '//a[@class="text-2 hover-no-underline weight-semi margin-vert-xsmall padding-left-medium padding-right-medium hidden large-up-block"]',
        )
        if dropdown_element.is_displayed():
            self.result.note += ", dropdown working properly"
            return True
        else:
            self.result.note += ", dropdown not working properly"
            self.result.isPass = False
            return False

    def run_tests(self, url):
        self.url = url
        if not self.fetch_url(url):
            self.result.note += "Website is down"
            return
        if not self.is_right_page():
            print(self.result.__str__())
            return
        self.are_images_high_quality()
        self.are_inner_pages_translated_to_hindi()
        self.is_dropdown_working_correctly()


class Result:
    def __init__(self, url: str, note: str = "", isPass: bool = True):
        self.note = note
        self.isPass = isPass
        self.url = url

    def __str__(self):
        print
        return f"{self.url}: \n{'Pass' if self.isPass else 'Fail'}: {self.note}"
