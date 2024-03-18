"""Class that houses the configuration to do with crawling."""


class Crawling:
    """Class that houses the settings for anything to do with crawling.

    This class houses the settings that have to do with the crawling process itself. Settings that are included in this
    class are the platform to crawl, the blacklisted keywords, the relevant keywords, the link follow policy, the
    maximum thread age, the maximum thread length and the reading speed range.

    Attributes
    ---------
    platform : str
        URL of the platform to crawl.
    platform_login : str
        URL of the login page of the platform to crawl.
    platform_section : str
        URL of a section page of the target platform.
    platform_subsection : str
        URL of a subsection page of the target platform.
    platform_thread : str
        URL of a thread page of the target platform.
    tor_path : str
        absolute path leading to the TOR Browser installation.
    blacklisted_keywords : list<str>
        List of blacklisted keywords. When these words are encountered, we stop parsing the thread or will not crawl a
        thread that contains any of these words.
    relevant_keywords : list<str>
        List of relevant keywords. How they are used depends on the link follow policy. If all links are followed, then
        the relevant keywords are not needed or used. If only the relevant links are followed, then the relevant
        keywords determine which threads are relevant and should be crawled.
    link_follow_policy : LinkFollowPolicy
        The link follow policy which can be 'follow all links' or 'follow only relevant links'.
    max_thread_age : datetime
        The maximum amount of time there may be between the first post of the thread and the date the crawler crawls the
        thread.
    max_thread_length : int
        The maximum amount of posts that will be crawled per thread.
    reading_speed_range : tuple<int, int>
        A tuple representing the reading speed range, where the first element is the lower bound and the second element
        is the upper bound in words per minute (WPM).
    delay : tuple <int, int>
        A tuple representing the normal delay range for fetching non-ThreadPages, The first element is the lower bound
        and the second element is the upper bound in seconds.
    need_training : bool
        A boolean specifying if it is currently needed to execute a training session.
    timeout : int
        The maximum amount of seconds to wait before retrying to load a page.
    download_timeout : int
        The maximum amount of seconds to wait before retrying to download a page.
    """

    def __init__(self):
        self.platform = None
        self.platform_login = None
        self.platform_section = None
        self.platform_subsection = None
        self.platform_thread = None
        self.tor_path = None
        self.blacklisted_keywords = None
        self.relevant_keywords = None
        self.link_follow_policy = None
        self.max_thread_age = None
        self.max_thread_length = None
        self.reading_speed_range = None
        self.delay = None
        self.need_training = None
        self.timeout = None
        self.download_timeout = None
