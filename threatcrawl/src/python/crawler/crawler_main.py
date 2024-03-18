"""Main class for the Crawler module"""
import datetime
import sys
import threading

import pytz

from config import Configuration
from database import DataAPI
from .setup_crawler import SetupCrawler
from .crawler_page_processing import CrawlerPageProcessing
from .crawler_time_controller import CrawlerTimeController
import time
import random
import asyncio
from enums import Relevance, PageType
from interpreter import ThreadData, ParsedData
from cli.cli import CLI
from datetime import timedelta
from utils import Logger


class CrawlerMain:
    """Main class for the Crawler module

    This class will execute the general crawling behaviour. It will have functions to start, terminate and pause the
    crawling. Furthermore, parameters will be stored alongside the parsed data of the current page (note that this
    is for short-term use, long term use will be stored separately in the database). Finally, there will be a function
    to generate the status message for the CLI module, which is based upon the parsed data and the given parameters.

    Parameters
    ----------
    data_api: DataAPI
        An instance of the DataAPI class, used to access the database
    parameters : Configurations
        The parameters of the crawler.
    craw_time_contr : CrawlerTimeController
        The time controller needed to generate the schedule for the crawler execution.
    pause : threading.Event
        A lock to pause the execution of the crawler.
    terminate : threading.Event
        A lock to terminate the execution of the crawler.
    resume : threading.Condition
        A lock to resume the execution of the crawler.
    cli : CLI
        The CLI object that the user interacts with
    solved : threading.Condition
        A lock to resume the execution of the crawler upon CAPTCHA resolution.
    cli_test : bool
        If true, only the options necessary for the CLI test (notify badly formatted page), will be run. By default,
        this value is false

    Attributes
    ----------
    __data_api: DataAPI
        An instance of the DataAPI class, used to access the database
    __parameters : Configuration
        The parameters of the crawler.
    __parsed_page : ParsedData
        The parsed data of the last fetched page.
    __craw_setup : SetupCrawler
        The part of the crawler that will handle starting the crawler.
    __craw_time_contr : CrawlerTimeController
        The part of the crawler that will manage the breaks and interrupts.
    __craw_page_proc : CrawlerPageProcessing
        The part of the crawler that will handle fetching the pages.
    __driver : TorBrowserDriver
        The crawler instance that will be used to interact with web pages
    __pause_event : threading.Event
        A lock to pause the execution of the crawler.
    __terminate_event : threading.Event
        A lock to terminate the execution of the crawler.
    __resume_condition : threading.Condition
        A lock to resume the execution of the crawler.
    __cli : CLI
        The CLI that the user communicates through
    __skip_tokens : bool
        A boolean to tell if to skip asking for new cloudflare tokens.
    """

    def __init__(self, data_api: DataAPI, parameters: Configuration, craw_time_contr: CrawlerTimeController,
                 pause: threading.Event, terminate: threading.Event, resume: threading.Condition, cli: CLI,
                 solved: threading.Condition, skip_tokens: bool, cli_test: bool = False):
        if not cli_test:
            self.__data_api = data_api
            self.__parameters = parameters
            self.__parsed_page = None
            self.__craw_setup = SetupCrawler(parameters.crawling.tor_path, parameters.preferences["sslCheck"])
            self.__craw_time_contr = craw_time_contr
            self.__craw_page_proc = CrawlerPageProcessing(self.__data_api, parameters, solved)
            self.__driver = None
            self.__pause_event = pause
            self.__terminate_event = terminate
            self.__resume_condition = resume
            self.__skip_tokens = skip_tokens
        self.__cli = cli

    def set_parameters(self, parameters: Configuration):
        """Sets the parameters of the Crawler to the given parameters.

        This will change the local variable `__parameters` to be up-to-date with the newly supplied parameters

        Parameters
        ----------
        parameters : Configurations
            The new parameters to be stored.

        Raises
        ------
        BadArgumentException
            The given argument for the parameters is invalid (not of proper type for example)

        """

        if parameters is None:
            raise ValueError("set_parameters does not take None values")

        self.__parameters = parameters

    def get_parameters(self) -> Configuration:
        """Gets the current `__parameters` variable of the Crawler.

        Returns
        -------
        parameters : Configurations
            The current parameters of the crawler.

        """

        return self.__parameters

    def start_crawling(self):
        """Starts the actual crawling of the module, to be called from the CLI module.

        This will initiate the crawling behaviour of the module, starting _crawling(). This will mean that the crawler
        is working on retrieving pages until it is either terminated, paused or encounters an error. Furthermore, the
        crawler will adhere to the specified workday and will terminate when the workday reaches its end.

        """

        Logger.log("state", "THREAT/crawl is starting")

        self.generate_cli_status()

        # if there is no driver yet, initialize one and load the first page
        if self.__driver is None:

            # Check if THREAT/crawl should wait for until workday has started
            break_interrupt_duration = self.__craw_time_contr.check_break_interrupt()
            if break_interrupt_duration > 0:
                resume_date = (datetime.datetime.now() + datetime.timedelta(
                    seconds=break_interrupt_duration)).replace(microsecond=0)
                Logger.log("state", "Workday has not yet started. Execution will resume at " + str(resume_date) +
                           " local time.")
                with self.__resume_condition:
                    self.__resume_condition.wait(timeout=break_interrupt_duration)
                # for step in track(range(int(break_interrupt_duration)), description="Starting workday"):
                #     time.sleep(1)
                Logger.log("state", "THREAT/crawl is starting crawling process")

            self.__driver = self.__craw_setup.start_browser(self.__parameters.crawling.timeout,
                                                            self.__parameters.preferences["downloadImages"],
                                                            self.__skip_tokens)

            # Load the url of the main page, this will be retrieved from parameters later
            self.__parsed_page = self.__craw_page_proc.next_page(self.__driver, None)

            # After parsing the page, if it is badly formatted, notify the user through the CLI
            if self.__parsed_page is not None:
                self.check_badly_formatted(self.__parsed_page)

        # start the actual crawling
        asyncio.run(self.__crawling())

    def _pause_crawling(self):
        """Pauses the crawling of the module, to be called form the CLI.

        This will pause the crawler. Pausing the crawler means that the current state of the crawler is maintained, so
        when it is started again it will continue like nothing has ever happened. This is the main difference with
        terminating the crawler where the state is not saved.
        """

        while self.__pause_event.is_set():
            time.sleep(1)

        self.start_crawling()

    async def _terminate_crawling(self):
        """terminates the crawling of the module, to be called form the CLI.

        This will terminate the crawler. terminating the crawler means that the current state of the crawler is not
        maintained, so when it is started again it will have to start like it is started from scratch. This is the main
        difference with pausing the crawler where the state is saved.

        Raises
        ----------
        BrowserNotFoundException
            The TOR Browser is not running.
        """

        # Re-train badly formatted first if needed
        self.__craw_page_proc.possible_train()

        # Then terminate the crawler
        self.__craw_setup.terminate_browser(self.__driver)

        # Then terminate the GUI
        # async with websockets.connect("ws://localhost:8080") as websocket:
        #     message = {
        #         'action': "terminate"
        #     }
        #     await websocket.send(to_json(message))
        #     await websocket.close()

        sys.exit(0)

    def generate_cli_status(self):
        """Generates the status of the crawler to be printed in the CLI module.

        This will use the data that is in the `__parameters` variable, data that is in the `parsed_page` variable and
        possibly data that is retrieved from the CrawlerTimeController class about the schedule. The date will be
        formatted in such a way that it is directly able to be printed in a CLI.

        Statics include:
            Start time of workday
            End time of workday
            ETA
            Platform name
            Thread name
            Max thread age
            Max thread length
            Link follow policy
            [Could] Reading speed range
            [Could] Start time of next interruption
            [Could] Start time of next break
            [Could] Timezone
            [Could] Nr. of web pages
            [Could] Resources (CPU, memory, storage)

        Returns
        -------
        String
            The formatted status of the crawler to be printed in the CLI containing at least all the required stats.
        """
        break_queue = self.__craw_time_contr.get_break_schedule()
        interrupt_queue = self.__craw_time_contr.get_interrupt_schedule()
        interrupt_queue.reverse()

        for times in break_queue.queue:
            start_time = times[0].astimezone(pytz.timezone(self.__parameters.workday.timezone)).strftime(
                "%d/%m/%Y %H:%M:%S")
            end_time = (times[0].astimezone(pytz.timezone(self.__parameters.workday.timezone))
                        + timedelta(seconds=times[1])).strftime("%d/%m/%Y %H:%M:%S")
            Logger.log("schedule", "Break schedule: " + str(start_time) + " --- " + str(end_time) + " in " +
                       self.__parameters.workday.timezone + " time")

        for times in interrupt_queue:
            start_time = times[0].astimezone(pytz.timezone(self.__parameters.workday.timezone)).strftime(
                "%d/%m/%Y %H:%M:%S")
            end_time = (times[0].astimezone(pytz.timezone(self.__parameters.workday.timezone))
                        + timedelta(seconds=times[1])).strftime("%d/%m/%Y %H:%M:%S")
            Logger.log("schedule", "Interrupt schedule: " + str(start_time) + " --- " + str(end_time) + " in " +
                       self.__parameters.workday.timezone + " time")

        Logger.log("schedule", "ETA end of the workday: " + str(timedelta(seconds=self.__craw_time_contr.get_ETA())))
        Logger.log("schedule", "Variance time between interruptions: " +
                   str(self.__parameters.workday.time_btw_interrupts_dev))

    def check_badly_formatted(self, parsed_page: ParsedData):
        """Checks whether a badly formatted page has been encountered

        If a badly formatted page has been encountered, the crawler notifies the user through the CLI that this
        occurred. This method is mainly used for testing purposes.
        """
        if parsed_page.is_badly_formatted:
            self.__cli.notify_bad_formatted_page()

    def __save_parsed_data(self):
        """Prepares a new document to save in the database.
        """

        parsed_page = self.__parsed_page

        document = parsed_page.to_database_format()

        resource_identifiers = [
            'next_page_button',
            'prev_page_button',
            'section_button',
            'home_button',
            'captcha_location']

        for identifier in resource_identifiers:
            if identifier in document and document[identifier] is not None:
                document[identifier] = self.__data_api['resource identifier'].insert(document[identifier]).exec()

        self.__data_api['platform structures'].insert(document).exec()

    async def __crawling(self):
        """The heart of the crawler, where the crawling of pages will be coordinated.

        This method will coordinate all the processing of the pages, threads, platforms. It will do so mainly by
        repeatedly calling next_page from the CrawlerPageProcessing class to retrieve the next, parsed, page. After
        retrieving a parsed page the crawler will check for how long it needs to pause to simulate reading
        and check if there are any planned interrupts or breaks.

        Raises
        ------
        NoMorePagesException
            There are no more pages to be found hence the crawler cannot continue parsing more pages.
        """

        # For now just fetch a new page 6 times, of course in the future this will be determined
        while True:
            # Go to the next page, use data from current page
            self.__parsed_page = self.__craw_page_proc.next_page(self.__driver, self.__parsed_page)

            # If the page is badly formatted, notify the user through the CLI
            self.check_badly_formatted(self.__parsed_page)

            self.generate_cli_status()

            # Pretend to read the page
            fetch_delay = self.__compute_fetch_delay()
            Logger.log("crawler", "Fetch delay: " + str(fetch_delay))
            # for step in track(range(fetch_delay), description="Reading page"):
            #     time.sleep(1)
            with self.__resume_condition:
                self.__resume_condition.wait(timeout=fetch_delay)

            self.__craw_page_proc.interact_with_page(driver=self.__driver, cur_page=self.__parsed_page)

            # Check if a break is planned
            break_interrupt_duration = self.__craw_time_contr.check_break_interrupt()
            if break_interrupt_duration > 0:
                resume_date = (datetime.datetime.now() + datetime.timedelta(
                    seconds=break_interrupt_duration)).replace(microsecond=0)
                Logger.log("state", "THREAT/crawl is in a scheduled break or interrupt. Execution will resume at " +
                           str(resume_date) + " local time.")
                # for step in track(range(int(break_interrupt_duration)), description="Break/Interrupt"):
                #     time.sleep(1)
                with self.__resume_condition:
                    self.__resume_condition.wait(timeout=break_interrupt_duration)

            # The crawler is being paused
            just_paused = True
            while self.__pause_event.is_set():  # or self.__terminate_event.is_set():
                if just_paused:
                    Logger.log("state", "THREAT/crawl is paused")
                    just_paused = False
                time.sleep(2)
                if self.__terminate_event.is_set():
                    self.__shutdown()

            if self.__terminate_event.is_set():
                self.__shutdown()

            # If the crawler is in a page different from a ThreadPage, and it is time to go to sleep, then terminate.
            if self.__parsed_page.page_type is not PageType.ThreadPage:
                if self.__craw_time_contr.check_end_time():
                    await self._terminate_crawling()

    def __compute_fetch_delay(self) -> int:
        """Compute the fetch delay of a page to mimic reading behaviour.

        Based on the reading speed that is set in the parameters, this function will compute the time it would take an
        average human to read the parsed data from the retrieved webpage. If no page is yet stored here (because
        no page has been parsed yet), the result will be 0.

        Returns
        -------
        int
            The amount of time it would take an average human to read the page in parsed_page in seconds. 0 if there is
            not yet a parsed page stored.
        """

        # If there is no parsed page return 0
        if self.__parsed_page is None:
            return 0

        # If the parsed page is a thread page, use page relevancy to determine how long the fetch delay is
        if isinstance(self.__parsed_page, ThreadData):
            # If the parsed page is relevant, calculate amount of time needed to read this page
            if self.__parsed_page.page_relevancy == Relevance.RELEVANT:
                # Set reading speed to be a random number inside the reading speed range
                reading_speed = random.randint(self.__parameters.crawling.reading_speed_range[0],
                                               self.__parameters.crawling.reading_speed_range[1])
                if self.__parsed_page.nrof_words_on_page < 0:
                    Logger.log("error", "Number of words on page is negative")
                    return random.randint(self.__parameters.crawling.delay[0], self.__parameters.crawling.delay[1])
                return int((self.__parsed_page.nrof_words_on_page / reading_speed) * 60)

        # if the parsed page is not a thread page or is irrelevant, return a number in the normal delay range
        return random.randint(self.__parameters.crawling.delay[0], self.__parameters.crawling.delay[1])

    def __shutdown(self):
        """Terminates the crawling process.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop().run_until_complete(self._terminate_crawling())
        Logger.log("state", "THREAT/crawl is terminated")
