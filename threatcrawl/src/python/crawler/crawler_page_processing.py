"""Processing class for the Crawler module"""
import json
import random
import threading
import time
import pyautogui
from interpreter import Interpreter, ParsedData, SectionData, ThreadData
from tbselenium.tbdriver import TorBrowserDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException, \
    WebDriverException, ElementNotInteractableException, MoveTargetOutOfBoundsException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from config import Configuration

from enums import PageType, Relevance, ThreadStatus
from utils import Logger
from trainer import ResourceIdentifier
from database import DataAPI
from datetime import datetime, timedelta
import typing as t

from .crawler_utils import CrawlerUtils


class CrawlerPageProcessing:
    """Processing class for the Crawler module.

    This class will be responsible for the fetching of the next page, possibly from the next thread, sending this page
    to the interpreter and relaying this result back to the main module of the crawler. Furthermore, this class
    will be able to move to a platform based on the given configurations, this will be used in the beginning of
    every session to initialize the crawler module.

    Parameters
    ----------
    data_api : DataAPI
        An instance of the DataAPI class, used to access the database.
    parameters : Configuration
        The parameters of the crawler.
    solved : threading.Condition
        Resume condition to communicate the crawler that the CAPTCHA has been solved and crawler execution can resume.

    Attributes
    ----------
    download_path : str
        Path to the tor browser with the path to the download folder appended to it.
    __data_api: DataAPI
        An instance of the DataAPI class, used to access the database.
    __visited_items : dict<PageType, dict<K, WebElement[]>>
        A dictionary of visited web elements for each page type currently open. K is either "ff" or "mt", with "ff"
        tracking WebElements which are unique for each page (so two visits to the same page give two unique sets
        of FWEs which are most likely disjoint) and "mt" saving the tags for multi-page tracking.
    __current_page :
        The HTML of the page currently in the browser. Initialized to None.
    __after_workday_url : str
        URL for the page to be trained after the workday. Initialized to None.
    __after_workday_page : str
        HTML of the page to be trained after the workday. Initialized to None.
    __parameters : Configuration
        The parameters of the crawler.
    __crawler_utils : CrawlerUtils
        The instance of a helper for the crawler.
    __interpreter : Interpreter
        The main class of the interpreter module which will handle the processing of the pages.
    explored_elements : list<str>
        List of the Selenium WebElement ids of each explored element (threads).
    __explored_threads_from_db : list<str>
        List of the titles of threads that have been previously crawled.
    """

    def __init__(self, data_api: DataAPI, parameters: Configuration, solved: threading.Condition):
        self.download_path = parameters.crawling.tor_path + "Browser/Downloads/"
        self.__data_api = data_api
        self.__visited_items = {}
        self.__current_page = None
        self.__after_workday_url = None
        self.__after_workday_page = None
        self.__parameters = parameters
        self.__crawler_utils = CrawlerUtils()
        self.__interpreter = Interpreter(data_api, self.__parameters, self.download_path, solved,
                                         need_training=not parameters.preferences["skipTraining"])
        self.explored_elements = []
        self.__explored_threads_from_db = self.__get_threads_of_platform()

        self.__opened_new_thread = False

        pyautogui.FAILSAFE = False

    def __get_threads_of_platform(self) -> t.List[str]:
        """Function to obtain a list of the titles of the threads that have been parsed for that platform.

        Returns
        -------
        final : t.List[str]
            A list with the titles of the crawled threads.
        """
        platform_id = self.__data_api["platforms"].find_one({"url": self.__parameters.crawling.platform}).exec()
        result = self.__data_api["threads"].find({"platform_id": platform_id["_id"]}).exec()
        final = []
        for res in result:
            final.append(res['title'])
        return final

    @staticmethod
    def toJSON(obj):
        return json.dumps(obj, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def next_page(self, driver: TorBrowserDriver, cur_page: ParsedData = None) -> ParsedData:
        """This method will fetch the next page from the current platform and parse it via the interpreter.

        This method will fetch the next page from the current platform. If there are no more pages on the current
        thread it will move to the next thread. The fetched page will be sent to the interpreter such that it will be
        parsed. The parsed page will be the return value for this method.

        Parameters
        ----------
        driver : TorBrowserDriver
            The driver to interact with the browser.
        cur_page : t.Union[ParsedData, None]
            The data from the current page. If this value is None it means that we are yet to visit the target platform.

        Returns
        -------
        ParsedData
            The data of the parsed page that is received from the interpreter.

        Raises
        ------
        NoMorePagesException
            There are no more pages to be found hence the crawler cannot continue parsing more pages.
        """

        next_page_type = PageType.FrontPage
        # First page, go through the training pages first and possibly login in the process
        if cur_page is None:
            if self.__parameters.preferences["skipTraining"] is False:
                cur_page = self.__training_sequence(driver)
            else:

                if self.__parameters.crawling.platform == self.__parameters.crawling.platform_login:
                    self.__navigate_to_page(driver, url=self.__parameters.crawling.platform)
                    page = self.__crawler_utils.save_page(driver.current_url, driver)
                    self.__current_page = page
                    cur_page = self.__interpreter.parse_page(page, driver.current_url, next_page_type)
                else:
                    cur_page, page = self.__login_sequence(driver)

        # normal page navigation
        else:
            # The actual page content, also send this to the database
            page = self.__crawler_utils.save_page(driver.current_url, driver)
            self.__current_page = page
            # If the page is none, there are probably blacklisted words, go to homepage
            if page is None:
                driver.load_url(self.__parameters.crawling.platform, wait_for_page_body=True)
            else:
                page_type = self.__interpreter.determine_page_type(self.__current_page)
                # Executing JS (if any) before interpreting the page
                if self.__interpreter.js_db_struct[page_type] != '':
                    driver.execute_script(self.__interpreter.js_db_struct[page_type])
                    # TODO this should wait and check if all the (expected) elements in the page are now visible
                    time.sleep(20)

                    # the actual page content, also send this to the database
                    page = self.__crawler_utils.save_page(driver.current_url, driver)
                    self.__current_page = page

            # Send the page to the interpreter and return the result
            cur_page = self.__interpreter.parse_page(page, driver.current_url, driver=driver,
                                                     new_thread=self.__opened_new_thread)
            # if self.__opened_new_thread:
            #     self.__opened_new_thread = False

            # This means that retraining needs to happen after the workday
            if self.__interpreter.training_after_workday and self.__after_workday_url is None:
                self.__after_workday_url = driver.current_url
                self.__after_workday_page = self.__current_page

        if cur_page is not None:
            # Check if the page is a login page, if so login and fetch the new page
            if cur_page.username_field is not None:
                self.__login(cur_page, driver)

        return cur_page

    def interact_with_page(self, driver: TorBrowserDriver, cur_page: ParsedData):
        """This method detects the type of page and detects the next button(s) to click or page to open/close, according
        to the type of page and to the presence of some elements within the page.

        Parameters
        ----------

        driver: TorBrowserDriver
            The driver to interact with the browser.
        cur_page : t.Union[ParsedData, None]
            The data from the current page. If this value is None it means that we are yet to visit the target platform.

        """

        new_tab = True  # Whether the new page must be opened in a new tab or in the same tab
        done = False  # Whether processing the current page is done and hence the tab can be closed or not
        button = None
        next_page_type = None
        thread_titles_elements = None
        section_or_subsection_link = False
        if isinstance(cur_page, SectionData):
            # List of sections, assume this to be on the home page
            if cur_page.page_type == PageType.FrontPage and cur_page.section_list is not None:
                button = self.__find_elements(cur_page.section_list, driver, True, cur_page.page_type,
                                              multi_page_track=True)
                next_page_type = PageType.SectionPage
                section_or_subsection_link = True

            # List of subsections, assume this to be on the section page
            elif cur_page.page_type == PageType.SectionPage and cur_page.subsection_list is not None:
                button = self.__find_elements(cur_page.subsection_list, driver, True, cur_page.page_type,
                                              multi_page_track=True)
                next_page_type = PageType.SubsectionPage
                section_or_subsection_link = True

            # List of threads, and it's going to be either on the section page or subsection page.
            if (cur_page.page_type == PageType.SectionPage or cur_page.page_type == PageType.SubsectionPage) and \
                    cur_page.thread_list is not None and button is None:  # and cur_page.subsection_list is None:
                new_tab = True  # Some cases might lead to entering this branch with new_tab set to false, resetting
                next_page_type = PageType.ThreadPage

                '''# Use first page buttons if present
                if cur_page.first_thread_page_button is not None:
                    button = self.__find_elements(cur_page.first_thread_page_button, driver, True, cur_page.page_type)
                    thread_titles_elements = self.__find_elements(cur_page.thread_list, driver, True,
                                                                  cur_page.page_type, cur_page.thread_relevancy,
                                                                  cur_page.thread_status)
                '''
                # If there are no first page buttons, fall back to thread titles.
                if button is None:
                    button = self.__find_elements(cur_page.thread_list, driver, True, cur_page.page_type,
                                                  cur_page.thread_relevancy, cur_page.thread_status)
                    self.__opened_new_thread = True
                # If there are no threads, then explore subsections.
                if button is None:
                    button = self.__find_elements(cur_page.subsection_list, driver, True, cur_page.page_type)

                # If nothing is returned, go to next page if possible
                if button is None:
                    button = self.__find_elements(cur_page.next_page_button, driver, False, cur_page.page_type)
                    new_tab = False

            if button is None:
                # Everything has been visited or is not on the current page so this page is fully done.
                done = True
        elif isinstance(cur_page, ThreadData):
            # On a thread page we check if it is blacklisted or not and delete everything in case it is
            if cur_page.page_relevancy == Relevance.BLACKLISTED:
                self.__data_api["full webpage"].update({
                    'page_url': driver.current_url},
                    {'$set': {'folder_contents': []}}
                ).exec()
                # Exit the tab if the thread is blacklisted
                done = True
            elif cur_page.page_relevancy == Relevance.IRRELEVANT:
                # Exit the tab if the thread is irrelevant
                done = True
            elif cur_page.is_thread_complete:
                # Thread is parsed completely, exit tab
                done = True
            else:
                new_tab = False
                try:
                    if self.__opened_new_thread and cur_page.first_thread_page_button is not None:
                        # Let's try to rollback to the first page if this is a new thread just opened.
                        button = self.__find_elements(cur_page.first_thread_page_button, driver, False,
                                                      cur_page.page_type)
                        for element in button:
                            # TODO This should be checked everywhere
                            if not element.is_enabled():
                                button.remove(element)
                        if len(button) == 0:
                            raise NoSuchElementException
                        self.__opened_new_thread = False
                    else:
                        raise NoSuchElementException
                except NoSuchElementException:
                    self.__opened_new_thread = False
                    try:
                        button = self.__find_elements(cur_page.next_page_button, driver, False, cur_page.page_type)
                        if len(button) == 0:
                            raise NoSuchElementException
                    except NoSuchElementException:
                        done = True
                        button = None
        else:
            # Got an instance of ParsedData that is not an instance of SectionData or ThreadData. Strange.
            Logger.log("error", "Crawler received an instance of ParsedData that is not an instance of SectionData "
                                "or ThreadData which indicates an error somewhere or not implemented behaviour. "
                                "Stopping execution now.")
            exit(1)
        # If the button is present do some navigation
        if button is not None or done:
            if isinstance(button, WebElement):
                # We have a single element to click
                if button not in self.explored_elements:
                    self.__navigate_to_page(driver, current_page=cur_page, button=button, close_tab=done, new_tab=new_tab)
                    if section_or_subsection_link:
                        self.explored_elements.append(button.id)
                else:
                    if cur_page.page_type == PageType.FrontPage:
                        Logger.log("state", "THREAT/crawl terminated the exploration of all the content in the"
                                            " sections of interest. Shutting down.")
                        exit(0)
                    else:
                        self.__close_tab(cur_page, driver)

            elif isinstance(button, list):
                # It may be that more than one button matched the next page...
                if not new_tab:
                    if len(button) == 0:
                        self.__navigate_to_page(driver, current_page=cur_page, close_tab=done, new_tab=new_tab)
                    else:
                        self.__navigate_to_page(driver, current_page=cur_page, button=button[0], close_tab=done,
                                                new_tab=new_tab)
                else:
                    all_explored = True
                    # Select a random thread from the list.
                    if next_page_type is not None and next_page_type == PageType.ThreadPage:
                        while len(button) != 0:
                            element = random.choice(button)
                            relevance = cur_page.thread_relevancy[button.index(element)]
                            del cur_page.thread_relevancy[button.index(element)]
                            button.remove(element)
                            if relevance == Relevance.BLACKLISTED or relevance == Relevance.IRRELEVANT:
                                continue
                            # This is the case in which the current link contains the title of the thread
                            # (it is not the first page link)
                            if thread_titles_elements is None:
                                # I parsed this thread
                                thread_title = element.text
                                if element.text in self.__explored_threads_from_db:
                                    continue
                            # This is the case in which we have to get in the thread to know the name of it.
                            #  This function calculates the the corresponding thread title by comparing the XPath of the
                            #  button and the XPath of all the thread titles. Supposing that this button is on the same
                            #  row of a table, this button and the corresponding thread will have a longer common prefix
                            #  thus allowing us to identify the correnct one.
                            #  first_page_button_xpaths_list = /html/.../table/tr[2]/td[2]/p[1]/a
                            #  threads_list = /html/.../table/tr[1,2]/td[2]/h4/b/a
                            #  The function computes then the prefixes /html/.../table/tr[ ... and /html/.../table/tr[2]
                            #  The last prefix is longer, then this is the one that will be chosen.

                            # TODO: still remains the problem for the mixed scenario: when there are buttons for first
                            #  page but not for every element, then those without will be excluded from the analysis.
                            #  Probably the solution can be tackled from another perspective, that would ease the whole
                            #  process: train within the thread for the first page button. If this button is there and
                            #  is clickable, then this must be clicked to begin with the thread. This is a possible
                            #  solution to implement in a future release of the tool.

                            # This problem should be fixed now: there's no "first page button" anymore, but rather
                            # the user shows the "first page button" within the thread, making this approac more general
                            # and robust.
                            else:
                                thread_title = self.__crawler_utils.find_associated_element(thread_titles_elements,
                                                                                            element, driver).text
                                if thread_title in self.__explored_threads_from_db:
                                    continue
                            # TODO: This should happen at the end of the thread, to prevent cases in which
                            #  errors break the parsing of a thread and it will be skipped as a result.
                            self.__explored_threads_from_db.append(thread_title)

                            self.__navigate_to_page(driver, current_page=cur_page, button=element, close_tab=done,
                                                    new_tab=new_tab)
                            self.explored_elements.append(element.id)
                            break
                        if len(button) == 0:
                            # Try to find next page
                            button = self.__find_elements(cur_page.next_page_button, driver, False, cur_page.page_type)
                            if button is None or len(button) == 0:
                                self.__close_tab(cur_page, driver)
                            else:
                                self.__navigate_to_page(driver, current_page=cur_page, button=button, close_tab=False,
                                                        new_tab=False)
                    else:
                        for element in button:
                            if element.id not in self.explored_elements:
                                all_explored = False
                                self.__navigate_to_page(driver, current_page=cur_page, button=element, close_tab=done,
                                                        new_tab=new_tab)
                                self.explored_elements.append(element.id)
                                break
                        if all_explored:
                            if cur_page.page_type == PageType.FrontPage:
                                Logger.log("state", "THREAT/crawl terminated the exploration of all the content in the"
                                                    " sections of interest. Shutting down.")
                                exit(0)
                            else:
                                self.__close_tab(cur_page, driver)
            else:
                self.__close_tab(cur_page, driver)

        # If no button is found, return to the URL and start crawling again
        else:
            Logger.log("crawler", "Button is None. Aborting current operation and recovering to a previous page.")
            if len(driver.window_handles) > 1:
                self.__navigate_to_page(driver, current_page=cur_page, close_tab=True)
            else:
                self.__navigate_to_page(driver, url=self.__parameters.crawling.platform)

    def __navigate_to_page(self, driver: TorBrowserDriver, current_page: ParsedData = None, close_tab: bool = False,
                           new_tab: bool = False, button: WebElement = None, url: str = None, refresh: bool = False):
        """Loads a webpage based on the given input. If none of the optional parameters are set then this function will
        do nothing.

        In order to trigger the intended behaviour, set the following parameters to get the desired result. They are
        ordered by execution flow, so when traversing the following list from top to bottom, the desired behaviour
        occurs on the first entry for which the condition behind the comma is true.

        - Close a tab, close_tab = True and current_page != None
        - Click on a button and the resulting page opens in a new tab, button != None and new_tab = True
        - Click on a button and the resulting page opens in the current tab, button != None
        - Load a URL and the resulting page opens in a new tab, url != None and new_tab = True
        - Load a URL and the resulting page opens in the current tab, url != None
        - Refresh the page, refresh = True
        - Nothing, all of the above conditions were not met

        Parameters
        ----------
        driver : TorBrowserDriver
            Driver that controls the Tor browser.
        current_page : ParsedData, optional
            Extracted information from the current page. None by default.
        close_tab : bool, optional
            Whether we have fully processed this page, there's nothing more to crawl to from this page and hence we can
            safely close the tab. False by default.
        new_tab : bool, optional
            Whether to open the newly loaded page in a new tab or not. False by default.
        button : WebElement, optional
            The button to click to go to a new page. None by default.
        url : str, optional
            The URL to load. None by default.
        refresh : bool, optional
            Specifies if to refresh the page.
        """
        cur_url = driver.current_url
        loading_new_page = False

        self.__crawler_utils.wait_tor_browser()
        if close_tab:
            self.__close_tab(current_page, driver)
        elif new_tab and button is not None:
            # opens new tab
            tab_count = len(driver.window_handles)
            unreachable = True
            while unreachable:
                try:
                    button.send_keys(Keys.CONTROL + Keys.ENTER)
                    unreachable = False
                except ElementNotInteractableException:
                    try:
                        # chain = ActionChains(driver)
                        # chain.move_to_element(button)
                        # chain.send_keys(Keys.CONTROL + Keys.ENTER)
                        # chain.perform()
                        driver.maximize_window()
                        time.sleep(2)
                        button.send_keys(Keys.CONTROL + Keys.ENTER)
                        unreachable = False
                    except MoveTargetOutOfBoundsException:
                        driver.maximize_window()
                        time.sleep(2)
                        button.send_keys(Keys.CONTROL + Keys.ENTER)
                        driver.set_window_position(0, 0)
                        driver.set_window_size(1000, 800)
                        unreachable = False
                    except ElementNotInteractableException:
                        # In this case probably the XPath isn't too great.
                        button = button.find_element(By.XPATH, "./..")
                        Logger.log("Error", "The element seems unreachable. Trying the parent...")

            # Wait for a bit until the driver detects the second tab
            start_time = datetime.now()
            while len(driver.window_handles) != tab_count + 1:
                try:
                    if datetime.now() - start_time > timedelta(seconds=self.__parameters.crawling.timeout):
                        raise TimeoutException()
                    time.sleep(1)
                except TimeoutException:
                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    unreachable = True
                    while unreachable:
                        try:
                            button.send_keys(Keys.CONTROL + Keys.ENTER)
                            unreachable = False
                        except ElementNotInteractableException:
                            button = button.find_element(By.XPATH, "./..")
                            Logger.log("Error", "The element seems unreachable. Trying the parent...")
                    start_time = datetime.now()

            driver.switch_to.window(driver.window_handles[-1])  # Opens last tab (i.e. most recent opened)

            # Wait for tab to start loading the relevant link
            while driver.current_url == "about:blank":
                time.sleep(2)

            loading_new_page = True
        elif button is not None:
            # Wait for a bit because sometimes the click is not noticed by the code immediately leading to the
            # same page being analysed again while the next one is displayed...
            try:
                # button = WebDriverWait(driver, 10).until(
                #     EC.element_to_be_clickable((By.XPATH, self.__generate_xpath(button, ""))))
                if isinstance(button, WebElement):
                    unreachable = True
                    while unreachable:
                        try:
                            button.click()
                            unreachable = False
                        except ElementNotInteractableException:
                            button = button.find_element(By.XPATH, "./..")
                elif isinstance(button, list):
                    # I'm assuming that having this kind of scenarios happens only when the xpath match a number of
                    # elements, but they've not been ignored in training phase and shouldn't cause harm in the majority
                    # of cases.
                    unreachable = True
                    while unreachable:
                        try:
                            button[0].click()
                            unreachable = False
                        except ElementNotInteractableException:
                            button = button[0].parent
                elif button is None:
                    raise ElementNotInteractableException("This button is a NoneType. Something's missing.")
                else:
                    raise ElementNotInteractableException("This button has an unexpected type. "
                                                          "Something went sour somewhere.")
                time.sleep(2)
            except (ElementClickInterceptedException, ElementNotInteractableException):
                # Apparently clicking failed so trying via action chain. If this breaks... NotLikeThis
                chain = ActionChains(driver)
                # TODO This may be promoted to a general use for finding elements.
                if current_page.page_type == PageType.LoginPage:
                    found = False
                    while not found:
                        chain.send_keys(Keys.TAB)
                        chain.perform()
                        current_element = driver.switch_to.active_element
                        current_element_xpath = self.__generate_xpath(current_element, "")
                        if current_element_xpath == current_element_xpath:
                            found = True
                            current_element.send_keys(Keys.ENTER)
                else:
                    found = True  # Just because this doesn't cover the login page case.
                    chain.move_to_element(button)
                    chain.click()
                    chain.perform()
                    time.sleep(2)

                if cur_url == driver.current_url:
                    if found is not None:
                        # This means the click failed because of an obscuring element, so scrolling it into view and
                        # then clicking.
                        driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        button.click()
                        time.sleep(2)

            loading_new_page = True
        elif new_tab and url is not None:
            # Open new tab and load the relevant URL
            tab_count = len(driver.window_handles)

            # Wait for the browser to be in focus and then open a new tab
            self.__crawler_utils.wait_tor_browser()
            pyautogui.hotkey("ctrl", "t")

            while len(driver.window_handles) != tab_count + 1:
                time.sleep(1)  # Wait for a bit until the driver detects the second tab

            driver.switch_to.window(driver.window_handles[-1])  # Opens last tab (i.e. most recent opened)

            try:
                driver.load_url(url)
            except WebDriverException:
                Logger.log("error", "Some unknown error occurred while loading the page, trying again in {} seconds"
                           .format(self.__parameters.crawling.timeout))
                time.sleep(self.__parameters.crawling.timeout)

            # Wait for tab to start loading the relevant link
            while driver.current_url == "about:blank":
                time.sleep(2)

            loading_new_page = True
        elif url is not None:
            # Load the URL
            try:
                driver.load_url(url)
            except WebDriverException:
                Logger.log("error", "Some unknown error occurred while loading the page, trying again in {} seconds"
                           .format(self.__parameters.crawling.timeout))
                time.sleep(self.__parameters.crawling.timeout)
            time.sleep(2)
            loading_new_page = True
        elif refresh:
            # Refresh the page
            try:
                loaded = False
                while not loaded:
                    try:
                        driver.refresh()
                        loaded = True
                    except TimeoutException:
                        CrawlerUtils.wait_tor_browser()
                        pyautogui.hotkey("ctrl", "shift", "l")
                        time.sleep(1)
            except WebDriverException:
                Logger.log("error", "Some unknown error occurred while loading the page, trying again in {} seconds"
                           .format(self.__parameters.crawling.timeout))
                time.sleep(self.__parameters.crawling.timeout)
            time.sleep(2)
            loading_new_page = True
        # This is the case in which there's no button to click, when attempting to find the thread first page button.
        else:
            return

        if url == cur_url or refresh:
            cur_url = "about:blank"  # Setting cur_url to something else otherwise we'll be hanging indefinitely

        if loading_new_page:
            # Wait until the page is loaded
            loaded = False
            started = datetime.now()

            while not loaded:
                try:
                    # Wait until the body of the page is loaded
                    driver.find_element_by("body", find_by=By.TAG_NAME)
                    # TODO this fails whenever in the training we have two identical URLs one after the other -
                    #  it thinks that the page never managed to load properly.
                    if cur_url != driver.current_url and not driver.is_connection_error_page:
                        loaded = True
                    elif cur_url == driver.current_url and driver.is_connection_error_page:
                        raise TimeoutException("Retrieving new page timed out.")
                    elif datetime.now() - started > timedelta(seconds=self.__parameters.crawling.timeout):
                        raise TimeoutException("Retrieving new page timed out.")
                except TimeoutException as e:
                    Logger.log("error", "A DNS or Internet connection error occurred. Trying again in {} seconds"
                               .format(self.__parameters.crawling.timeout))
                    Logger.log("error", "Details on error: " + e.msg)
                    time.sleep(self.__parameters.crawling.timeout)

                    started = datetime.now()
                    # Refresh current page
                    while True:
                        try:
                            driver.refresh()
                            break
                        except TimeoutException:
                            driver.set_page_load_timeout(int(self.__parameters.crawling.timeout * 1.5))
                except WebDriverException as e:
                    if "TypeError" in e.msg:
                        # This may happen if the driver tries to check the page when the content is not available
                        Logger.log("error", "I attempted to read the page too early. I'll wait 5 seconds before "
                                            "checking again")
                        time.sleep(5)
                    else:
                        raise e

    def __login(self, parsed_page: ParsedData, driver: TorBrowserDriver):
        """This method will fill in and login at a login page.

        Especially during the execution of next_page() it might be the case that a login window appears, or it
        needs to be satisfied first. This function will make sure to use the credentials from the parameters to
        satisfy the login procedure of the current platform.

        Parameters
        ---------
        parsed_page : ParsedData
            The parsed data which indicate the fields and buttons for the login page
        driver : TorBrowserDriver
            The driver to interact with the browser.

        Raises
        ------
        BadArgumentException
            The given argument for the parameters is invalid (not of proper type for example).

        NavigationError
            When the crawler is not able to find its way to the platform it will raise a NavigationError.
        """

        username = self.__find_elements(parsed_page.username_field, driver, False, parsed_page.page_type)[0]
        password = self.__find_elements(parsed_page.password_field, driver, False, parsed_page.page_type)[0]

        # Fill out username in human speed
        for letter in self.__parameters.username:
            username.send_keys(letter)
            time.sleep(0.23)

        # Fill out password in human speed
        for letter in self.__parameters.password:
            password.send_keys(letter)
            time.sleep(0.23)

        # Locate the button to move to the next page
        button = self.__find_elements(parsed_page.login_button, driver, False, parsed_page.page_type)[0]

        # click that button (TODO maybe include mouse movement)
        self.__navigate_to_page(driver, button=button, current_page=parsed_page)

        # Wait for a possible redirect to trigger
        time.sleep(10)

    def __find_elements(self, object_id: ResourceIdentifier, driver: TorBrowserDriver, visited_check: bool,
                        page_type: PageType, relevancy: t.List[Relevance] = None, status: t.List[ThreadStatus] = None,
                        multi_page_track: bool = False) -> t.Optional[t.List[WebElement]]:
        """ A method that returns the object based on the ParsedData data object

        Parameters
        ----------
        object_id : ResourceIdentifier
            The object to fetch from the page.
        driver : TorBrowserDriver:
            The driver to use to retrieve the object.
        visited_check : bool
            This is used to indicated whether we only want to use the buttons once, leaving out duplicates.
        page_type : PageType
            Type of page currently being visited.
        relevancy : list of ThreadRelevancy
            A list of the thread relevancies, only applicable when dealing with threads otherwise it is None.
        status : list of ThreadStatus
            A list of the thread statuses, only applicable when dealing with threads otherwise it is None.
        multi_page_track : bool
            Whether we need to track this element across multiple pages or not. Defaults to False.

        Return
        ------
        object : WebElement or None
            The object usable by Selenium or None if nothing could be found (or everything has already been visited).
        """

        if object_id is None:
            return None

        # objects = object.get_elements(self.__current_page)
        #
        # for j in range(len(objects)):
        #     item = None  # Reset before each iteration for proper functioning
        #     c_object = ' '.join(objects[j][:objects[j].find(">")].replace("\n", " ").split())
        #
        #     # This splits on every space-word-equals_sign combination
        #     objects_split = re.split(r',?\s(?=[\w-]+=)', c_object)
        #
        #     identifiers = []
        #     id = ""
        #
        #     # Whether to skip this element or not, may occur when irrelevant stuff is found. Is prone to errors or
        #     # overfitting...
        #     skip = False
        #
        #     for i in objects_split:
        #         if i[-1] == "\"" and "=" in i:
        #             if "href" in i:
        #                 url = i[5:][i[5:].rfind("/") + 1:]
        #                 if url == '"#"':  # Assumes that any link with # as href will not lead to a new page
        #                     skip = True
        #                     break
        #                 # getting this in the right format is a pain
        #                 href_string = "contains(@href," + "\"" + url + ") and "
        #                 href_string = href_string.replace("amp;", "")  # Replace rogue amp; with nothing
        #                 identifiers.append(href_string)
        #             else:
        #                 i = i.replace("amp;", "")  # Replace rogue amp; with nothing
        #                 if "src" in i:  # Skip src as it uses the local source and not the webpage source
        #                     continue
        #                 identifiers.append("@" + i + " and ")
        #                 if "id" in i:
        #                     id = "@" + i
        #
        #     if skip:
        #         continue
        #
        #     # First check if we can uniquely find the element by ID (since this is the least error-prone way)
        #     if not id == "":
        #         result = ("//" + objects_split[0][1:] + "[" + id + "]")
        #         try:
        #             items = driver.find_elements_by_xpath(result)
        #             if len(items) == 1:
        #                 item = items[0]
        #         except InvalidSelectorException:
        #             Logger.log("error", "Object with: " + result + " has invalid format; original = " + c_object)
        #             item = None
        #         except NoSuchElementException:
        #             Logger.log("error", "Object with: " + result + " not found")
        #             item = None
        #
        #     if len(identifiers) > 0:
        #         # Otherwise we use the rest of the identifiers
        #         result = ("//" + objects_split[0][1:] + "[")
        #
        #         for i in identifiers:
        #             if "src" in i:  # Skip src as it uses the local source and not the webpage source
        #                 continue
        #             else:
        #                 result += i
        #
        #         if "and" in result:
        #             result = result[:len(result) - 5]
        #
        #         result += "]"
        #     else:
        #         result = ("//" + objects_split[0][1:])
        #
        #     if item is None:
        #         try:
        #             item = driver.find_element_by_xpath(result)
        #         except InvalidSelectorException:
        #             Logger.log("error", "Object with: " + result + " has invalid format; original = " + c_object)
        #             item = None
        #         except NoSuchElementException:
        #             Logger.log("error", "Object with: " + result + " not found")
        #             item = None
        #
        #     if item is not None:
        #         # If we are in a list and we have already seen this item, continue
        #         if visited_check and page_type in self.__visited_items.keys():
        #             if item.id in self.__visited_items[page_type]["ff"]:
        #                 continue
        #             elif multi_page_track and "mt" in self.__visited_items[page_type].keys():
        #                 if objects[j] in self.__visited_items[page_type]["mt"]:
        #                     continue
        #         # If the thread is blacklisted, skip it
        #         if relevancy is not None and relevancy[j] == Relevance.BLACKLISTED:
        #             continue
        #         if relevancy is not None and relevancy[j] == Relevance.IRRELEVANT:
        #             continue
        #         # If the thread is parsed, skip it
        #         if status is not None and status[j] == ThreadStatus.PARSED:
        #             continue
        #
        #         # If it is not yet visited, return it and add it to the visited dict
        #         if page_type in self.__visited_items.keys():
        #             self.__visited_items[page_type]["ff"].append(item.id)
        #             if multi_page_track and "mt" in self.__visited_items[page_type].keys():
        #                 self.__visited_items[page_type]["mt"].append(objects[j])
        #             elif multi_page_track:
        #                 self.__visited_items[page_type]["mt"] = [objects[j]]
        #         else:
        #             self.__visited_items[page_type] = {"ff": [item.id]}
        #             if multi_page_track:
        #                 self.__visited_items[page_type]["mt"] = [objects[j]]
        return object_id.get_selenium_elements(driver)

        # print("I expect here to see a list of elements, the list of sections.")
        # print("Length: " + item.)
        # return item
        #
        # return None

    def possible_train(self):
        """If there is an after_workday_url set, the crawler will train the interpreter again
        """

        if self.__after_workday_url is not None:
            self.__interpreter.start_training_after_workday(self.__after_workday_page, self.__after_workday_url)

    def __close_tab(self, cur_page: ParsedData, driver: TorBrowserDriver):
        """Closes the current tab and returns control to the last still opened tab.

        If there is only one tab open then nothing will happen, the last tab must always explicitly be closed by
        calling driver.quit().

        Parameters
        ---------
        cur_page : ParsedData
            The parsed data which indicate the fields and buttons for the current page
        driver : TorBrowserDriver
            The driver to interact with the browser.
        """
        # Close the current tab and clear the visited items from the dict for this page only
        self.__visited_items.pop(cur_page.page_type, None)
        tab_count = len(driver.window_handles)

        # If the current tab count is exactly 1, we're not going to close this thing. Refresh and return 5 secs later.
        if tab_count == 1:
            loaded = False
            while not loaded:
                try:
                    driver.refresh()
                    loaded = True
                except TimeoutException:
                    CrawlerUtils.wait_tor_browser()
                    pyautogui.hotkey("ctrl", "shift", "l")
                    time.sleep(1)
            time.sleep(5)
            return

        driver.close()

        while len(driver.window_handles) != tab_count - 1:
            time.sleep(1)

        driver.switch_to.window(driver.window_handles[-1])

    def __training_sequence(self, driver: TorBrowserDriver) -> ParsedData:
        """This function will go through the following pages first once the crawler starts:
        log-in page via URL
        home page via URL
        section page via URL
        section page 2 via button
        subsection page via URL (optional)
        subsection page 2 via button (optional)
        thread page via URL
        thread page 2 via button

        Parameters
        ----------
        driver : TorBrowserDriver
            The driver to interact with the browser.

        Returns
        -------
        ParsedData
            ParsedData from the last parsed page of the training
        """
        if self.__parameters.crawling.platform_login != self.__parameters.crawling.platform:
            url_list = [self.__parameters.crawling.platform_login, self.__parameters.crawling.platform,
                        self.__parameters.crawling.platform_section, self.__parameters.crawling.platform_subsection,
                        self.__parameters.crawling.platform_thread]
        else:
            url_list = [self.__parameters.crawling.platform, self.__parameters.crawling.platform_section,
                        self.__parameters.crawling.platform_subsection, self.__parameters.crawling.platform_thread]

        # Throw away all possible None values in the list (if any)
        while True:
            try:
                url_list.remove(None)
            except ValueError:
                break

        while len(url_list) > 0:
            url = url_list.pop(0)  # Get the first URL from the list and remove it from said list
            first_page = True
            find_page_two = False
            back_to_page_one = False
            train = True
            stay_on_page = False
            javascript = ""

            while train:
                if driver.current_url != url:
                    if not stay_on_page:
                        # If we're just beginning, first open the login page.
                        if first_page:
                            self.__navigate_to_page(driver, url=url)
                    else:
                        stay_on_page = False

                # Save the page
                self.__current_page = self.__crawler_utils.save_page(driver.current_url, driver, training=True)
                # Interpret the page and train on it
                if not first_page:
                    parsed_page = self.__interpreter.parse_page(self.__current_page, driver.current_url, driver=driver,
                                                                training=True, reuse_method_identifiers_map=True,
                                                                javascript=javascript)
                else:
                    parsed_page = self.__interpreter.parse_page(self.__current_page, driver.current_url, driver=driver,
                                                                training=True, javascript=javascript)

                # If the page had JS to execute, then the page must be downloaded again and train it.
                if not isinstance(parsed_page, str):

                    # If it is a page potentially containing a navigational item, remember to navigate also in page 2
                    if parsed_page.page_type == PageType.SectionPage or parsed_page.page_type == PageType.SubsectionPage \
                            or parsed_page.page_type == PageType.ThreadPage:
                        if first_page:
                            first_page = False
                            find_page_two = True

                    if parsed_page.page_type == PageType.LoginPage:
                        self.__login(parsed_page, driver)
                        train = False
                        Logger.log("crawler", "Log in successful")

                    time.sleep(2)

                    if back_to_page_one:
                        if parsed_page.prev_page_button is not None:
                            # That shouldn't happen...
                            button = self.__find_elements(parsed_page.prev_page_button,
                                                          driver, False, parsed_page.page_type)[0]
                            if button is not None:
                                self.__navigate_to_page(driver, button=button)
                                find_page_two = False
                                back_to_page_one = False
                            else:
                                break
                        else:
                            break
                    elif find_page_two:
                        if parsed_page.next_page_button is not None:
                            # This may happen in the case there was no specification for a next page button
                            button = self.__find_elements(parsed_page.next_page_button,
                                                          driver, False, parsed_page.page_type)[0]
                            if button is not None:
                                self.__navigate_to_page(driver, button=button)
                                find_page_two = False
                                back_to_page_one = True
                            else:
                                break
                        else:
                            break
                    else:
                        train = False
                        first_page = True
                else:
                    stay_on_page = True
                    javascript = parsed_page

        # Back to front page
        self.__navigate_to_page(driver, url=self.__parameters.crawling.platform)

        # TODO change that. This downloads twice the front page to let self.__craw_page_proc._next_page in __crawling()
        #  (in start_crawling() in crawler_main.py) to begin crawling rather than going for the training_sequence.
        #  I'm not fixing it right now because I don't know what are other possible side effects.

        # the actual page content, also send this to the database
        page = self.__crawler_utils.save_page(driver.current_url, driver)
        self.__current_page = page
        # send the page to the interpreter and return the result
        parsed_page = self.__interpreter.parse_page(page, driver.current_url, driver=driver, training=True)

        return parsed_page

    def __login_sequence(self, driver: TorBrowserDriver) -> t.Tuple[ParsedData, str]:
        """This function will go through the login page when no training is needed:

        Parameters
        ----------
        driver : TorBrowserDriver
            The driver to interact with the browser.

        Returns
        -------
        ParsedData
            ParsedData from the last parsed page of the training
        str
            HTML content of the page.
        """
        # Dev note: This function is very dirty and hardcoded, repeating the same thing over and over. Might need to be
        # properly reworked with methods and stuff.

        # Load the login page
        self.__navigate_to_page(driver, url=self.__parameters.crawling.platform_login)

        # the actual page content, also send this to the database
        page = self.__crawler_utils.save_page(driver.current_url, driver)
        self.__current_page = page

        # send the page to the interpreter and return the result
        parsed_page = self.__interpreter.parse_page(page, driver.current_url, PageType.LoginPage, driver=driver)

        # Check if the page is a login page, if so login and fetch the new page
        self.__login(parsed_page, driver)

        if driver.current_url == self.__parameters.crawling.platform:
            # the actual page content, also send this to the database
            page = self.__crawler_utils.save_page(driver.current_url, driver)
            self.__current_page = page

            page_type = self.__interpreter.determine_page_type(self.__current_page)
            # Executing JS (if any) before interpreting the page
            if self.__interpreter.js_db_struct[page_type] != '':
                driver.execute_script(self.__interpreter.js_db_struct[page_type])
                # TODO this should wait and check if all the (expected) elements in the page are now visible.
                #  I don't know how to achieve this, so there's an arbitrary 20 seconds wait.
                time.sleep(20)

                # the actual page content, also send this to the database
                page = self.__crawler_utils.save_page(driver.current_url, driver)
                self.__current_page = page

            # send the page to the interpreter and return the result
            parsed_page = self.__interpreter.parse_page(page, driver.current_url, PageType.FrontPage)
        else:
            self.__navigate_to_page(driver, url=self.__parameters.crawling.platform)

            # the actual page content, also send this to the database
            page = self.__crawler_utils.save_page(driver.current_url, driver)
            self.__current_page = page

            page_type = self.__interpreter.determine_page_type(self.__current_page)
            # Executing JS (if any) before interpreting the page
            if self.__interpreter.js_db_struct[page_type] != '':
                driver.execute_script(self.__interpreter.js_db_struct[page_type])
                # TODO this should wait and check if all the (expected) elements in the page are now visible
                time.sleep(20)

                # the actual page content, also send this to the database
                page = self.__crawler_utils.save_page(driver.current_url, driver)
                self.__current_page = page

            # send the page to the interpreter and return the result
            parsed_page = self.__interpreter.parse_page(page, driver.current_url)

        return parsed_page, page

    def __generate_xpath(self, child_element: WebElement, current) -> t.Optional[str]:
        """Function generating the XPath of a given element.

        Parameters
        ----------
        child_element : WebElement
            the nested elements that may be within the current element.
        current : str
            the current element's XPath.

        Returns
        -------
        str
            Calculated XPath for the element.
        """

        child_tag = child_element.tag_name
        if child_tag == "html":
            return "/html[1]" + current
        parent_element = child_element.find_element(By.XPATH, "..")
        children_elements = parent_element.find_elements(By.XPATH, "*")
        count = 0
        for children_element in children_elements:
            children_element_tag = children_element.tag_name
            if child_tag == children_element_tag:
                count = count + 1
            if child_element == children_element:
                result = "/" + child_tag
                if count > 1:
                    result = result + "[" + str(count) + "]"
                result = result + current
                return self.__generate_xpath(parent_element, result)
        return None
