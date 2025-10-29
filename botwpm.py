from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
from selenium import webdriver
from typing import Union, Optional
from pathlib import Path
import logging
import time
import yaml

logging.basicConfig(
  format="%(levelname)s:\t%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

class BotWPM:
  def __init__(self, browser:str, url:str, *, WPM:int, TIME:int, login:Optional[dict]=None, config:Optional[dict]=None):
    self.driver = self.__get_webdriver(browser)
    self.driver.set_window_size(width=980, height=1280)
    self.__data = self.__load_data(url)
    self.__login = login
    self.__config = config 
    self.__url = url
    self._wpm = WPM 
    self._time = TIME
  
  def __get_webdriver(self, browser:str) -> Union[webdriver.Chrome, webdriver.Firefox]:
    return {
      "chrome": lambda: webdriver.Chrome(),
      "firefox": lambda: webdriver.Firefox(),
    }.get(browser)()
  
  def __load_data(self, url) -> dict:
    url = "://".join(urlparse(url)[:2]) + "/"
    with open((Path(__file__).absolute().parent / "data.yaml"), "r") as file:
      data = yaml.safe_load(file)   
    return data[url]
  
  @property
  def interval(self):
    return self._time / (self._wpm * 5 * (60 / self._time) )

  def __button_click(self, xpath:str):
    self.driver.find_element(By.XPATH, xpath).click()
  
  def __accept_cookies(self):
    if "cookies" in self.__data:
      logger.info("Accepting cookies...")
      try:
        WebDriverWait(self.driver, 5).until(
          EC.presence_of_element_located((By.XPATH, self.__data["cookies"]["xpath"]))
        ).click()
        logger.info("Cookies have been accepted successfully.")
      except Exception as e:
        logger.exception("Cookies were not accepted: %s", e)
    else:
      logger.warning("Cookies path are missing. Skipping cookies process.")

  def __sign_in_user(self):
    if "login" in self.__data and self.__login:
      logger.info("Starting logging process for user '%s'", self.__login.get("email"))
      try:
        self.driver.get(self.__data["login"]["url"])
        time.sleep(.5)
        for key, element in self.__data["login"]["xpath"]["form"].items():
          self.driver.find_element(By.XPATH, element).send_keys(self.__login.get(key.lower()))
        self.__button_click(xpath=self.__data["login"]["xpath"]["submit"])
        time.sleep(2)
        if self.driver.current_url != self.__url:
          self.driver.get(self.__url)
        logger.info("User has been authenticated sucessfully.")
      except Exception as e:
        logger.exception("Login process failed for user '%s': %s", self.__login.get("username", "unknown"), e)
        raise e
    else:
      logger.warning("Login credintials are missing. Skipping login process.")

  def __set_config(self):
    if "config" in self.__data and self.__config:
      logger.info("Starting the process of setting up the configration...")
      try:
        for k, v in self.__config.items():
          k:str = k.lower()
          if k in self.__data["config"]:
            self.__button_click(xpath=self.__data["config"][k][v])
          time.sleep(.1)
          logger.info("Configuration settings have been applied.")
      except Exception as e:
        logger.exception("Configuration process failed: %s", e)
    else:
      logger.warning("Configuration settings are missing. Skipping configuration process.")

  def type(self):
    if self.driver.current_url != self.__url:
      self.driver.get(self.__url)


    logger.info("Starting the process of typing...")
    start_time = time.time()
    end_time = start_time + self._time
    typed_chars = 0

    try:      
      input_field = self.driver.find_element(By.XPATH, self.__data["typing-field"]["path"]["input"])
      words_element = WebDriverWait(self.driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, self.__data["typing-field"]["path"]["words"]))
      )
      
      while time.time() < end_time:
        for char in list(words_element.text):
          if time.time() >= end_time:
            break
          try:
            input_field.send_keys(char)
            time.sleep(self.interval)
            typed_chars += 1
          except WebDriverException as e:
            logger.error(f"Keypress error: {e}. Retrying char '{char}'...")
            time.sleep(0.05)
            continue

        try:
          words_element = self.driver.find_element(By.CSS_SELECTOR, self.__data["typing-field"]["path"]["words"])
        except:
          pass

    except Exception as e:
      print(e)      
      self.driver.quit()

  def run(self):
    self.driver.get(self.__url)
    self.__sign_in_user()
    self.__accept_cookies()
    self.__set_config()
    self.type()