"""Class containing all the information the crawler needs to make a decision on a section page"""
from .parsed_data import ParsedData
from enums import CaptchaType, ThreadStatus, Relevance, PageType
from trainer.resource_identifier import ResourceIdentifier
import typing as t


class SectionData(ParsedData):
    """Class containing all the information the crawler needs to make a decision on a section page.

    Parameters
    ---------
    page_type : PageType
        The type of page for which the other attributes are filled in.
    next_page_button : ResourceIdentifier
        The location on the web page where the next page button is.
    prev_page_button : ResourceIdentifier
        The location on the web page where the previous page button is.
    section_button : ResourceIdentifier
        The location on the web page where the section button is. This button is used to go to the (sub)sections page.
        Can be None if it could not be found or is not supposed to be present.
    home_button : ResourceIdentifier
        The location on the web page where the home button is. This button is used to go to the home page.
    login_button : ResourceIdentifier
        The location on the web page where the login button is. This button is used to log in.
    goto_login_button : ResourceIdentifier
        The location on the web page where the button to go to the login button is.
    first_thread_page_button : ResourceIdentifier
        The location on the web page where the button to go to the first page of a thread is.
    nrof_words_on_page : int
        How many readable words are on the page. Used in the fetch delay calculations. Is always non-negative.
    captcha_on_page : bool
        Whether a CAPTCHA is present on the page or not.
    captcha_type : CaptchaType
        The type of CAPTCHA present on the page. Is only set if 'captcha_on_page' is set to true.
    captcha_location : ResourceIdentifier
        The location on the web page where the CAPTCHA is. Is only set if 'captcha_on_page' is set to true.
    username_field : ResourceIdentifier
        The location on the web page where the username field for logging in is.
    password_field : ResourceIdentifier
        The location on the web page where the password field for logging in is.
    is_badly_formatted : bool
        Whether the page is badly formatted or not
    thread_list : ResourceIdentifier
        ResourceIdentifier that finds the list of threads that need to be crawled. One instance should be able to find
        all threads. Should be None if `section_list`or `subsection_list` is a ResourceIdentifier.
    thread_status : list of ThreadStatus
        List of statuses of the threads that need to be crawled is already parsed in the past, has been updated since
        the last parse or have not been parsed before. Is assumed to follow the same order as `thread_list`. Should only
        set if `thread_list` is not None.
    thread_relevancy : list of Relevance
        List of relevancies of the threads that need to be crawled. Lists whether the thread is blacklisted, irrelevant,
        relevant or unknown. Is assumed to follow the same order as `thread_list`. Should only be set if `thread_list`
        is not None.
    section_list : ResourceIdentifier
        ResourceIdentifier that finds the list of sections that need to be crawled. Should be None if `thread_list`
        or `subsection_list` is a ResourceIdentifier.
    subsection_list : ResourceIdentifier
        ResourceIdentifier that finds the list of subsections that need to be crawled. Should be None if
        `thread_list` or `section_list` is a ResourceIdentifier.

    Attributes
    ---------
    page_type : PageType
        The type of page for which the other attributes are filled in.
    next_page_button : ResourceIdentifier
        The location on the web page where the next page button is.
    prev_page_button : ResourceIdentifier
        The location on the web page where the previous page button is.
    section_button : ResourceIdentifier
        The location on the web page where the section button is. This button is used to go to the (sub)sections page.
        Can be None if it could not be found or is not supposed to be present.
    home_button : ResourceIdentifier
        The location on the web page where the home button is. This button is used to go to the home page.
    login_button : ResourceIdentifier
        The location on the web page where the login button is. This button is used to log in.
    goto_login_button : ResourceIdentifier
        The location on the web page where the button to go to the login button is.
    first_thread_page_button : ResourceIdentifier
        The location on the web page where the button to go to the first page of a thread is.
    nrof_words_on_page : int
        How many readable words are on the page. Used in the fetch delay calculations. Is always non-negative.
    captcha_on_page : bool
        Whether a CAPTCHA is present on the page or not.
    captcha_type : CaptchaType
        The type of CAPTCHA present on the page. Is only set if 'captcha_on_page' is set to true.
    captcha_location : ResourceIdentifier
        The location on the web page where the CAPTCHA is. Is only set if 'captcha_on_page' is set to true.
    username_field : ResourceIdentifier
        The location on the web page where the username field for logging in is.
    password_field : ResourceIdentifier
        The location on the web page where the password field for logging in is.
    is_badly_formatted : bool
        Whether the page is badly formatted or not
    thread_list : ResourceIdentifier
        ResourceIdentifier that finds the list of threads that need to be crawled. One instance should be able to find
        all threads. Should be None if `section_list`or `subsection_list` is a ResourceIdentifier.
    thread_status : list of ThreadStatus
        List of statuses of the threads that need to be crawled is already parsed in the past, has been updated since
        the last parse or have not been parsed before. Follows the same order as `thread_list`. Only set if
        `thread_list` is not None.
    thread_relevancy : list of Relevance
        List of relevancies of the threads that need to be crawled. Lists whether the thread is blacklisted, irrelevant,
        relevant or unknown. Follows the same order as `thread_list`. Only set if `thread_list` is not None.
    section_list : ResourceIdentifier
        ResourceIdentifier that finds the list of sections that need to be crawled. Should be None if `thread_list`
        or `subsection_list` is a ResourceIdentifier.
    subsection_list : ResourceIdentifier
        ResourceIdentifier that finds the list of subsections that need to be crawled. Should be None if
        `thread_list` or `section_list` is a ResourceIdentifier.

    Notes
    -----
    Do note that every attribute can be None if errors occur during the parsing process. Therefore, before directly
    accessing an attribute always check if it is None or not!
    """

    def __init__(self, page_type: PageType, next_page_button: ResourceIdentifier = None,
                 prev_page_button: ResourceIdentifier = None, section_button: ResourceIdentifier = None,
                 home_button: ResourceIdentifier = None, login_button: ResourceIdentifier = None,
                 goto_login_button: ResourceIdentifier = None, first_thread_page_button: ResourceIdentifier = None,
                 nrof_words_on_page: int = -1, captcha_on_page: bool = False, captcha_type: CaptchaType = None,
                 captcha_location: ResourceIdentifier = None, username_field: ResourceIdentifier = None,
                 password_field: ResourceIdentifier = None, is_badly_formatted: bool = False,
                 thread_list: ResourceIdentifier = None, thread_status: t.List[ThreadStatus] = None,
                 thread_relevancy: t.List[Relevance] = None, section_list: ResourceIdentifier = None,
                 subsection_list: ResourceIdentifier = None):
        super().__init__(page_type, next_page_button=next_page_button, prev_page_button=prev_page_button,
                         section_button=section_button, home_button=home_button, login_button=login_button,
                         goto_login_button=goto_login_button, first_thread_page_button=first_thread_page_button,
                         nrof_words_on_page=nrof_words_on_page, captcha_on_page=captcha_on_page,
                         captcha_type=captcha_type, captcha_location=captcha_location, username_field=username_field,
                         password_field=password_field, is_badly_formatted=is_badly_formatted)
        self.thread_list = thread_list
        self.thread_status = thread_status
        self.thread_relevancy = thread_relevancy
        self.section_list = section_list
        self.subsection_list = subsection_list
