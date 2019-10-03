from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Crawler():
    def __init__(self, driver_path):
        chromedriver = driver_path
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        self.driver = webdriver.Chrome(chromedriver, chrome_options=options)

    def expand_shadow_element(self, element):
        shadow_root = self.driver.execute_script(
            'return arguments[0].shadowRoot', element
        )
        return shadow_root

    def get_all_attributes(self, element):
        attributes = self.driver.execute_script(
            'var items = {}; \
            for (index = 0; index < arguments[0].attributes.length; ++index) { \
                items[arguments[0].attributes[index].name] = \
                arguments[0].attributes[index].value \
            }; \
            return items;', 
            element
        )
        return attributes

    def get_shadow_root(self, by, value, driver=None):
        root = self.get_element(by, value, driver)
        shadow_root = self.expand_shadow_element(root)
        return shadow_root

    def get_all_elements(self, by, value, driver=None):
        if driver is None:
            driver = self.driver
        return WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (by, value)
            )
        )

    def get_element(self, by, value, driver=None):
        if driver is None:
            driver = self.driver
        return WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (by, value)
            )
        )
