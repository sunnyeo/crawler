import tempfile
import glob, time
import shutil, os

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Crawler():
    def __init__(self, driver_path, headless=False):
        chromedriver = driver_path
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-automation'])

        self.headless = headless
        self.download_path = tempfile.mkdtemp()
        print ('download_path: %s' %self.download_path)

        if self.headless:
            options.headless = True
        else:
            options.add_experimental_option('prefs',
                {'download.default_directory': self.download_path,
                'download.prompt_for_download': False,
                'download.directory_upgrade': True,
                'safebrowsing.enabled': False,
                'safebrowsing.disable_download_protection': True}
            )

        self.driver = webdriver.Chrome(chromedriver, chrome_options=options)

    def enable_download_in_headless_chrome(self):
        self.driver.command_executor._commands["send_command"] = \
                ("POST", '/session/$sessionId/chromium/send_command')

        params = {'cmd': 'Page.setDownloadBehavior',
                'params': {'behavior': 'allow', 'downloadPath': self.download_path}}
        self.driver.execute("send_command", params)

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

    def get_shadow_root(self, by, value, element=None):
        root = self.get_element(by, value, element)
        shadow_root = self.expand_shadow_element(root)
        return shadow_root

    def get_all_elements(self, by, value, element=None):
        if element is None:
            element = self.driver
        return WebDriverWait(element, 10).until(
            EC.presence_of_all_elements_located(
                (by, value)
            )
        )

    def get_element(self, by, value, element=None):
        if element is None:
            element = self.driver
        return WebDriverWait(element, 10).until(
            EC.presence_of_element_located(
                (by, value)
            )
        )

    def move_file(self, new_path, timeout=10):
        download = False
        for i in range(timeout):
            time.sleep(1)
            file_list = glob.glob(self.download_path + '/*')
            if len(file_list) == 1:
                if file_list[0].split('.')[-1] is not 'crdownload':
                    download = True
                    break
        if download:
            download_file = max(file_list, key=os.path.getctime)
            print ('Download: %s' %download_file)
            shutil.copy(download_file, new_path)
            os.remove(download_file)
        else:
            print ('Download Fail')
        return download

    def download_file_url(self, download_url, new_path):
        self.driver.execute_script('window.open()')
        self.driver.switch_to.window(self.driver.window_handles[-1])
        if self.headless:
            self.enable_download_in_headless_chrome()
        self.driver.get(download_url)

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[-1])

        return self.move_file(new_path)

    def download_file_click(self, new_path):
        self.driver.execute_script('window.open()')
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get('chrome://downloads')
        while True:
            try:
                old_path = self.download_path + '/' + self.driver.execute_script(
                    "return document.querySelector('downloads-manager').shadowRoot. \
                    querySelector('#downloadsList downloads-item').shadowRoot. \
                    querySelector('div#content #file-link').text"
                )
                shutil.copy(old_path, new_path)
                os.remove(old_path)
                break
            except:
                continue
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[-1])