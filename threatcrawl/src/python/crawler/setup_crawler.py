"""Setup class for the Crawler module"""
import time
from pathlib import Path

import pyautogui
import pymsgbox
import pyperclip
from selenium.webdriver.common.by import By
from tbselenium.tbdriver import TorBrowserDriver
import os

from crawler.crawler_utils import CrawlerUtils
from trainer.xpath_helper_functions import calculate_xpath
from utils import Logger


class SetupCrawler:
    """The setup_crawler class will run at the start and at the end of the workday.

    At the start of the workday the function `start_browsing` setups the browser before crawling.
    At the end of the workday the function `terminate_browsing` terminates the browser process and closes all other
    programs.

    Attributes
    ----------
    __tbb_path : str
        The path of the Tor browser on the machine.
    __ssl_check : bool
        A boolean representing whether disable all SSL certificates verification in TorBrowser.
    """

    def __init__(self, tbb_path, ssl_check):
        self.__tbb_path = tbb_path
        self.__ssl_check = ssl_check
        pyautogui.FAILSAFE = False

    def start_browser(self, loading_timeout: int, load_images: bool, skip_tokens: bool) -> TorBrowserDriver:
        """Start up the TOR browser and setups selenium.
        
        Parameters
        ----------
        loading_timeout : int
            Timeout in seconds to load a page.
        load_images : bool
            Boolean communicating TorBrowser if to download images or not from any source in the explored pages.
        skip_tokens : bool
            Boolean to skip the acquisition of cloudflare tokens.

        Returns
        -------
        driver : TorBrowserDriver
            The driver which will interact with the pages.
        """
        # Momentarily start the browser to get the profile, disable SSL settings and then close browser
        driver = TorBrowserDriver(self.__tbb_path, tbb_logfile_path=os.devnull)

        profile = driver.profile
        profile.set_preference("dom.webdriver.enabled", False)
        profile.set_preference("useAutomationExtension", False)
        # Disable loading images
        if not load_images:
            profile.set_preference("permissions.default.image", 2)

        # Changing userAgent may play a positive role, but comes at the price of becoming more traceable and I'm not
        # sure at which level. According to panopticlick.eff.org, we lose definitely some anonymity.
        # However, let's test it for now.

        # useragent = UserAgent()
        # profile.set_preference("general.useragent.override", useragent.random)
        # profile.set_preference("privacy.resistFingerprinting", False)

        # caps['proxy'] = {
        #     "httpProxy": proxy,
        #     "ftpProxy": proxy,
        #     "sslProxy": proxy,
        #     "proxyType": "MANUAL"}

        # If ssl check should be disabled, disable it
        if self.__ssl_check is False:
            profile = driver.profile
            profile.accept_untrusted_certs = True
            profile.assume_untrusted_cert_issuer = False

        profile.update_preferences()

        path = profile.path

        os.system("rm -rf /tmp/curprofile")
        os.system("cp -r " + path + " /tmp/curprofile")
        driver.quit()

        time.sleep(1)
        # TODO one day, rather than using extensions to set navigation.webdriver to false at every page load, there is
        #  the possibility of using Firefox CDP. In few words, Selenium Chrome already supports the CDP commands, in
        #  particular Page.addScriptToEvaluateOnNewDocument, invokable with the function execute_cdp
        #  (https://stackoverflow.com/a/59367912/4804285). If Selenium Firefox won't but Firefox will implement it
        #  (https://bugzilla.mozilla.org/show_bug.cgi?id=1597879), then it's possible to open a websocket towards
        #  Firefox devtools (it should be open on port 9222) to get the list of all websockets managing the single pages
        #  and to run the command specified above (details on how to find pages and connect to ws:
        #  https://chromedevtools.github.io/devtools-protocol/).
        #  ______________
        #  python3 -m websockets ws://localhost:49613/devtools/browser/fe6aa961-602d-4767-acfb-2163573fc4bf
        #  then send (single line)     {"id":15, "method":"Page.addScriptToEvaluateOnNewDocument",
        #                              "parameters":{"source": "Object.defineProperty(navigator, 'webdriver',
        #                              { get: () => undefined })"}}
        # Start new instance with the new profile containing the new settings
        driver = TorBrowserDriver(self.__tbb_path, tbb_logfile_path=os.devnull, tbb_profile_path="/tmp/curprofile",
                                  use_custom_profile=True)
        driver.set_page_load_timeout(loading_timeout)  # 10 minutes timeout loading
        # Tampermonkey will open its welcome page. Close it.
        time.sleep(5)

        count = 0
        while True:
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[-1])
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)
                break
            if count > 5:
                break
            time.sleep(2)
            count += 1

        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)

        if not skip_tokens and pymsgbox.confirm("Do you need to add new CloudFlare tokens? If you have already enough "
                                                "from a previous session press 'no'", buttons=["Yes", "No"]) == "Yes":
            self.__prepare_cf_tickets(driver, True)
        else:
            self.__prepare_cf_tickets(driver, False)

        return driver

    def __prepare_cf_tickets(self, driver: TorBrowserDriver, manual_insert: bool):
        """

        Parameters
        ----------
        driver : TorBrowserDriver
            TorBrowser instance.
        manual_insert : bool
            A flag to decide whether the user will provide tickets manually or these will be fetched from a file.

        Returns
        -------

        """
        # Fetching tokens
        commands = []
        cf_tokens_file = str(Path.home()) + "/threatcrawl-cftokens"
        if manual_insert:
            if os.path.exists(cf_tokens_file):
                os.remove(cf_tokens_file)
            with open(cf_tokens_file, 'w') as f:
                while True:
                    cookie = pymsgbox.prompt("Gimme cookies")
                    key = cookie.split(':')[0]
                    value = ':'.join(cookie.split(':')[1:]).replace('\\', '\\\\')[:-1][1:]
                    command = "window.localStorage.setItem('" + key + "', '" + value + "')"
                    commands.append(command)
                    f.writelines([key+"\n", value+"\n"])
                    if pymsgbox.confirm("Yummy! Do you have more?", buttons=["Yes", "No"]) == "No":
                        break
        else:
            # TODO this could be optimized; the crawler termination could be followed from the extraction of the
            #  remaining tickets, while this remains for extra caution if the crawler crashes for some reason.
            try:
                with open(cf_tokens_file, 'r') as f:
                    lines = f.readlines()
                    for key, value in zip(lines[0::2], lines[1::2]):
                        command = "window.localStorage.setItem('" + key + "', '" + value + "')"
                        commands.append(command)
            except FileNotFoundError:
                Logger.log("warning", "CloudFlare token file not found.")

        if len(commands) != 0:
            driver.load_url("about:debugging#/runtime/this-firefox")
            # Finding the button for the plugin
            plugin_xpath = calculate_xpath(driver.find_element_by("//*[text()='Privacy Pass']", find_by=By.XPATH), driver)
            button_xpath = '/'.join(plugin_xpath.split('/')[:-1]) + "/div[1]/button"
            driver.find_element_by(button_xpath, find_by=By.XPATH).click()

            time.sleep(1)

            CrawlerUtils.wait_tor_browser()
            driver.switch_to.window(driver.window_handles[-1])

            # Typing cookies in localStorage
            for command in commands:
                pyperclip.copy(command)
                time.sleep(1)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(1)
                pyautogui.hotkey('enter')

            time.sleep(1)
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

    def terminate_browser(self, driver):
        """terminates the TOR browser process and selenium.

        Parameters
        ----------
        driver : TorBrowserDriver
            The driver to terminate.

        Raises
        ----------
        ValueError
            The TOR Browser is not running.
        """

        if driver is None:
            raise ValueError("No driver is defined")
        else:
            driver.quit()
