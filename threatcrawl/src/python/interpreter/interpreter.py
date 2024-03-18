""" Interpreter class to parse web pages from the crawler. """
import time
from datetime import datetime
from datetime import timedelta
from copy import deepcopy

import pyautogui
import pymsgbox
import threading

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from tbselenium.tbdriver import TorBrowserDriver

from crawler.captcha_solver import CaptchaSolver
from crawler.crawler_utils import CrawlerUtils
from .interpreter_kw import InterpreterKW
from .interpreter_nav import InterpreterNav
from .interpreter_data import InterpreterData
from .interpreter_captcha import InterpreterCAPTCHA
from .interpreter_verifier import InterpreterVerifier
from .thread_data import ThreadData
from .section_data import SectionData
from .interpreter_utils import strip_tags
from .need_training_error import NeedTrainingError
from .parsed_data import ParsedData
from config.configuration import Configuration
from config.configuration import Crawling
from config.configuration import Workday
from enums import PageType, StructuralElement, Relevance, ThreadStatus, DataElement, NavigationalElement
from tld import get_tld
from trainer import ResourceIdentifier, Trainer
from trainer.xpath import XPath
from trainer.xpath_except import XPathExcept
from trainer.html_class import HTMLClass
from trainer.trainer import convert_name_to_structural_element
from trainer.page import Page
from database.querying import QueryBuilder
from database import DataAPI
from utils import Logger
import typing as t
import pytz


