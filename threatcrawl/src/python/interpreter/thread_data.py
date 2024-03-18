"""Class containing all the information the crawler needs to make a decision on a thread page"""
from trainer.resource_identifier import ResourceIdentifier
from .parsed_data import ParsedData
from enums import Relevance, CaptchaType, PageType
from datetime import datetime


class ThreadData(ParsedData):
    """Class containing all the information the crawler needs to make a decision on a thread page.

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
    page_relevancy : Relevance
        How relevant the current page is based on the found keywords and the link follow policy
    nrof_posts_current_thread : int
        How many posts have been parsed in the current thread. Is non-negative unless this could not be retrieved, then
        it is -1.
    thread_age : datetime
        The date of the first post of the thread. Defines how old the thread is.
    is_thread_complete : bool
        Whether the thread has been crawled completely. False if not, True if so.

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
    page_relevancy : Relevance
        How relevant the current page is based on the found keywords and the link follow policy
    nrof_posts_current_thread : int
        How many posts have been parsed in the current thread. Is non-negative unless this could not be retrieved, then
        it is -1.
    thread_age : datetime
        The date of the first post of the thread. Defines how old the thread is.
    is_thread_complete : bool
        Whether the thread has been crawled completely. False if not, True if so.

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
                 page_relevancy: Relevance = None, nrof_posts_current_thread: int = -1,
                 thread_age: datetime = None, is_thread_complete: bool = False):
        super().__init__(page_type, next_page_button=next_page_button, prev_page_button=prev_page_button,
                         section_button=section_button, home_button=home_button, login_button=login_button,
                         goto_login_button=goto_login_button, first_thread_page_button=first_thread_page_button,
                         nrof_words_on_page=nrof_words_on_page, captcha_on_page=captcha_on_page,
                         captcha_type=captcha_type, captcha_location=captcha_location, username_field=username_field,
                         password_field=password_field, is_badly_formatted=is_badly_formatted)
        self.page_relevancy = page_relevancy
        self.nrof_posts_current_thread = nrof_posts_current_thread
        self.thread_age = thread_age
        self.is_thread_complete = is_thread_complete
