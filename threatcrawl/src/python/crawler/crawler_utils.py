import os
import shutil
import sys
import threading
import time
from datetime import datetime, timedelta
from os import listdir, remove
from os.path import isfile, isdir, join, split
from typing import List, Union

import pyautogui
import pyperclip
import yaml
from bs4.dammit import EncodingDetector
from ewmh import EWMH
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tbselenium.tbdriver import TorBrowserDriver
from termcolor import colored

from database import create_api_from_config
from trainer.xpath_helper_functions import calculate_full_xpath
from utils import Logger


class CrawlerUtils:
    """A class containing helper functions for the crawler.

    Attributes
    ----------

    api: DataAPI
        API to interact with the database.
    download_path: str
        path where downloaded files will be stored.
    timeout: int
        timeout in seconds for loading a page.
    default_download_timeout: int
        default timeout in seconds for downloading a page.
    current_download_timeout:
        current and adjusted timeout in seconds for downloading a page.
    """

    def __init__(self):
        config_id = sys.argv[3]
        config = CrawlerUtils.read_config('config.yaml')
        self.api = create_api_from_config(config['database'])
        user_configuration = self.api['configurations'].find_by_id(config_id).exec()

        if user_configuration is None:
            print(f'Invalid configuration id provided: {config_id}')
            print('THREAT/crawl will quit because there is no configuration to run with')
            exit(1)

        crawling_config = user_configuration['configuration']
        preferences_config = user_configuration['preferences']
        self.download_path = crawling_config['torPath'] + 'Browser/Downloads/'
        self.timeout = preferences_config['pageLoadingTimeout']
        self.default_download_timeout = preferences_config['downloadTimeout']
        self.current_download_timeout = self.default_download_timeout

        pyautogui.FAILSAFE = False

    @staticmethod
    def read_config(filename: str):
        """Read the configuration of a given file.

        Parameters
        ---------
        filename : str
            Name of the file to read. Should be a .yaml file.

        Raises
        ---------
        FileNotFoundError
            If the config file could not be found

        """
        try:
            with open(filename) as config_file:
                config = yaml.full_load(config_file)

                return config
        except FileNotFoundError as error:
            message = f'Configuration could not be loaded because the config file could not be found. ' \
                      f'Filename = {filename}'
            raise RuntimeError(message) from error

    @staticmethod
    def wait_tor_browser():
        """This method will halt any progress until the tor browser is selected
        """
        ewmh = EWMH()
        # Make sure that the right window is selected
        time.sleep(1)
        while True:
            try:
                if not bytes("Tor Browser", ' utf-8') in ewmh.getWmName(ewmh.getActiveWindow()):
                    Logger.log("warning", "Browser not selected, progress will resume once it is selected again")
                    while True:
                        time.sleep(1)
                        try:
                            if bytes("Tor Browser", ' utf-8') in ewmh.getWmName(ewmh.getActiveWindow()):
                                break
                        except TypeError:
                            pass
                break
            except TypeError:
                pass

    @staticmethod
    def stop_download(driver: TorBrowserDriver):
        """Stops current downloads and removes all files in the download folder."""
        # Open download manager
        CrawlerUtils.wait_tor_browser()
        pyautogui.hotkey('ctrl', 'shift', 'y')
        time.sleep(1)
        new_handle_id = len(driver.window_handles)-1
        driver.switch_to.window(driver.window_handles[new_handle_id])

        # List of buttons for interrupting a download
        buttons = driver.find_elements(By.XPATH, "//*[@tooltiptext='Cancel']")
        for button in buttons:
            button.click()
            time.sleep(1)

        driver.close()
        time.sleep(1)
        new_handle_id = len(driver.window_handles) - 1
        driver.switch_to.window(driver.window_handles[new_handle_id])

    @staticmethod
    def remove_files(download_path: str):
        """Removes all files in the download folder.

        Parameters
        ----------
        download_path: str
            path in which the download files are saved.
        """
        # remove the files from local storage
        file_list = listdir(download_path)
        while len(file_list) > 0:
            file = file_list.pop()
            if isfile(download_path + file):
                remove(download_path + file)
            elif isdir(download_path + file):
                shutil.rmtree(download_path + file)
            else:
                continue

    @staticmethod
    def download_page(name: str):
        """Download the page by waiting for the browser to be in focus and pressing CTRL + S to save.

        Parameters
        ----------
        name : str
            Name of the file that the saved webpage will have.
        """
        CrawlerUtils.wait_tor_browser()

        # Use pyautogui to save the file to local storage
        # FOR ONLY THIS PART THE BROWSER NEEDS TO BE FOCUSSED
        pyautogui.hotkey('ctrl', 's')
        time.sleep(1)
        try:
            pyperclip.copy(name)
            # Test: circumventing possible race condition between storing the name in the clipboard and pasting.
            time.sleep(1)
        except pyperclip.PyperclipException:
            Logger.log("ERROR", "In order to work, THREAT/crawl needs xsel installed on the system. Please run "
                                "'sudo apt install xsel'")
        pyautogui.hotkey('ctrl', 'v')
        pyautogui.hotkey('enter')
        time.sleep(3)

    def save_page(self, name: str, driver: TorBrowserDriver, training: bool = False, is_retry: bool = False) -> str:
        """Downloads the current page and optionally stores it to the database. Returns its string representation

        Uses buttons commands to store a page locally, send the files to the database store the string of the main
        .html file, remove the files and return the string of the main .html file

        Parameters
        ----------
        name : str
            The name of the page to be stored.
        driver : TorBrowserDriver
            The driver to interact with the browser.
        training : bool
            A bool representing whether this is a page to save or not.
        is_retry : bool
            A bool needed to adjust the timeout for downloading the page.

        Returns
        -------
        page : str
            The main .html in String format of the current page.
        """

        if is_retry:
            self.current_download_timeout = round(1.5 * self.current_download_timeout)
        else:
            self.current_download_timeout = self.default_download_timeout

        downloaded = False

        try:
            name = name.split("//")[1].replace("/", "").replace("%", "")
            if len(name) > 250:
                name = name[0:249]
        except IndexError:
            name = driver.current_url.split("//")[1].replace("/", "").replace("%", "")
            if len(name) > 250:
                name = name[0:249]

        CrawlerUtils.remove_files(self.download_path)
        CrawlerUtils.download_page(name)

        # Check if the html page exists on disk and wait for it to exist until it times out.
        while not downloaded:
            try:
                start_time = datetime.now()
                while not isfile(self.download_path + name + ".html"):
                    if datetime.now() - start_time >= timedelta(seconds=self.current_download_timeout):
                        raise TimeoutException()
                    else:
                        time.sleep(1)
                    time.sleep(1)
                downloaded = True
            except TimeoutException:
                Logger.log("crawler", "Page download timed out, requesting new Tor circuit, adjusting timeouts"
                                      " and trying again")

                # Ask for a new tor circuit, refresh and download again.
                CrawlerUtils.stop_download(driver)
                CrawlerUtils.remove_files(self.download_path)

                CrawlerUtils.wait_tor_browser()
                pyautogui.hotkey("ctrl", "shift", "l")

                # Beginning placeholder for __navigate_to_page(driver, refresh=True)
                # Since I'm reloading, I have to set the cur_rul to about:blank to avoid reloading to infinity
                cur_url = "about:blank"
                time.sleep(1)
                loaded = False
                while not loaded:
                    try:
                        driver.refresh()
                        loaded = True
                    except TimeoutException:
                        CrawlerUtils.wait_tor_browser()
                        pyautogui.hotkey("ctrl", "shift", "l")
                        time.sleep(1)
                CrawlerUtils.wait_tor_browser()
                loading_new_page = True
                if loading_new_page:
                    loaded = False
                    started = datetime.now()

                    while not loaded:
                        try:
                            # Wait until the body of the page is loaded
                            driver.find_element_by("body", find_by=By.TAG_NAME)

                            if cur_url != driver.current_url and not driver.is_connection_error_page:
                                loaded = True
                            elif cur_url == driver.current_url and driver.is_connection_error_page:
                                raise TimeoutException("Retrieving new page timed out.")
                            elif datetime.now() - started > timedelta(seconds=self.timeout):
                                raise TimeoutException("Retrieving new page timed out.")
                        except TimeoutException as e:
                            Logger.log("error",
                                       "A DNS or Internet connection error occurred. Trying again in {} seconds"
                                       .format(self.timeout))
                            Logger.log("error", "Details on error: " + e.msg)
                            time.sleep(self.timeout)

                            started = datetime.now()
                            # Refresh current page
                            loaded = False
                            while not loaded:
                                try:
                                    driver.refresh()
                                    loaded = True
                                except TimeoutException:
                                    CrawlerUtils.wait_tor_browser()
                                    pyautogui.hotkey("ctrl", "shift", "l")
                                    time.sleep(1)
                            driver.set_page_load_timeout(driver.timeouts.page_load)
                # End placeholder refresh page
                CrawlerUtils.download_page(name)

        # Read the html page, should never fail because the download should always be done when reaching this code
        while True:
            try:
                with open(self.download_path + name + ".html", "r", encoding='UTF-8') as f:
                    page = f.read()

                    # Checking if it is none, if so try to read it again.
                    if page is None or page == "":
                        Logger.log("crawler", "Reading the page failed, trying again in one second")
                        time.sleep(1)
                        continue
                    break
            except UnicodeDecodeError:
                with open(self.download_path + name + ".html", "r", encoding='latin-1') as f:
                    page = f.read()

                    # Checking if it is none, if so try to read it again.
                    if page is None:
                        Logger.log("crawler", "Reading the page failed, trying again in one second")
                        time.sleep(1)
                        continue
                    break
            except FileNotFoundError:
                time.sleep(1)

        # Detecting encoding and reading the file again
        detector = EncodingDetector(page, is_html=True)
        encoding = detector.find_declared_encoding(page, is_html=True)

        with open(self.download_path + name + ".html", "r", encoding=encoding) as file:
            page = file.read()

        # Replace old encoding with python unicode (utf-8), such that it may be displayed properly elsewhere
        page = page.replace(encoding, "utf-8")

        # Read all the files in the folder to push to the query
        folder_files = []
        folder_names = []

        try:
            files = listdir(self.download_path + name + "_files")
            while len(files) > 0:
                filename = files.pop()
                if not (filename.endswith(".gif") or filename.endswith(".js")):
                    path = join(self.download_path + name + "_files", filename)
                    if isfile(path):
                        with open(path, 'rb') as f:
                            folder_names.append(filename)
                            folder_files.append(f.read())
                    else:
                        path_begin, path_end = split(path)
                        for f in listdir(path):
                            files.append(str(join(path_end, f)))

        except FileNotFoundError:
            Logger.log("crawler", "No extra files needed for this webpage")

        # Send the file to the database, comment to not flood the database. Update if already in db otherwise insert
        query = {'page_url': driver.current_url}
        page_count = self.api["full webpage"].count_documents(query).exec()
        page_dict = {
            'page_url': driver.current_url,
            'file_name': name,
            'file_contents': page,
            'folder_names': folder_names,
            'folder_contents': folder_files,
            'badly_formatted': False
        }

        def insert_page(page_dictionary, file_name, data_api):
            Logger.log("database", "File with name: " + colored(file_name, "cyan") + " is being uploaded into the database")
            data_api["full webpage"].insert(page_dictionary).exec()
            Logger.log("database", "File with name: " + colored(file_name, "cyan") + " saved to the database")

        def update_page(query_message, page_dictionary, file_name, data_api):
            Logger.log("database", "File with name: " + colored(file_name, "cyan") + " is being updated in the database")
            data_api["full webpage"].update(query_message, page_dictionary).exec()
            Logger.log("database", "File with name: " + colored(file_name, "cyan") + " updated in the database")

        th = threading.Thread()
        # I'm almost sure there's no case in which a long-to-load page will be required before the end of this task.
        if page_count == 0:
            th = threading.Thread(target=insert_page, args=(page_dict, name, self.api))
            th.start()
        elif page_count >= 1:
            th = threading.Thread(target=update_page, args=(query, page_dict, name, self.api))
            th.start()

        # If we're during training, we need to get first the page saved in the db, as it is needed for training purposes
        if training:
            th.join()

        CrawlerUtils.remove_files(self.download_path)

        return page

    @staticmethod
    def find_associated_element(candidate_list: List[WebElement], target: WebElement, driver: TorBrowserDriver
                                ) -> Union[WebElement, None]:
        """This function allows to identify the most "close" WebElement from a list of WebElements to a specific
        WebElement by comparing the similarity of their XPaths. The element among the candidates with the longest common
        XPath with the target is going to be the associated element.

        Parameters
        ----------
        candidate_list: List[WebElement]
            List of the potential WebElements associated to the target.
        target: WebElement
            The element for which it is necessary to find the associated element.
        driver: TorBrowserDriver
            Instance of the crawler.

        Returns
        -------
        Union[WebElement, None]
            The WebElement associated to the target.
        """
        target_xpath = calculate_full_xpath(target, driver)
        prefixes = []
        for candidate in candidate_list:
            prefixes.append(os.path.commonprefix([target_xpath, calculate_full_xpath(candidate, driver)]))
        longest_prefix = max(prefixes, key=len)
        security_check = list(filter(lambda x: len(x) == len(longest_prefix), prefixes))
        if len(security_check) != 1:
            return None
        else:
            index = prefixes.index(longest_prefix)
            return candidate_list[index]