class Interpreter:
    """ Interpreter class to parse web pages from the crawler.

    The Interpreter class is the connection between the individual interpreters which take care of the different parts
    of the web page that need to be identified, like the navigational elements and the relevant data in the thread and
    the rest of the system. This class connects to the database and the crawling system. It puts interpreted data into
    the database and feeds information into the crawler so that it can make informed decisions on where to go next.

    Parameters
    ----------
    data_api : DataAPI
        DataAPI instance, used to access the database
    config : Configuration
        Configuration object that houses the configuration.
    download_path : str
        String representing the download path for TorBrowser.
    solved : threading.Condition
        Lock used to communicate when a CAPTCHA has been detected or solved.
    need_training : bool, optional
        Whether training is needed. Should only be passed in when testing! Default is true.

    Attributes
    ---------
    __inter_data : InterpreterData
        The interpreter for the data.
    __inter_kw : InterpreterKW
        The interpreter for the keywords.
    __inter_nav: InterpreterNav
        The interpreter for the navigational elements.
    __inter_cap : InterpreterCAPTCHA
        The interpreter for the CAPTCHAs.
    __inter_ver : InterpreterVerifier
        The interpreter that verifies that the trained structure works.
    __data_api : DataAPI
        DataAPI instance, used to access the database
    __config : Configuration
        Configuration object that houses the configuration.
    __badly_formatted_count : int
        How often a page has been marked as badly formatted.
    __missing_nav_count : int
        How often a page has been missing a navigational element.
    __first_two_hours : bool
        Flag to check if we're in the first two hours of crawler execution. Needed to verify if there are interpreter
        errors and how many of them during this time frame.
    __captcha_solver : CaptchaSolver
        Instance of CaptchaSolver to identify CAPTCHAs and ask the user to solve them.
    __helpers : CrawlerUtils
        Helper of crawler and interpreter.
    __download_path : str
        Path where pages are downloaded.
    js_db_struct : dict<PageType, str>
        Dictionary containing the possible JavaScript to execute in each PageType before interacting with the page.
    training_after_workday : bool
        Whether a training session is needed after the workday has ended.
    method_identifiers_map : dict<ResourceIdentifier, int>
        Dictionary keeping track of the AnalyzerMethod used to obtain the identifier for a given ResourceIdentifier
    __need_training : bool
        Whether the platform structure is still missing some things or whether it is complete. True when in need of
        training, False otherwise.
    __thread_missing : bool
        Whether the thread page is in the platform structure.
    __missing_struct : bool
        Whether the platform structure is missing/empty or stored in the database. True if missing/empty, False if
        stored in the database.

    Raises
    -----
    ValueError
        If the retrieved structure is not and cannot be converted to a dictionary of <PageType, <StructuralElement,
        ResourceIdentifier>> pairs.
    """

    def __init__(self, data_api: DataAPI, config: Configuration, download_path: str, solved: threading.Condition,
                 need_training: bool = True):
        structure = {}
        self.__verify_config(config)

        if not isinstance(data_api, DataAPI):
            raise ValueError("No connection to database found!")

        self.__inter_data = InterpreterData(structure)
        self.__inter_nav = InterpreterNav(structure)
        self.__inter_cap = InterpreterCAPTCHA(structure)
        self.__inter_ver = InterpreterVerifier(structure)

        self.__data_api = data_api
        self.__config = config
        self.__inter_kw = InterpreterKW()
        self.__badly_formatted_count = 0
        self.__missing_nav_count = 0
        self.__first_two_hours = True
        self.__captcha_solver = CaptchaSolver(solved)
        self.__helpers = CrawlerUtils()
        self.__download_path = download_path
        self.js_db_struct = {}

        self.training_after_workday = False
        self.method_identifiers_map = {}

        # Always needs training to confirm existing platform structure, or create new one. Only override for tests!
        self.__need_training = need_training

        for p_type in PageType:
            self.js_db_struct[p_type] = ''

        if self.__need_training:
            self.__thread_missing = True
            self.__missing_struct = True

        platform_name = get_tld(config.crawling.platform, as_object=True).parsed_url.netloc
        Logger.log("interpreter", "Platform name: {}".format(platform_name))
        platform = self.__find_or_insert('platforms', {'url': config.crawling.platform},
                                         {'url': config.crawling.platform, 'name': platform_name})

        struct = structure
        result = self.__data_api["resource identifier"].find({'platform_url': platform_name}).exec()

        if result:
            db_struct = {}
            for entry in result:
                p_type = PageType[entry['page_type']["enum_value"]]
                page_struct = {}
                for key, value in entry['structural_elements'].items():
                    try:
                        struct_elm = convert_name_to_structural_element(key)
                    except KeyError:
                        Logger.log("interpreter", "Could not understand key in db. Need to retrain")
                        page_struct = {}
                        break

                    date_format = value['date_format']
                    if value['identifier_type'] == "XPath":
                        xpath = value['identifier']
                        page_struct[struct_elm] = XPath(xpath, date_format=date_format)
                    if value['identifier_type'] == "HTMLClass":
                        html_class = value['identifier']
                        page_struct[struct_elm] = HTMLClass(html_class, date_format=date_format)
                    if value['identifier_type'] == "XPathExcept":
                        x_path_use = value['identifier']['x_path_use']
                        x_path_remove = value['identifier']['x_path_remove']
                        page_struct[struct_elm] = XPathExcept(XPath(x_path_use), XPath(x_path_remove),
                                                              date_format=date_format)
                if not page_struct:
                    # If no structure is added in the dict, structure is improperly saved so abort and retrain
                    break
                db_struct[p_type] = page_struct
                self.js_db_struct[p_type] = entry['javascript']
            struct = db_struct

        self.__platform_id = platform['_id']
        self.__confirmed = {}

        if struct:
            self.__update_structure(struct, config)
            if PageType.FrontPage in self.__structure.keys() and PageType.SectionPage in self.__structure.keys() and \
                    PageType.ThreadPage in self.__structure.keys():
                self.__missing_struct = False
            else:
                self.__missing_struct = True

            # If no need to do training, set confirmed accordingly
            for key in self.__structure.keys():
                self.__confirmed[key] = not need_training
        else:
            self.__structure = struct

    def parse_page(self, page: str, url: str, page_type: PageType = None, driver: TorBrowserDriver = None,
                   training: bool = False, reuse_method_identifiers_map: bool = False, javascript: str = '',
                   new_thread: bool = False) -> t.Union[ParsedData, str]:  # This is rather bad from a sw eng perspective.
        # These two data types are very different.
        """Start the parsing process of the web page.

        This function starts the parsing process of the web page, where the Interpreter makes use of the individual
        interpreters to identify the relevant data and elements.

        Parameters
        ---------
        page : str
            The web page to parse.
        url : str
            The URL of the page to parse.
        page_type : PageType
            The type of the page to parse.
        driver : TorBrowserDriver
            The driver puppeteering the tor browser session.
        training : bool
            If the current page is a training page or not.
        reuse_method_identifiers_map : bool
            If the method_identifiers_map should be preserved or reinitialized to empty.
        javascript : str
            The JavaScript obtained from the frontend to execute before interacting with the current page.
        new_thread : bool
            Whether this is a new thread and parsing/saving should be interrupted in favor of reaching the first page
            of the thread first.

        Returns
        -------
        Union[ParsedData, str]
            All the relevant information needed to let the crawler make a decision on whether to continue crawling the
            current thread or to find a new thread, how long the crawler should wait before fetching a new web page and
            the locations of the navigational elements.

        Raises
        ------
        RuntimeError
            If one of the subinterpreters could not complete parsing. The extracted data is therefore unreliable and
            could not be returned.
        """
        # Check whether we are still in the first half an hour of crawling
        workday_start = self.__config.workday.start_time

        # This is used for verifying whether there are too many errors just right away, suggesting errors in the
        # training or updates in the structure.
        if self.__first_two_hours and datetime.now().astimezone(pytz.timezone(self.__config.workday.timezone)) > \
                workday_start + timedelta(hours=2):
            self.__first_two_hours = False

        # First and foremost, any CAPTCHAs here?
        self.__inter_cap.parse_page(page)

        while self.__inter_cap.captcha_full_page:
            self.__captcha_solver.solve_captcha(self.__inter_cap.captcha_type)
            self.__helpers.wait_tor_browser()
            page = self.__helpers.save_page(driver.current_url, driver)

            cap_parsed = self.__inter_cap.parse_page(page)

        # If we're training, solving captchas at this stage is pointless, as we refresh the page to verify that
        # identifiers are stable. This has to happen in self.__start_training here in interpreter.py
        if not training:
            if self.__inter_cap.captcha_on_page and not self.__inter_cap.captcha_full_page:
                self.__captcha_solver.solve_captcha(self.__inter_cap.captcha_type)
                self.__helpers.wait_tor_browser()

        # If structure is empty dict, start training
        is_train_page = False  # Whether this page is used for training or not
        # reuse_method_identifiers_map is used as marker for the page 2 and back to 1 in threads to keep trace of and
        # use the method_identifiers_map.
        if self.__need_training or reuse_method_identifiers_map:
            # If there was JS to execute, then communicate that it was not a training yet to the training_sequence.
            page_structure = self.__start_training(page, url, driver=driver, is_page_two=reuse_method_identifiers_map,
                                                   javascript=javascript)
            if isinstance(page_structure, str):
                return page_structure
            else:
                is_train_page = True

        # Determine page type - I don't like this method at all.
        if page_type is None:
            page_type = self.__determine_page_type(page)
            Logger.log("type", page_type.name)

        # Get parsing status from each of the individual interpreters (except kw)
        data_parsed = self.__inter_data.parse_page(page, page_type, driver)
        nav_parsed = self.__inter_nav.parse_page(page_type)

        if page_type == PageType.ThreadPage:
            parsed_data = ThreadData(page_type)
            # If we're opening a new thread and there's a thread first page button, then we're on the wrong position of
            # the thread, so reset it first. I check if this button actually exists, so we can avoid to save the page.
            if new_thread and self.__inter_nav.first_thread_page_button is not None:
                try:
                    driver.find_element(By.XPATH, self.__inter_nav.first_thread_page_button.x_path)
                    parsed_data.first_thread_page_button = self.__inter_nav.first_thread_page_button
                    parsed_data.page_relevancy = Relevance.RELEVANT
                    return parsed_data
                except NoSuchElementException:
                    pass
        elif isinstance(page_type, PageType):
            parsed_data = SectionData(page_type)
        else:
            Logger.log("interpreter", "Could not determine page type, need more training!")
            self.__need_training = True
            return SectionData(PageType.FrontPage)

        if not data_parsed or not nav_parsed:
            raise RuntimeError("An unknown error occurred during page parsing :(")

        # Get data from the data interpreter and put it in the correct ParsedData subclass
        parsed_data.nrof_words_on_page = self.__inter_data.nrof_words

        # Initialise variables just to be sure nothing breaks down
        authors_user_names = None
        authors_nrof_posts = None
        authors_popularity = None
        registration_dates = None

        thread_section = None
        posts_dates = None

        if page_type == PageType.ThreadPage:
            try:
                parsed_data.nrof_posts_current_thread = self.__inter_data.authors_nrof_posts
            except ValueError:
                parsed_data.nrof_posts_current_thread = -1
                Logger.log("interpreter", "Could not determine nrof posts in this thread.")
            try:
                parsed_data.thread_age = self.__inter_data.thread_age
            except ValueError:
                parsed_data.thread_age = None
                Logger.log("interpreter", "Could not determine thread age.")
            try:
                parsed_data.is_thread_complete = self.__inter_data.is_thread_complete
            except ValueError:
                parsed_data.is_thread_complete = False

            if self.__inter_nav.prev_page_button is None and self.__inter_nav.next_page_button is None:
                parsed_data.is_thread_complete = True

            # Get the data for the database exclusively
            try:
                authors_user_names = self.__inter_data.authors_usernames
            except ValueError:
                authors_user_names = None
                Logger.log("interpreter", "Could not find author usernames.")
            try:
                authors_nrof_posts = self.__inter_data.authors_nrof_posts
            except ValueError:
                authors_nrof_posts = None
                Logger.log("interpreter", "Could not find author nrof posts.")
            try:
                authors_popularity = self.__inter_data.authors_popularity
            except ValueError:
                authors_popularity = None
                Logger.log("interpreter", "Could not find author popularity.")
            try:
                registration_dates = self.__inter_data.authors_registration_date
            except ValueError:
                registration_dates = None
                Logger.log("interpreter", "Could not find registration date.")

            try:
                thread_title = self.__inter_data.thread_title
            except ValueError:
                thread_title = None
                Logger.log("interpreter", "Could not find thread title.")
            try:
                thread_section = self.__inter_data.thread_section
            except ValueError:
                thread_section = None
                Logger.log("interpreter", "Could not find thread section.")
            try:
                posts_dates = self.__inter_data.posts_dates
            except ValueError:
                posts_dates = None
                Logger.log("interpreter", "Could not find post dates.")
            try:
                posts_contents = self.__inter_data.posts_contents
            except ValueError:
                posts_contents = None
                Logger.log("interpreter", "Could not find post contents.")

            try:
                parsed_data.section_button = self.__structure[page_type][DataElement.ThreadSection]
            except KeyError:
                parsed_data.section_button = None
                Logger.log("interpreter", "Could not find section button.")

            # Setting certain variables to None to stop python from complaining and ensuring nothing breaks down
            threads = None

        else:
            thread_list = self.__inter_data.thread_list
            section_list = self.__inter_data.section_list
            subsection_list = self.__inter_data.subsection_list

            threads = self.__set_section_button(thread_list, section_list, subsection_list, page, parsed_data)

            # Setting certain variables to None to stop python from complaining and ensuring nothing breaks down
            thread_title = None
            posts_contents = None

        # Get data from the navigational interpreter and put it in ParsedData
        try:
            parsed_data.next_page_button = self.__inter_nav.next_page_button
        except ValueError:
            parsed_data.next_page_button = None
            Logger.log("interpreter", "Could not find next page button.")
        try:
            parsed_data.prev_page_button = self.__inter_nav.prev_page_button
        except ValueError:
            parsed_data.prev_page_button = None
            Logger.log("interpreter", "Could not find previous page button.")
        try:
            parsed_data.home_button = self.__inter_nav.home_button
        except ValueError:
            parsed_data.home_button = None
            Logger.log("interpreter", "Could not find home button.")
        try:
            parsed_data.login_button = self.__inter_nav.login_button
        except ValueError:
            parsed_data.login_button = None
            Logger.log("interpreter", "Could not find login button.")
        try:
            parsed_data.goto_login_button = self.__inter_nav.goto_login_button
        except ValueError:
            parsed_data.goto_login_button = None
            Logger.log("interpreter", "Could not find goto login button.")
        try:
            parsed_data.first_thread_page_button = self.__inter_nav.first_thread_page_button
        except ValueError:
            Logger.log("interpreter", "Could not find first thread page button.")
        try:
            parsed_data.username_field = self.__inter_nav.login_username
        except ValueError:
            parsed_data.username_field = None
            Logger.log("interpreter", "Could not find username field.")
        try:
            parsed_data.password_field = self.__inter_nav.login_password
        except ValueError:
            parsed_data.password_field = None
            Logger.log("interpreter", "Could not find password field.")

        # Determine whether a page is truly badly formatted or whether it is expected to miss certain elements.
        if self.__inter_nav.is_badly_formatted:
            self.__determine_badly_formatted(parsed_data)

            if self.__inter_nav.is_badly_formatted:
                # It is verified that the page is truly badly formatted, so mark it and continue execution
                self.__badly_formatted_count += 1
                self.__missing_nav_count += 1
                parsed_data.is_badly_formatted = True
            else:
                parsed_data.is_badly_formatted = False
        else:
            parsed_data.is_badly_formatted = False

        # Get data from the keyword interpreter and put it in ParsedData, if needed.
        if page_type == PageType.ThreadPage:
            self.__inter_kw.parse_page(None, thread_title, posts_contents)
        elif threads is not None:  # Being Section page or Subsection page with threads
            self.__inter_kw.parse_page(threads, None, None)

        if page_type == PageType.ThreadPage:
            parsed_data.page_relevancy = self.__inter_kw.page_relevancy
        elif page_type == PageType.SectionPage or page_type == PageType.SubsectionPage:
            parsed_data.thread_relevancy = self.__inter_kw.threads_relevancy
        else:
            parsed_data.page_relevancy = None
            parsed_data.thread_relevancy = None

        if page_type == PageType.ThreadPage and not is_train_page:
            # I'm not sure why the DB should say from a previously saved page whether this is still relevant or not.
            db_relevancy = None
            # Store data in the database, if it is complete
            if not self.__inter_data.is_data_complete:
                self.__badly_formatted_count += 1
                msg = "Not all data from the interpreter can be stored because the data is not complete."

                if thread_title is not None:
                    msg += " Still saving the thread to avoid breakdowns/loops further down the line."
                    db_relevancy = self.__store_data(authors_user_names, authors_nrof_posts, authors_popularity,
                                                     registration_dates, thread_title, thread_section, posts_dates,
                                                     posts_contents, parsed_data.page_relevancy,
                                                     self.__inter_data.post_count)
                else:
                    msg += " Cannot store anything because the thread title is missing. In theory crawler should "
                    msg += "not get stuck in a loop... "
                Logger.log("interpreter", msg)
            else:
                db_relevancy = self.__store_data(authors_user_names, authors_nrof_posts, authors_popularity,
                                                 registration_dates, thread_title, thread_section, posts_dates,
                                                 posts_contents, parsed_data.page_relevancy,
                                                 # thread_age, authors_email,
                                                 self.__inter_data.post_count)

            # Set relevancy got from db if not on a first page. Because it inserts a record on the first page it
            # does not overwrite it with an empty or different relevancy.
            if db_relevancy is not None:
                parsed_data.page_relevancy = db_relevancy

        self.__handle_badly_formatted(url, parsed_data)

        # Get data from the CAPTCHA interpreter and put it in ParsedData, if needed.
        try:
            parsed_data.captcha_on_page = self.__inter_cap.captcha_on_page
        except ValueError:
            parsed_data.captcha_on_page = False
            Logger.log("interpreter", "Could not determine whether a captcha is present or not.")
        try:
            parsed_data.its_a_captcha_page = self.__inter_cap.captcha_full_page
        except ValueError:
            parsed_data.its_a_captcha_page = False

        if parsed_data.captcha_on_page:
            parsed_data.captcha_type = self.__inter_cap.captcha_type
        else:
            parsed_data.captcha_type = None

        # If not withing the first half an hour and the page is formatted correctly, reset badly formatted trackers
        if not self.__first_two_hours and not parsed_data.is_badly_formatted:
            self.__badly_formatted_count = 0
            self.__missing_nav_count = 0

        return parsed_data

    def determine_page_type(self, page: str) -> PageType:
        """Determine the page type based on the HTML of the page and the saved platform structure.

        Parameters
        ----------
        page : str
            HTML of the page for which the PageType must be determined.

        Returns
        -------
        PageType
            Type of the page.

        Raises
        ------
        NeedTrainingError
            If more training is needed this error is raised, as the page type cannot be reliably determined.
        """

        if self.__need_training:
            raise NeedTrainingError()
        else:
            return self.__determine_page_type(page)

    def __update_structure(self, struct: t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]],
                           config: Configuration):
        """Updates the platform structure for this instance and all subinterpreters

        Raises
        ------
        ValueError
            If the given platform structure is not a proper platform structure.
        """
        self.__structure = struct
        if not self.__verify_structure():
            Logger.log("interpreter", "Structure is not a proper one. Needs retraining!")

        if self.__inter_data is None:
            self.__inter_data = InterpreterData(struct)
        else:
            self.__inter_data.structure = struct
        if self.__inter_nav is None:
            self.__inter_nav = InterpreterNav(struct)
        else:
            self.__inter_nav.structure = struct
        if self.__inter_cap is None:
            self.__inter_cap = InterpreterCAPTCHA(struct)
        else:
            self.__inter_cap.structure = struct
        if self.__inter_ver is None:
            self.__inter_ver = InterpreterVerifier(struct)
        else:
            self.__inter_ver.structure = struct

        # Set the configuration stuff into the keyword interpreter
        self.__inter_kw.relevant_kw = config.crawling.relevant_keywords
        self.__inter_kw.blacklisted_kw = config.crawling.blacklisted_keywords
        self.__inter_kw.link_policy = config.crawling.link_follow_policy

    def __verify_structure(self) -> bool:
        """Verifies the platform structure

        Raises
        ------
        ValueError
            If the structure is not a dictionary.

        Returns
        -------
        bool
            Whether the structure is in the proper form (True) or whether something is not (False).

        Notes
        -----
        The ValueError can probably not be fixed without serious code restructure. Therefore it is an error. All the
        other stuff that is being verified are warnings. Those can be fixed by retraining (hopefully) and hence do not
        raise an error.
        """
        if not isinstance(self.__structure, dict):
            raise ValueError("The stored platform structure is not a dictionary!")
        elif self.__structure == {}:
            # No known platform structure so training is definitely needed. Nothing to do here but added for clarity :)
            return False
        elif not all(isinstance(elm, PageType) for elm in self.__structure.keys()):
            Logger.log("interpreter", "Not all keys of the platform structure dictionary are PageTypes!")
            return False
        elif not all(isinstance(elm, dict) for elm in self.__structure.values()):
            Logger.log("interpreter", "Not all values of the platform structure dictionary are dictionaries!")
            return False
        elif not all(isinstance(elm, StructuralElement) for pages in self.__structure.values() for elm in pages.keys()):
            Logger.log("interpreter", "Not all keys of the PageType dictionary in the platform structure dictionary are"
                                      " StructuralElements!")
            return False
        elif not all(isinstance(elm, ResourceIdentifier) for pages in self.__structure.values()
                     for elm in pages.values()):
            Logger.log("interpreter", "Not all values of the PageType dictionary in the platform structure dictionary"
                                      " are dictionaries!")
            return False
        return True

    def __verify_config(self, config: Configuration):
        """Verifies the obtained configuration.

        Parameters
        ----------
        config : Configuration
            The configuration to verify. Values are not verified, only whether the objects are instantiated.

        Raises
        ------
        ValueError
            If `config` is None
        AssertionError
            If `config` is not an instance of Configuration, the `crawling` attribute is no instance of Crawling or the
            `workday` attribute is no instance of Workday.
        """
        if config is None:
            raise ValueError("Configuration is None!")
        elif not isinstance(config, Configuration):
            raise AssertionError("Configuration is not a configuration object!")
        elif not isinstance(config.crawling, Crawling):
            raise AssertionError("Configuration has no instance of Crawling as an attribute!")
        elif not isinstance(config.workday, Workday):
            raise AssertionError("Configuration has no instance of Workday as an attribute!")
        elif not isinstance(config.crawling.platform, str):
            raise AssertionError("Configuration has no platform defined!")
        elif not isinstance(config.crawling.relevant_keywords, list):
            raise AssertionError("Configuration has not relevant keywords list defined! Not even an empty one.")
        elif not isinstance(config.crawling.blacklisted_keywords, list):
            raise AssertionError("Configuration has no blacklisted keywords list defined! Not even an empty one.")

    def __determine_thread_status(self, parsed_data: SectionData, page: str) -> t.Union[t.List[str], None]:
        """Determines the ThreadStatus of the threadlist in `parsed_data`

        Parameters
        ----------
        parsed_data : SectionData
            Parsed data containing the thread list. Must be a SectionData object as the other ParseData objects do not
            have that attribute. Will be filled with the ThreadStatus list in the `thread_status` attribute of
            `parsed_data`.
        page : str
            HTML of the page from where the info comes from. Used to get the threads from the page.

        Returns
        -------
        t.Union[t.List[str], None]
            Thread titles on `page` or None if no titles should be on the page or could not be found.
        """
        # Future TODO fix status to include updated (so new posts are present)
        # Determine ThreadStatus
        qb = QueryBuilder(self.__data_api, "threads")
        thread_status = []

        # For each thread check if their title is in the database and retrieve thread status. If not in db, use
        # UNKNOWN. Assumes that thread titles are unique on a platform basis (so no duplicate titles on the same
        # platform). Skip if no thread titles should be on the page (and so is none) or if it could not be found.
        threads = None

        if parsed_data.thread_list is not None:
            threads = strip_tags(parsed_data.thread_list.get_elements(page))

            for thread in threads:
                if thread:
                    # Assuming no linebreaks in title so only need to pick first element.
                    query = {"title": thread[0]}
                    nrof_results = qb.count_documents(query).exec()

                    if nrof_results == 0:
                        thread_status.append(ThreadStatus.UNKNOWN)
                        continue
                    elif nrof_results > 1:
                        query = {"title": thread, "platform_id": self.__platform_id}

                    result = qb.find_one(query).exec()

                    if result is not None:
                        thread_status.append(ThreadStatus.PARSED)
                    else:
                        thread_status.append(ThreadStatus.UNKNOWN)
                else:
                    Logger.log("interpreter", "Encountered empty element in thread list, skipping for now")

            if not thread_status:
                # No threads could be found so badly formatted page :(
                parsed_data.thread_status = None
            else:
                parsed_data.thread_status = thread_status

        return threads

    def __determine_badly_formatted(self, parsed_data: ParsedData):
        """Determine whether a page is truly badly formatted or that certain elements may be missing and hence the page
           is not badly formatted at all.

        Parameters
        ----------
        parsed_data : ParsedData
            ParsedData class that indicates the type of page.
        """
        if self.__inter_nav.prev_page_button is None:
            if isinstance(parsed_data, ThreadData):
                # This evaluates to true on every first page of a thread where the previous page button is allowed
                # to be missing.
                if parsed_data.nrof_posts_current_thread == self.__inter_data.posts_per_page:
                    self.__inter_nav.is_badly_formatted = False
            elif isinstance(parsed_data, SectionData):
                # There should never be a reason to go back. Setting to false.
                self.__inter_nav.is_badly_formatted = False
        if self.__inter_nav.next_page_button is None:
            if isinstance(parsed_data, ThreadData):
                # If the thread is complete then the next page button is allowed to be missing.
                if parsed_data.is_thread_complete:
                    self.__inter_nav.is_badly_formatted = False
            if isinstance(parsed_data, SectionData):
                # The next page button is allowed to be missing on the last page, but the best detection we have is
                # this button being missing. So assuming this is the last page and hence no badly format mark.
                self.__inter_nav.is_badly_formatted = False

    def __store_data(self, authors_user_names: t.List[str], authors_nrof_posts: t.List[int],
                     authors_popularity: t.List[int], registration_dates: t.Optional[t.List[t.Union[datetime, str]]],
                     thread_title: str, thread_section: str, posts_dates: t.Optional[t.List[t.Union[datetime, str]]],
                     posts_contents: t.List[str], page_relevancy: Relevance, post_count: int) -> t.Optional[Relevance]:
        """Store the extracted data in the database.

        Parameters
        ----------
        authors_user_names : list of str
            Usernames of the authors of the posts.
        authors_nrof_posts : list of int
            Nrof posts each author has made on the platform. Should be in the same order as `authors_user_names`.
        authors_popularity : list of int
            How popular each author is on the platform. Should be in the same order as `authors_user_names`.
        registration_dates : list of str
            Dates of registration of each of the authors.
        thread_title : str
            Title of the thread this data belongs to.
        thread_section : str
            Section to which `thread` belongs.
        posts_dates : list of str
            Dates when each post was posted in the thread. Should be in the same order as `authors_user_names`
        posts_contents : list of str
            The contents of each post. Should be in the same order as `authors_user_names`
        post_count : int
            The current amount of posts counted by InterpreterData.

        Returns
        -------

        Relevance
            Relevance of the stored page.
        """
        if thread_title is None:
            # If thread title does not exist we cannot save anything to the database
            return page_relevancy

        thread_find_dict = {
            'title': thread_title,
            'platform_id': self.__platform_id
        }

        thread_dict = {
            'title': thread_title,
            'platform_id': self.__platform_id,
            'posts': [],
            'section': ''
        }

        if thread_section is not None:
            thread_dict['section'] = thread_section
        else:
            thread_dict['section'] = None

        if page_relevancy is not None:
            thread_dict['relevancy'] = page_relevancy
        else:
            thread_dict['relevancy'] = Relevance.UNKNOWN

        thread = self.__find_or_insert_thread(thread_find_dict, thread_dict)

        # Update relevancy if relevance is blacklisted. Irrelevant and relevant is decided on first thread page and
        # hence does not need updating.
        if page_relevancy is not None and page_relevancy == Relevance.BLACKLISTED:
            thread["relevancy"] = page_relevancy
            self.__data_api['threads'].update_by_id(thread['_id'], thread)
            Logger.log("blacklist", "This page contains one or more blacklisted keywords. Aborting the crawling of"
                                    "the thread and not storing this page.")
            return

        saved_post_count = len(thread['posts'])
        if post_count > saved_post_count:
            next_sequence_number = saved_post_count + 1
            # length is the same for all arrays, since is_data_complete holds
            if authors_user_names is not None:
                nrof_posts = len(authors_user_names)
            else:
                nrof_posts = post_count
            save_all = True  # Save everything or only author usernames and post contents

            if authors_popularity is None:
                authors_popularity = []
            if registration_dates is None:
                registration_dates = []
            if posts_dates is None:
                posts_dates = []

            if len(posts_contents) != nrof_posts or len(authors_nrof_posts) != nrof_posts or \
                    len(authors_popularity) != nrof_posts or len(registration_dates) != nrof_posts or \
                    len(posts_dates) != nrof_posts:
                Logger.log("interpreter", "Mismatch in list lengths! Only saving users and posts. \n Users: {} \n "
                                          "Users nrof posts: {} \n Users popularity: {} \n Users registration dates: {}"
                                          " \n Posts: {} \n Post dates: {}"
                           .format(len(authors_user_names), len(authors_nrof_posts), len(authors_popularity),
                                   len(registration_dates), len(posts_contents), len(posts_dates)))
                if len(posts_contents) != nrof_posts:
                    Logger.log("interpreter", "Can not save users and posts due to mismatch in their lengths. Aborting "
                                              "saving all together.")
                    if page_relevancy is not None:
                        return page_relevancy
                    else:
                        return Relevance.UNKNOWN
                else:
                    save_all = False

            for n in range(nrof_posts):
                user_find_dict = {}
                user_dict = {}

                if authors_user_names is not None:
                    user_dict['username'] = authors_user_names[n]
                    user_find_dict['username'] = authors_user_names[n]
                else:
                    # If usernames could not be extracted then users cannot be coupled to posts and hence saving
                    # anything is not possible besides the thread itself.
                    break

                user_find_dict['platform_id'] = self.__platform_id
                user_dict['platform_id'] = self.__platform_id

                if authors_nrof_posts is not None and save_all:
                    user_dict['nrof_posts'] = authors_nrof_posts[n]
                else:
                    user_dict['nrof_posts'] = None

                if authors_popularity is not None and save_all:
                    user_dict['popularity'] = authors_popularity[n]
                else:
                    user_dict['popularity'] = None

                if registration_dates is not None and save_all:
                    user_dict['registration_date'] = registration_dates[n]
                else:
                    user_dict['registration_date'] = None

                user = self.__find_or_insert_user(user_find_dict, user_dict)

                post = {
                    'sequence_number': next_sequence_number,
                    'user_id': user['_id'],
                    'thread_id': thread['_id'],
                    'attachments': []  # Can be replaced in future code, will not be implemented now.
                }

                if posts_contents is not None:
                    post['content'] = posts_contents[n]
                else:
                    # No posts to be saved so saving users is useless as they are not linked to the thread. Aborting.
                    break

                if posts_dates is not None and save_all:
                    post['date_posted'] = posts_dates[n]
                else:
                    post['date_posted'] = None

                next_sequence_number += 1

                post_id = self.__data_api['posts'].insert(post).exec()
                thread['posts'].append(post_id)

        self.__data_api['threads'].update_by_id(thread['_id'], {'$set': {'posts': thread['posts']}}).exec()

        if isinstance(thread["relevancy"], Relevance):
            return thread["relevancy"]
        elif isinstance(thread["relevancy"], str):
            return Relevance(thread["relevancy"].lower())
        elif isinstance(thread["relevancy"], dict):
            return Relevance(thread["relevancy"]["enum_value"].lower())
        else:
            Logger.log("interpreter", "Could not convert db enum back to python enum ({}), defaulting to "
                                      "unknown".format(thread["relevancy"]))
            return Relevance.UNKNOWN

    def __set_section_button(self, thread_list: t.Union[ResourceIdentifier, None],
                             section_list: t.Union[ResourceIdentifier, None],
                             subsection_list: t.Union[ResourceIdentifier, None],
                             page: str, parsed_data: SectionData) -> t.List[str]:
        """ Set the section button and the other relevant attributes in `parsed_data`

        Parameters
        ----------
        thread_list : ResourceIdentifier
            ResourceIdentifier that locates the list of threads on the page.
        section_list : ResourceIdentifier
            ResourceIdentifier that locates the list of sections on the page.
        subsection_list : ResourceIdentifier
            ResourceIdentifier that locates the list of subsections on the page.
        page : str
            HTML of the page being parsed.
        parsed_data : SectionData
            DataClass of which certain attributes must be set depending on what is None.

        Returns
        -------
        list of str
            List of threads.
        """
        # Determine what to set
        if thread_list is not None:
            # Thread list should only be present if threads are actually on the page so always default to this.
            parsed_data.thread_list = thread_list
            threads_in_list = self.__determine_thread_status(parsed_data, page)

            threads = []
            for thread in threads_in_list:
                if thread:
                    threads.append(thread[0])

            if not threads:
                threads = None
        else:
            parsed_data.thread_list = None
            threads = None

        # Sections/subsections can be present on the same page with threads so account for this
        if section_list is not None and subsection_list is not None:
            if len(section_list.get_elements(page)) > len(subsection_list.get_elements(page)):
                parsed_data.section_list = section_list
                parsed_data.section_button = None
                parsed_data.subsection_list = subsection_list
            else:
                parsed_data.subsection_list = subsection_list
                parsed_data.section_button = None
                parsed_data.section_list = section_list
        elif section_list is not None:
            parsed_data.section_list = section_list
            parsed_data.subsection_list = None
            parsed_data.section_button = None
        elif subsection_list is not None:
            parsed_data.subsection_list = subsection_list
            parsed_data.section_list = None
            parsed_data.section_button = None

        return threads

    def __apply_badly_formatted(self, url: str):
        """Apply the badly formatted mark on a badly formatted page.

        Parameters
        ----------
        url : str
            URL to identify the page in the database
        """
        query = {"page_url": url}
        nrof_pages = self.__data_api["full webpage"].count_documents(query).exec()

        if nrof_pages == 0:
            Logger.log("interpreter", "Could not retrieve page with url {} from the database".format(url))
        elif nrof_pages >= 1:
            if nrof_pages > 1:
                Logger.log("interpreter", "Found multiple pages in the database with the same url "
                                          "({}). I'm taking the first result".format(url))

            webpage_original = self.__data_api["full webpage"].find_one(query).exec()
            webpage = deepcopy(webpage_original)
            webpage["badly_formatted"] = True

            self.__data_api["full webpage"].update(webpage_original, webpage)

    def __handle_badly_formatted(self, url: str, parsed_data: ParsedData):
        """Handles the badly formatted pages, by applying the mark and notifying the user based on the badly formatted
        count

        Parameters
        ----------
        url : str
            URL of the page currently being parsed
        parsed_data : ParsedData
            ParsedData class that determines whether the page is badly formatted or not.
        """
        if parsed_data.is_badly_formatted:
            # Apply badly formatted mark if the page is badly formatted
            self.__apply_badly_formatted(url)

            # Check if it is within the first two hours. If so then check the overall count.
            if self.__first_two_hours:
                # Needs immediate training.
                if self.__badly_formatted_count >= 3 or self.__missing_nav_count >= 2:
                    Logger.log("interpreter", "Found either three badly formatted pages or two pages for which "
                                              "navigational elements are missing")
                    self.__need_training = True
            else:
                # Check consecutive count and postpone training until after the workday
                if self.__badly_formatted_count >= 3:
                    Logger.log("interpreter", "Found three consecutive badly formatted pages")
                    self.training_after_workday = True

    def __find_or_insert_thread(self, query, new_thread):
        return self.__find_or_insert('threads', query, new_thread)

    def __find_or_insert_user(self, query, new_user):
        return self.__find_or_insert('users', query, new_user)

    def __find_or_insert(self, collection, query, document) -> t.Dict:
        """Finds a document matching the query, otherwise inserts `document`

        This functions attempts to find a document matching the query. If such a document
        exists, it is returned. If no such document exists, `document` will be inserted.
        In most practical cases, `query` should match the `document`, but this is not
        enforced.

        Parameters
        ----------
        collection: str
            The name of the collection that contains the document
        query: dict
            A MongoDb Query object
        document: dict
            The document to insert of no document was found

        Returns
        -------
        dict
            The first document matching the query, or `document` if no
            such document exists
        """
        result = self.__data_api[collection].find_one(query).exec()

        if result is None:
            document['_id'] = self.__data_api[collection].insert(document).exec()
            return document

        return result

    def __determine_page_type(self, page: str) -> t.Union[PageType, None]:
        """Determines the page type of the supplied page based on the platform structure.

        Parameters
        ----------
        page : str
            HTML of the page to determine the PageType of.

        Returns
        -------
        PageType
            PageType of the page based on the saved platform structure (`__structure`). None if nothing is in the
            platform structure dict.

        Notes
        -----
        It determines the page type based on the least amount of missing elements, under the assumption that elements
        are not on a page if they are not relevant (like author_usernames on a front page).
        """
        # Try to find all elements on the page and mark those that are missing
        found = {}
        for page_type, element in self.__structure.items():
            for elm, identifier in element.items():
                if not identifier.get_elements(page) and elm != NavigationalElement.PreviousPageButton and \
                        elm != NavigationalElement.NextPageButton:
                    if page_type in found.keys():
                        found[page_type] += 1
                    else:
                        found[page_type] = 1

            # Only reason this page_type is not in found yet is because everything has been found so far. I.e. 0 missing
            # elements.
            if page_type not in found.keys():
                found[page_type] = 0

        # Get the key with the lowest amount of missing elements. Assumes elements cannot be found if they do not belong
        # to this page. Needs testing to confirm.
        if len(found) == 0:
            return None

        if PageType.LoginPage in found.keys() and found[PageType.LoginPage] == 0:
            return PageType.LoginPage
        else:
            least_not_found = None
            least_numerical_not_found = -1
            for key, element in found.items():
                if least_numerical_not_found == -1:
                    least_numerical_not_found = element
                    least_not_found = key
                elif least_numerical_not_found > element:
                    least_numerical_not_found = element
                    least_not_found = key
                elif least_numerical_not_found == element:
                    # If the same amount of elements are not found and the amount of elements that are part of the
                    # current page_type is larger than the previously found least missing elements page_type then
                    # replace it with the new one under the assumption that if something is not that page a lot more
                    # elements should be missing. Can break on badly formatted pages :(
                    if len(self.__structure[key]) > len(self.__structure[least_not_found]):
                        least_not_found = key

            return least_not_found

    def __start_training(self, page: str, url: str, first: bool = False, driver: TorBrowserDriver = None,
                         is_page_two=False, javascript: str = '') -> t.Optional[str]:
        """Function that starts training of the supplied page.

        After the training is done, the structure is verified. If the structure is in the proper format, the relevant
        internal parameters are updated so that each subinterpreter has the new platform structure saved. If the
        structure is not properly formatted then the training happens a second time. If that training has the same
        problem then an error is raised. Otherwise, the same thing happens as if the structure has a proper format the
        first time around.

        Parameters
        ----------
        page : str
            HTML of the page to train.
        url : str
            URL of the page to train.
        first : bool, optional
            Whether this is the first call or a second call because something went wrong.

        Returns
        -------
        page_structure : str
            Structure of the page.

        Raises
        ------
        AssertionError
            If the platform structure is incorrectly formatted after the second try.
        """
        if is_page_two:
            trainer = Trainer(self.__data_api, driver=driver, method_identifiers_map=self.method_identifiers_map)
        else:
            trainer = Trainer(self.__data_api, driver=driver)
        page_obj = Page(page, url)
        page_struct, self.method_identifiers_map = trainer.train(page_obj, javascript=javascript)

        # If there was JS to execute, then communicate that it was not a training yet to the training_sequence.
        if isinstance(page_struct, str):
            return page_struct
        while True:
            identified_elements = page_struct.identifiers
            loaded = False
            while not loaded:
                try:
                    driver.refresh()
                    loaded = True
                except TimeoutException:
                    CrawlerUtils.wait_tor_browser()
                    pyautogui.hotkey("ctrl", "shift", "l")
                    time.sleep(1)
            ## TODO check for captchas here!!
            if self.js_db_struct[page_struct.page_type] != '':
                driver.execute_script(self.js_db_struct[page_struct.page_type])
            had_issues = []
            for key in identified_elements.keys():
                if isinstance(identified_elements[key], XPathExcept):
                    elements = driver.find_elements(by=By.XPATH, value=identified_elements[key].x_path_use.x_path)
                    elements += driver.find_elements(by=By.XPATH, value=identified_elements[key].x_path_remove.x_path)
                else:
                    elements = driver.find_elements(by=By.XPATH, value=identified_elements[key].x_path)
                if len(elements) == 0:
                    answer = pymsgbox.confirm('Is there a ' + key.name + ' in the current page? ', 'Check',
                                              ['Yes', 'No'])
                    if answer == 'Yes':
                        self.method_identifiers_map[key] = self.method_identifiers_map[key] + 1
                        had_issues.append(key)
            if len(had_issues) != 0:
                self.__helpers.save_page(driver.current_url, driver, training=True)
                if is_page_two:
                    trainer = Trainer(self.__data_api, driver=driver, had_issues=had_issues,
                                      method_identifiers_map=self.method_identifiers_map)
                else:
                    trainer = Trainer(self.__data_api, driver=driver, had_issues=had_issues)
                page_obj = Page(driver.page_source, url)
                page_struct, self.method_identifiers_map = trainer.train(page_obj)
            else:
                break

        # Get the old structure and update it for this PageType
        new_struct = self.__structure
        new_struct[page_struct.page_type] = page_struct.identifiers

        try:
            self.__update_structure(new_struct, self.__config)
        except AssertionError:
            if first:
                # If there was JS to execute, then communicate that it was not a training yet to the training_sequence.
                page_structure = self.__start_training(page, url, first=False)
                if isinstance(page_structure, str):
                    return page_structure
            else:
                raise AssertionError("After the second training the platform structure format is still not correct. "
                                     "Please look at the training saving code and fix the incorrect formatting!")
        self.__need_training = self.__determine_training(page)

        # It should happen in parse_page. Nonetheless, I have to parse the same page as before to check the existence
        # of a captcha after refreshing for stability, and I don't want to evaluate whether a captcha is in the page,
        # forcing me to solve it immediately.
        if self.__inter_cap.captcha_on_page and not self.__inter_cap.captcha_full_page:
            self.__captcha_solver.solve_captcha(self.__inter_cap.captcha_type)
            self.__helpers.wait_tor_browser()

    def __determine_training(self, page: str) -> bool:
        """Determine whether additional training is needed or not.

        Training proceeds according to the following flow: log-in page, front page, section page, section page 2,
        subsection page, subsection page 2, thread page, thread page 2. The only type of page that is optional is the
        subsection page and subsection page 2. All others are required. Due to this order, we only need to check if
        a thread page is defined and whether the second thread page has been trained.

        Parameters
        ---------
        page : str
            String representation of the HTML page

        Returns
        -------
        bool
            Whether training is needed or not. True if training is needed, False if not.
        """
        if self.__missing_struct:
            # Added because this can only be trained on the second thread page, marking the end of training.
            first_thread_page = False

            section_missing = True
            front_missing = True

            for key in self.__structure.keys():
                if key == PageType.ThreadPage and self.__thread_missing:
                    self.__thread_missing = False
                    first_thread_page = True
                elif key == PageType.SectionPage:
                    section_missing = False
                elif key == PageType.FrontPage:
                    front_missing = False

            if not (self.__thread_missing or section_missing or front_missing):
                if first_thread_page:
                    # All types of essential pages present but only trained on first thread page, need to continue
                    return True
                else:
                    # All types of essential pages present, no more training needed :)
                    self.__missing_struct = True
                    return False
            else:
                # Due to agreed training structure this should always trigger unless we have reached a thread page
                return True
        else:
            # Determine page to check which one has been confirmed
            key = self.__determine_page_type(page)
            self.__confirmed[key] = True

            # Check whether all pages have been confirmed
            if all(self.__confirmed[key] for key in self.__confirmed.keys()):
                return False  # Everything is confirmed, no more training needed :)
            else:
                return True  # Not everything is confirmed so more training is needed

    @property
    def config(self) -> Configuration:
        """Gets the configuration of the Interpreter

        Returns
        -------
        Configuration
            Configuration object of the Interpreter
        """
        return self.__config

    @config.setter
    def config(self, config: Configuration):
        """Sets the configuration of the Interpreter

        Parameters
        ----------
        config : Configuration
            Configuration object to set.

        Raises
        ------
        ValueError
            If `config` is None or not an instance of Configuration.
        """

        self.__verify_config(config)
        self.__config = config

    @property
    def interpreter_verifier(self) -> InterpreterVerifier:
        """Gets the InterpreterVerifier for the current platform structure

        Returns
        -------
        InterpreterVerifier
            InterpreterVerifier for the current platform structure.
        """
        return self.__inter_ver

    def start_training_after_workday(self, page: str, url: str) -> t.Optional[bool]:
        """Starts a training session, supposed to be called after the workday has ended and the training_after_workday
        attribute has been set to True

        Parameters
        ----------
        page : str
            HTML of the page to train on.
        url : str
            URL corresponding to the page to train.
        """
        # If there was JS to execute, then communicate that it was not a training yet to the training_sequence.
        if not self.__start_training(page, url):
            return False
        self.training_after_workday = False
