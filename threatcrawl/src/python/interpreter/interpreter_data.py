"""Class that extracts the relevant data from a web page"""
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tbselenium.tbdriver import TorBrowserDriver

from crawler.crawler_utils import CrawlerUtils
from trainer.resource_identifier import ResourceIdentifier
from enums import StructuralElement, DataElement, NavigationalElement, PageType
from datetime import datetime
from interpreter.interpreter_utils import strip_tags, convert_types, get_type, verify_struct
from interpreter.word_counter import count_words, verify_posts_content, interpret_count
from dateparser import parse
from utils import Logger
import typing as t


class InterpreterData:
    """Class that extracts the relevant data from a web page.

    This class collects the relevant data from a web page. This data includes the type of page, the threads on the page
    that can be crawled, the threads on the page that we already know and those that have changed since we last crawled
    them, the usernames of the authors of posts in a thread, the nr. of (total platform) messages the authors of posts
    in a thread have, the popularity of the authors of posts in a thread, the registration date of the authors of posts
    in a thread, the emails of the authors of posts in a thread, the title of the thread, the section that the thread
    belongs to, the age of the thread, the dates of posting of the posts in a thread, the contents of the posts of a
    thread and the number of words on a page in a thread. This class also houses some more additional information,
    like whether all the information could be understood and whether this page marks the end of the thread or not.

    The attributes are only updated if their preconditions are met. This is to retain certain information that may be
    relevant but cannot be extracted from that exact page because it is missing (either by design of the platform or
    because the page is badly formatted).

    Parameters
    ---------
    structure : dict of <StructuralElement, ResourceIdentifier> pairs
        The platform structure of the platform to which all the web pages belong that need to be parsed.

    Attributes
    ---------
    __structure : dict of <StructuralElement, ResourceIdentifier> pairs
        The platform structure of the platform to which all the web pages belong that need to be parsed. Is initialised
        in the constructor.
    __thread_list : list of ResourceIdentifier
        List of threads that are recognised to be on the page. Only set if `page_type` is not set to ThreadPage.
    __section_list : list of ResourceIdentifier
        List of sections that are recognised to be on the page. Only set if `page_type` is not set to ThreadPage.
    __subsection_list : list of ResourceIdentifier
        List of subsections that are recognised to be on the page. Only set if `page_type` is not set to ThreadPage.
    __section_title : str
        Title of the section that has been previously visited. Updates when `page_type` is SectionPage.
    __subsection_title : str
        Title of the subsection that has been previously visited, None if gone from a SectionPage to a ThreadPage.
        Updates when `page_type` is SubsectionPage.
    __authors_usernames : list of str
        List that contains the usernames of the authors of the posts in the thread on the last parsed page. Only set if
        `page_type` is set to ThreadPage.
    __authors_nrof_posts : list of int
        List that contains the number of posts of the authors of the posts in the thread (the thread which was on
        the last parsed page) on the complete platform. Has the same order as `__authors_usernames`. Only set if
        `page_type` is set to ThreadPage.
    __authors_popularity : list of int
        List that contains the popularity of the authors of the posts in the thread (the thread which was on the last
        parsed page) on the complete platform. Has the same order as `__authors_usernames`. Only set if `page_type` is
        set to ThreadPage.
    __authors_registration_date : list of datetime
        List that contains the registration dates of the authors of the posts in the thread on the last parsed page.
        Has the same order as `__authors_usernames`. Only set if `page_type` is set to ThreadPage.
    __authors_emails : list of str
        List that contains the email addresses of the authors of the posts in the thread on the last parsed page. Has
        the same order as `__authors_usernames`. Only set if `page_type` is set to ThreadPage.
    __thread_title : str
        Title of the thread to which the last parsed page belongs. Only set if `page_type` is set to ThreadPage.
    __thread_section : str
        Title of the section to which the thread on the last parsed page belongs. Only set if `page_type` is set to
        ThreadPage.
    __thread_age : datetime
        Date of the first post of the thread on the last parsed page. Only set if `page_type` is set to ThreadPage and
        the page is the first page of the thread.
    __posts_dates : list of date
        List of dates that belong to the posts in the thread on the last parsed page. Has the same order as
        `__authors_usernames`. Only set if `page_type` is set to ThreadPage.
    __posts_content : list of str
        List of the contents of the posts in the thread on the last parsed page. Has the same order as
        `__authors_usernames`. Only set if `page_type` is set to ThreadPage.
    __post_count : int
        How many posts belong to the current thread. Includes the posts on the last parsed page. Only accurate if
        `page_type` is set to ThreadPage, on non-ThreadPages the count is reset to 0.
    __posts_per_page : int
        How many posts are expected per page of the current thread. Is used to check whether the end of the thread has
        been reached. Only accurate if `page_type` is set to ThreadPage, on non-ThreadPages the count is reset to 0.
        This value is set on the first page of a thread and used to check against on other pages. If the number of
        posts per page is larger than stored, the larger value is used (as it is assumed that the first page has been
        badly formatted).
    __nrof_words : int
        The amount of readable words on the last parsed page. Is always set, however is only relevant when `page_type`
        is set to ThreadPage.
    is_data_complete : bool
        Whether all the relevant information (determined by the value of the `page_type` attribute) could be
        extracted from the page. True if all information could be extracted, False if not. False indicates a badly
        formatted page or an incorrect platform structure.
    is_thread_complete : bool
        Whether we have reached the last page of the thread. Is only set if `page_type` is set to ThreadPage.

    Raises
    ------
    ValueError
        If `structure` is not a dictionary of <StructuralElement, ResourceIdentifier> pairs.

    Notes
    -----
    A thread being parsed completely differs from having extracted all relevant information. It could happen that one
    page of the thread is badly formatted and not all information of the thread could be extracted. However, if the
    last page has been parsed, then the thread has been parsed completely. These two concepts are different and should
    always be kept in mind. Therefore, the `is_thread_complete` attribute stores whether we have parsed the last page
    of the thread and on each single page of the thread the `is_data_complete` attribute stores whether we could
    extract all information.
    """

    def __init__(self, structure: t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]]):
        verify_struct(structure)

        self.__structure = structure
        self.__thread_list = None
        self.__section_list = None
        self.__subsection_list = None
        self.__section_title = None
        self.__subsection_title = None
        self.__authors_usernames = None
        self.__authors_nrof_posts = None
        self.__authors_popularity = None
        self.__authors_registration_date = None
        self.__authors_emails = None
        self.__thread_title = None
        self.__thread_section = None
        self.__thread_age = None
        self.__posts_dates = None
        self.__posts_content = None
        self.__post_count = -1
        self.__posts_per_page = -1
        self.__nrof_words = -1
        self.is_data_complete = None
        self.is_thread_complete = None

    def parse_page(self, page: str, page_type: PageType, driver: TorBrowserDriver = None) -> bool:
        """Parse the supplied web page according to the known platform structure.

        During parsing, all the attributes are set (if their preconditions are met). If an attribute cannot be set
        even though it should be settable according to the platform structure and the preconditions, then the
        `__is_data_complete` bool will be set to False. Returns True when finished, returns False if it could not
        finish.

        Parameters
        ---------
        page : str
            The web page to parse.
        page_type : PageType
            The type of the page to parse.
        driver : TorBrowserDriver
            TorBrowser driver handling the crawling session.

        Returns
        -------
        bool
            True if parsing the page is completed, False if the parsing did not complete. Note that completing parsing
            is different from extracting all the relevant data. A page can be parsed completely without all the
            information being extracted (either because it doesn't exist or because this page is badly formatted).
        """
        # Reset some information to None for proper functioning
        self.__thread_list = None
        self.__section_list = None
        self.__subsection_list = None

        # Gets all data on the page
        extracted_data = {}
        optional_data = {}
        raw_data = {}
        for key, value in self.__structure[page_type].items():
            elements = value.get_elements(page)
            elements = strip_tags(elements)
            raw_data[key] = elements

            # Convert a list of lists with one element into a single list, except post contents because that is done
            # elsewhere
            if len(elements) == 1 and key != DataElement.PostContent:
                elements = elements[0]
            elif all(len(elm) == 1 for elm in elements):
                single_list = []

                for elm in elements:
                    single_list.append(elm[0])

                elements = single_list

            if isinstance(get_type(key), datetime):
                dates = self.__extract_date(value.date_format, elements)

                converted = dates
            elif isinstance(get_type(key, page_type=page_type), ResourceIdentifier):
                # If the key is for a NavigationalElement or InputElement (as those return ResourceIdentifiers) then it
                # indicates XPath which is not relevant for the data extraction and conversion can hence be skipped with
                # a few exceptions: ThreadTitle list on a non-Thread page and SectionTitle and SubsectionTitle on every
                # page.
                if page_type != PageType.ThreadPage and key == DataElement.ThreadTitle:
                    converted = value
                elif key == DataElement.SectionTitle or key == DataElement.SubsectionTitle:
                    converted = value
                    optional_data[key] = elements  # Assign tag values as they may be useful in the future
                else:
                    continue
            else:
                # Convert to correct datatype (str or int)
                if elements:
                    converted = convert_types(elements, key, page_type=page_type)
                else:
                    # Empty list gets yeeted so that we do not pretend something is present while it isn't
                    converted = None

            if not elements:
                extracted_data[key] = None
            else:
                extracted_data[key] = converted

        self.__assign_values(extracted_data, optional_data, page_type, driver)

        # if page_type == PageType.ThreadPage:
        #     self.__check_values(raw_data, page_type)

        # Determine how many words are on the page
        self.__posts_content = verify_posts_content(page_type, self.__posts_content)
        if self.__thread_list is not None:
            self.__nrof_words = count_words(page_type, self.__posts_content, self.__thread_list, page)
        elif self.__section_list is not None and self.__subsection_list is not None:
            # If both exist, check which one contains the links to the sections/subsections and which one is just
            # a few buttons
            if len(self.__section_list.get_elements(page)) > len(self.__subsection_list.get_elements(page)):
                self.__nrof_words = count_words(page_type, self.__posts_content, self.__section_list, page)
            else:
                self.__nrof_words = count_words(page_type, self.__posts_content, self.__subsection_list, page)
        elif self.__section_list is not None:
            self.__nrof_words = count_words(page_type, self.__posts_content, self.__section_list, page)
        elif self.__subsection_list is not None:
            self.__nrof_words = count_words(page_type, self.__posts_content, self.__subsection_list, page)
        else:
            # This should occur if we are on a ThreadPage, so only posts content is needed.
            self.__nrof_words = count_words(page_type, self.__posts_content, None, page)

        self.is_data_complete = interpret_count(self.__nrof_words)

        old = True
        for key, value in extracted_data.items():
            if value is None:
                # Make an exception for SectionTitle because of section/subsection structure and impossible general
                # training. Only if the heuristics fail too then it should be marked as incomplete.
                if key == DataElement.ThreadSection:
                    if self.__thread_section is not None:
                        continue

                self.is_data_complete = False
                old = False
                break

        if old:
            self.is_data_complete = True

        self.__determine_thread_end(page, page_type)

        return True

    def __extract_date(self, date_format: str, strings: t.Union[t.List[str], t.List[t.List[str]]]) -> \
            t.Union[None, datetime, t.List[datetime]]:
        """Extracts the date from a string that supposedly contains a date

        Parameters
        ---------
        date_format : str
            String representation of the date format that is used. For the supported syntax, please check the notes.
        strings : list of str | list of list of str
            The list of (list of) strings that contain a date formatted according to the `date_format`.

        Returns
        -------
        None
            If no dates could be extracted.
        datetime
            If a single date could be extracted.
        list of datetime
            List of dates that could be extracted. Follows the same order as `strings` but it cannot be guaranteed that
            elements are not missing.

        Notes
        -----
        The syntax that is expected from `date_format` is listed at the following location
        https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
        """
        if date_format is None:
            Logger.log("warning", "I expected a date format but None was given. "
                                  "Attempting parsing but it can go wrong!")

        if not isinstance(strings[0], list):
            strings = [strings]

        dates = self.__parse_date(strings, date_format=date_format)

        if not dates:
            dates = None
        elif len(dates) == 1:
            dates = dates[0]

        return dates

    def __parse_date(self, strings: t.List[t.List[str]], date_format: str = None) -> t.List[t.List[datetime]]:
        """Parse the date using the information from the parameters

        Parameters
        ----------
        strings : t.List[t.List[str]]
            The list of list of strings that contain a date.
        date_format : str
            The date format the dates are in. Follows the format as specified in
            https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior

        Returns
        -------
        t.List[t.List[datetime]]
            strings converted into dates if possible.
        """
        date_list = []
        for e in strings:
            dates = []
            for elm in e:
                try:
                    dates.append(parse(elm, date_formats=[date_format]))
                except ValueError:
                    Logger.log("warning", "Could not understand the date. Continuing. Erring string {}".format(elm))
                    continue

            date_list.append(dates)
        return date_list

    def __assign_values(self, extracted_data: t.Dict[StructuralElement, t.Any],
                        optional_data: t.Dict[StructuralElement, t.Any], page_type, driver: TorBrowserDriver = None):
        """Assign the extracted data to the correct attributes.

        Parameters
        ----------
        extracted_data : dict<StructuralElement, Any>
            Dictionary containing the StructuralElement as key and the corresponding data as value.
        page_type : PageType
            The type of page the data comes from. Determines what values are saved.
        """
        if page_type != PageType.ThreadPage:
            for key, value in extracted_data.items():
                if isinstance(key, DataElement):
                    if key == DataElement.ThreadTitle:
                        self.__thread_list = value
                    elif key == DataElement.SectionTitle:
                        self.__section_list = value
                        if page_type == PageType.SectionPage:
                            try:
                                self.__section_title = optional_data[key][0]
                            except IndexError:
                                self.__section_title = None
                        elif page_type == PageType.FrontPage:
                            self.__section_title = None
                    elif key == DataElement.SubsectionTitle:
                        self.__subsection_list = value
                        if page_type == PageType.SubsectionPage:
                            try:
                                self.__subsection_title = optional_data[key][0]
                            except IndexError:
                                pass
                        elif page_type == PageType.SectionPage:
                            self.__subsection_title = None
        else:
            # In case of thread pages, we have to re-extract data and use XPaths to understand which username,
            # post count, ... belongs to which post. This is necessary because sometimes extraction may fail for
            # one or more post for a single attribute. This would result in lists of different lengths not
            # accounting for which posts have missing information.
            thread_struct = self.__structure[PageType.ThreadPage]

            self.__save_thread_title(thread_struct, driver)
            self.__save_thread_section(thread_struct, driver)
            self.__save_thread_age(thread_struct, driver)

            self.__authors_usernames = []
            self.__authors_nrof_posts = []
            self.__authors_popularity = []
            self.__authors_emails = []
            self.__authors_registration_date = []
            self.__posts_content = []
            self.__posts_dates = []

            post_content_list = driver.find_elements(By.XPATH, thread_struct[DataElement.PostContent].x_path)

            authors_usernames_elements = self.__find_related_elements(
                DataElement.AuthorUsername, driver, thread_struct)
            authors_nrof_posts_elements = self.__find_related_elements(
                DataElement.AuthorNrOfPosts, driver, thread_struct)
            authors_popularity_elements = self.__find_related_elements(
                DataElement.AuthorPopularity, driver, thread_struct)
            authors_emails_elements = self.__find_related_elements(
                DataElement.AuthorEmail, driver, thread_struct)
            authors_regdate_elements = self.__find_related_elements(
                DataElement.AuthorRegistrationDate, driver, thread_struct)
            posts_dates = self.__find_related_elements(
                DataElement.PostDate, driver, thread_struct)

            # I'm assuming that post content is always possible to retrieve.
            # Here I add a None or the text of the element to the associated array if any was found.
            for post_content in post_content_list:
                self.__add_value_to_array(self.__authors_usernames, CrawlerUtils.find_associated_element(
                    authors_usernames_elements, post_content, driver))
                self.__add_value_to_array(self.__authors_nrof_posts, CrawlerUtils.find_associated_element(
                    authors_nrof_posts_elements, post_content, driver))
                self.__add_value_to_array(self.__authors_popularity, CrawlerUtils.find_associated_element(
                    authors_popularity_elements, post_content, driver))
                self.__add_value_to_array(self.__authors_emails, CrawlerUtils.find_associated_element(
                    authors_emails_elements, post_content, driver))
                self.__add_value_to_array(self.__authors_registration_date, CrawlerUtils.find_associated_element(
                    authors_regdate_elements, post_content, driver))
                self.__add_value_to_array(self.__posts_dates, CrawlerUtils.find_associated_element(
                    posts_dates, post_content, driver))
                self.__posts_content.append(post_content.text)

    @staticmethod
    def __add_value_to_array(target_array, element: t.Optional[WebElement]):
        if element is not None:
            target_array.append(element.text)
        else:
            target_array.append(None)

    def __determine_thread_end(self, page: str, page_type: PageType):
        """Determines whether the end of a thread has been reached. Also updates the post count.

        Parameters
        ----------
        page : str
            HTML of the webpage being parsed.
        page_type : PageType
            What type of page is currently being parsed.
        """
        # If the current page is not a ThreadPage reset post count and posts per page to 0, else add nrof posts to post
        # count. Also checks whether the end of the thread has been reached (current posts < posts per page).
        # This assumes that between different threads a non-ThreadPage is parsed.
        if page_type != PageType.ThreadPage:
            self.__post_count = 0
            self.__posts_per_page = 0
            self.is_thread_complete = False
        elif self.__posts_content is not None:
            if self.__post_count == -1:
                self.__post_count = 0
            self.__post_count += len(self.__posts_content)

            if self.__posts_per_page <= 0:
                self.__posts_per_page = len(self.__posts_content)
                # Assumes threads consist out of more than one page. Can be overridden in main interpreter
                self.is_thread_complete = False
            elif self.__posts_per_page < len(self.__posts_content):
                Logger.log("warning", "First page is badly formatted! Found a larger value for posts per page! The old "
                                      "was {}, the new one is {}".format(self.__posts_per_page,
                                                                         len(self.__posts_content)))
                self.__posts_per_page = len(self.__posts_content)
                self.is_thread_complete = False
            elif self.__posts_per_page >= len(self.__posts_content):
                # If next page button is on the page, we are not done yet. Otherwise I assume we are done.
                if self.__structure[page_type][NavigationalElement.NextPageButton].get_elements(page):
                    # Check if the posts per page are larger than the found amount of posts. This indicates missing data
                    if self.__posts_per_page > len(self.__posts_content):
                        Logger.log("warning", "Page is badly formatted! Found less posts ({}) on this page than usual "
                                              "in this thread ({})and the next page button is present!"
                                   .format(len(self.__posts_content), self.__posts_per_page))
                        self.is_data_complete = False
                    self.is_thread_complete = False
                else:
                    self.is_thread_complete = True

    def __save_thread_title(self, thread_struct: dict, driver: TorBrowserDriver):
        try:
            value = driver.find_elements(By.XPATH, thread_struct[DataElement.ThreadTitle].x_path)[0]
            if value is not None:
                self.__thread_title = value.text
            else:
                self.__thread_title = None
        except KeyError:
            self.__thread_title = None

    def __save_thread_section(self, thread_struct: dict, driver: TorBrowserDriver):
        try:
            value = driver.find_elements(By.XPATH, thread_struct[DataElement.ThreadTitle].x_path)
            if isinstance(value, list):
                self.__thread_section = value[0].text
            else:
                # Could not find section on page so defaulting back to some previously saved info based on
                # some heuristics which won't be perfect
                if self.__subsection_title is not None and isinstance(self.__subsection_title, str):
                    self.__thread_section = self.__subsection_title
                elif self.__section_title is not None and isinstance(self.__section_title, str):
                    self.__thread_section = self.__section_title
                else:
                    self.__thread_section = None
        except KeyError:
            self.__thread_section = None

    def __save_thread_age(self, thread_struct: dict, driver: TorBrowserDriver):
        try:
            value = driver.find_elements(By.XPATH, thread_struct[DataElement.ThreadTitle].x_path)
            if self.__thread_age is None and value is not None and isinstance(value, list) and value:
                # Only set thread age for first page, is None if previously parsed page was not a ThreadPage
                self.__thread_age = value[0].text
            elif self.__thread_age is not None:
                self.__thread_age = None
            else:
                self.__thread_age = None
        except KeyError:
            self.__thread_age = None

    @staticmethod
    def __find_related_elements(key: DataElement, driver: TorBrowserDriver, thread_struct: dict):
        try:
            return driver.find_elements(By.XPATH, thread_struct[key].x_path)
        except KeyError:
            return [None]

    def __check_values(self, raw: t.Dict[StructuralElement, t.Any], page_type: PageType):
        """Checks whether all lists have the expected length and applies heuristics to get them to the correct length
        if that is not the case. Once the heuristics have trimmed the lengths of the lists they are assigned to the
        correct attributes.

        Parameters
        ----------
        raw : dict<StructuralElement, Any>
            Dictionary containing the raw data retrieved by the ResourceIdentifiers before being converted into the
            correct datatype.
        page_type : PageType
            Type of page currently being parsed.
        """
        if self.__authors_usernames is not None:
            desired_length = len(self.__authors_usernames)
        else:
            desired_length = self.__post_count
        corrected_data = {}

        if self.__authors_nrof_posts is not None:
            if len(self.__authors_nrof_posts) != desired_length:
                new = []

                for elm in raw[DataElement.AuthorNrOfPosts]:
                    if isinstance(elm, list):
                        nested = []
                        for e in elm:
                            if e.isnumeric():
                                nested.append(e)
                            else:
                                # Check whether the whole string consists only out of numbers with possibly commas
                                # and dots. With at least one number in front and behind the dot/comma and only one
                                # dot/comma separating each number.
                                pattern = "^[0-9]{1,3}(,[0-9]{3})*(.[0-9]+)?$"
                                match = re.match(pattern, e)
                                if bool(match):
                                    nested.append(e)

                        if nested:
                            new.append(nested)
                    else:
                        if elm.isnumeric():
                            new.append(elm)

                if len(new) == desired_length:
                    corrected_data[DataElement.AuthorNrOfPosts] = convert_types(new, DataElement.AuthorNrOfPosts,
                                                                                page_type)
                else:
                    Logger.log("error", "Could not correct a mismatch in lengths for author nrof posts.")
                    Logger.log("error", "Result of the failed attempt: {}".format(new))

        if self.__authors_registration_date is not None:
            if len(self.__authors_registration_date) != desired_length:
                new = []

                for elm in raw[DataElement.AuthorRegistrationDate]:
                    if isinstance(elm, list):
                        nested = []

                        for e in elm:
                            if "join date" in e.lower():
                                continue
                            else:
                                nested.append(e)

                        if nested:
                            new.append(nested)
                    else:
                        if "join date" in elm:
                            continue
                        else:
                            new.append(elm)

                if len(new) == desired_length:
                    corrected_data[DataElement.AuthorRegistrationDate] = self.__extract_date(
                        self.__structure[page_type][DataElement.AuthorRegistrationDate].date_format, new)
                else:
                    Logger.log("error", "Could not correct a mismatch in lengths for author registration dates.")

        # Assign the new values, if empty then nothing happens :)
        self.__assign_values(corrected_data, raw, page_type)

    @property
    def thread_list(self) -> t.Union[ResourceIdentifier, None]:
        """Gets the list of threads stored in the `__thread_list` attribute.

        Returns
        -------
        ResourceIdentifier | None
            ResourceIdentifier to find the list of threads on the last parsed page where `page_type` was not set to
            ThreadPage. None if no threads should be on the page or if they could not be found.

        Raises
        ------
        ValueError
            If `__thread_list` is not an instance of ResourceIdentifier.
        """
        return self.__thread_list

    @property
    def section_list(self) -> t.Union[ResourceIdentifier, None]:
        """Gets the list of sections stored in the `__section_list` attribute.

        Returns
        -------
        ResourceIdentifier | None
            ResourceIdentifier to find the list of sections on the last parsed page where `page_type` was not set to
            ThreadPage. None if no sections should be on the page or if they could not be found.

        Raises
        ------
        ValueError
            If `__section_list` is not an instance of ResourceIdentifier.
        """
        return self.__section_list

    @property
    def subsection_list(self) -> t.Union[ResourceIdentifier, None]:
        """Gets the list of threads stored in the `__subsection_list` attribute.

        Returns
        -------
        ResourceIdentifier | None
            ResourceIdentifier to find the list of subsections on the last parsed page where `page_type` was not set to
            ThreadPage. None if no subsections should be on the page or if they could not be found.

        Raises
        ------
        ValueError
            If `__subsection_list` is not an instance of ResourceIdentifier.
        """
        return self.__subsection_list

    @property
    def authors_usernames(self) -> t.Union[t.List[str], None]:
        """Gets the list of author usernames stored in the `__authors_usernames` attribute.

        Returns
        -------
        list of str | None
            List of usernames of the authors of the posts in the last parsed page where `page_type` was set to
            ThreadPage. None if no home author usernames should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If `__authors_usernames` is not an instance of a list or an element is not an instance of str.
        """
        return self.__authors_usernames

    @property
    def authors_nrof_posts(self) -> t.Union[t.List[int], None]:
        """Gets number of posts of the authors stored in the `__authors_nrof_posts` attribute.
        Returns
        -------
        list of int | None
            List of the number of posts on the platform of the authors of the posts of the thread on the last parsed
            page where `page_type` was set to ThreadPage. Follows the same order as `__authors_usernames`. None if no
            number of posts of the authors should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If `__authors_nrof_posts` is not an instance of a list or an element is not an instance of int.
        """
        return self.__authors_nrof_posts

    @property
    def authors_popularity(self) -> t.Union[t.List[int], None]:
        """Gets the popularity of the authors stored in the `__authors_popularity` attribute.

        Returns
        -------
        list of int
            List of the popularity score on the platform of the authors of the posts of the thread on the last parsed
            page where `page_type` was set to ThreadPage. Follows the same order as `__authors_usernames`. None if no
            author popularity should be on the page or if it could not be found. Subject to change if not all platforms
            adopt a score system with numbers but with ranks.

        Raises
        ------
        ValueError
            If `__authors_popularity` is not an instance of a list or an element is not an instance of int.
        """
        return self.__authors_popularity

    @property
    def authors_registration_date(self) -> t.Optional[t.List[t.Union[datetime, str]]]:
        """Gets the registration dates of the authors stored in the `__authors_registration_date` attribute.

        Returns
        -------
        t.Optional[t.List[t.Union[datetime, str]]]
            List of the registration dates of the authors of the posts of the thread on the last parsed page where
            `page_type` was set to ThreadPage. Follows the same order as `__authors_usernames`, but elements may be
            missing, which cannot be avoided due to date conversion failing for numerous reasons. None if no
            registration dates should be on the page or if it could not be found. The registration dates could be
            expressed also as strings when no parsing of the dates is performed.

        Raises
        ------
        ValueError
            If `__authors_registration_date` is not an instance of a list or an element is not an instance of
            datetime.
        """
        return self.__authors_registration_date

    @property
    def authors_emails(self) -> t.Union[t.List[str], None]:
        """Gets the email addresses of the authors stored in the `__authors_emails` attribute.

        Returns
        -------
        list of str
            List of the email addresses of the authors of the posts of the thread on the last parsed page where
            `page_type` was set to ThreadPage. Follows the same order as `__authors_usernames`. None if no email
            addresses should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If `__authors_emails` is not an instance of a list or an element is not an instance of str.
        """
        return self.__authors_emails

    @property
    def thread_title(self) -> t.Union[str, None]:
        """Gets the title of the thread stored in the `__thread_title` attribute.

        Returns
        -------
        str
            Title of the thread on the last parsed page where `page_type` was set to ThreadPage. None if no thread title
            should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If `__thread_title` is not an instance of str.
        """
        return self.__thread_title

    @property
    def thread_section(self) -> t.Union[str, None]:
        """Gets the section to which the thread belongs stored in the `__thread_section` attribute.

        Returns
        -------
        str
            The title of the section to which the thread on the last parsed page where `page_type` was set to
            ThreadPage belongs. None if no section should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If `__thread_section` is not an instance of str.
        """
        return self.__thread_section

    @property
    def thread_age(self) -> t.Union[datetime, None]:
        """Gets the starting date of the thread stored in the `__thread_age` attribute.

        Returns
        -------
        datetime
            The date of the first post of the thread on the last parsed page where `page_type` was set to ThreadPage.
            None if no starting date should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If `__thread_age` is not an instance of datetime.
        """
        return self.__thread_age

    @property
    def posts_dates(self) -> t.Optional[t.List[t.Union[datetime, str]]]:
        """Gets the dates of the posts of the thread stored in the `__posts_dates` attribute.

        Returns
        -------
        t.Optional[t.List[t.Union[datetime, str]]]
            List of dates of the posts of the thread on the last parsed page where `page_type` was set to ThreadPage.
            None if no post dates should be on the page or if it could not be found. The post dates could be expressed
            also as strings when no parsing of the dates is performed.

        Raises
        ------
        ValueError
            If `__posts_date` is not an instance of a list or an element is not an instance of datetime.
        """
        return self.__posts_dates

    @property
    def posts_contents(self) -> t.Union[t.List[str], None]:
        """Gets the contents of the posts of the thread stored in the `__posts_contents` attribute.

        Returns
        -------
        list of str
            List of the contents of the posts of the thread on the last parsed page where `page_type` was set to
            ThreadPage. Follows the same order as the `__posts_dates` attribute. None if no post contents should be on
            the page or if it could not be found.

        Raises
        ------
        ValueError
            If `__posts_contents` is not an instance of a list or an element is not an instance of str.
        """
        return self.__posts_content

    @property
    def post_count(self) -> t.Union[int, None]:
        """Gets the amount of posts in the current thread stored in the `__post_count` attribute.

        Returns
        -------
        int
            How many posts are in the current thread on the last parsed page where `page_type` was set to ThreadPage.
            None if no posts should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If `__post_count` is not an instance of int.
        """
        return self.__post_count

    @property
    def posts_per_page(self) -> t.Union[int, None]:
        """Gets the number of posts expected on a single page, stored in the `__posts_per_page` attribute.

        Returns
        -------
        int
            The number of posts expected on the page. -1 if somehow the number of expected posts could not be
            determined. None if some unforeseen error occurs.
        """
        return self.__posts_per_page

    @property
    def nrof_words(self) -> t.Union[int, None]:
        """Gets the number of words on the page stored in the `__nrof_words` attribute.

        Returns
        -------
        int
            The number of readable words on the last parsed page. -1 if the number of words could not be determined.
            Might only be relevant when the `page_type` attribute was set to ThreadPage but is updated when parsing
            other types of pages as well. There should in principle never be the case that this is None but it could
            happen due to unforseen errors. Prepare for this situation!

        Raises
        ------
        ValueError
            If `__post_count` is not an instance of int.
        """
        return self.__nrof_words

    @property
    def structure(self) -> t.Union[t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]], None]:
        """Get the structure that InterpreterData uses.

        Returns
        ------
        dict<PageType, dict<StructuralElement, ResourceIdentifier>> | None
            The structure used by InterpreterData, None if improperly initialised."""
        return self.__structure

    @structure.setter
    def structure(self, struct: t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]]):
        """Set the structure that InterpreterData uses.

        Parameters
        ------
        struct : dict<PageType, dict<StructuralElement, ResourceIdentifier>>
            The structure to be used by InterpreterData."""
        verify_struct(struct)
        self.__structure = struct
