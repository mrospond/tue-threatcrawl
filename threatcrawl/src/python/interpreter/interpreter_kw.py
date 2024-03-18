"""Class that locates the keywords on a web page."""

from config.link_follow_policy import LinkFollowPolicy
from enums import Relevance
import typing as t


class InterpreterKW:
    """Class that locates the keywords on a web page and determines the page's relevancy.

    This class locates the keywords on a web page and determines the page's relevancy. The page relevancy depends on
    the link follow policy and on the found relevant keywords and the found blacklisted keywords.

    Attributes
    ---------
    __page_relevancy : Relevance
        The relevancy status of the page. Should only be set if `thread_titles` is None when parse_page is called.
    __threads_relevancy : list of Relevance
        The relevancy status of the threads in the list. Should only be set if `thread_titles` is not None when
        parse_page is called.
    __relevant_kws : list of str
        List of relevant keywords.
    __blacklisted_kws : list of str
        List of blacklisted keywords.
    __link_policy : LinkFollowPolicy
        Link policy to follow.

    Raises
    ------
    ValueError
        If `structure` is not a dictionary of <StructuralElement, ResourceIdentifier> pairs.
    """

    def __init__(self):
        self.__page_relevancy = None
        self.__threads_relevancy = None
        self.__relevant_kws = None
        self.__blacklisted_kws = None
        self.__link_policy = None

    def parse_page(self, thread_titles: t.Union[t.List[str], None], thread_title: t.Union[str, None],
                   posts_content: t.Union[t.List[str], None]):
        """Parse the supplied web page according to the known platform structure to identify the keywords on the page.

        The keywords that are present on the page combined with the configured link follow policy determine how relevant
        the page is and influence the decision to continue crawling this thread (if this page is a thread) or whether to
        avoid this thread in the future. The page relevancy is set after this function has returned.

        Parameters
        ---------
        thread_titles : t.Union[t.List[str], None]
            The list of threads to crawl in the case of a section page. None if the page is a thread page.
        thread_title : t.Union[str, None]
            The title of the thread in the case of a thread page. None if the page is a section page.
        posts_content : t.Union[t.List[str], None]
            The list of posts of the thread in the case of a thread page. None if the page is a section page.
        """

        # If there are thread_titles, then we're in a Section or Subsection page.
        if thread_titles is not None:
            self.__threads_relevancy = []
            self.__page_relevancy = None
            # We're in the case of looking at blacklisted keywords
            if self.__link_policy == LinkFollowPolicy.FOLLOW_ALL:
                # This is a SectionPage or a SubsectionPage, so look for blacklisted keywords in the titles
                for title in thread_titles:
                    relevance = self.__return_relevancy_from_list(self.__blacklisted_kws, title, Relevance.BLACKLISTED)
                    # No blacklisted kw found, so it is good to go.
                    if relevance == Relevance.UNKNOWN:
                        relevance = Relevance.RELEVANT
                    self.__threads_relevancy.append(relevance)
            # We're in the case of focussed crawling
            else:
                for title in thread_titles:
                    relevance = self.__return_relevancy_from_list(self.__relevant_kws, title, Relevance.RELEVANT)
                    # No blacklisted kw found, so it is good to go.
                    if relevance == Relevance.UNKNOWN:
                        relevance = Relevance.IRRELEVANT
                    self.__threads_relevancy.append(relevance)

        # Else, we're within a thread.
        if thread_title is not None and posts_content is not None:
            # The only use case when within a thread is to abort crawling if blacklisted keywords are encountered.
            # At first, the page relevancy is unknown and the threads relevancy is irrelevant.
            self.__page_relevancy = Relevance.RELEVANT
            self.__threads_relevancy = None

            # Check for a blacklisted keyword in the posts.
            for post in posts_content:
                self.__check_relevancy_from_list(self.__blacklisted_kws, post, Relevance.BLACKLISTED)

    @staticmethod
    def __check_for_word(kw: str, text: str) -> bool:
        """Checks for a given post whether there is a keyword present.

        Both `kw` and `text` are given a space at the start and end of the string to ensure only words are found, and
        not parts of a word. So, if 'gun' is the keyword, it is found in 'I have a gun', but not in 'It has begun'.
        The user should take care of edge cases, such as plural, punctuation, etc.

        Parameters
        ---------
        kw : str
            The keyword to look for
        text : str
            The string where the keyword is looked for

        Returns
        ---------
        bool
            Whether the `kw` is found in `post`
        """
        return kw.lower() in text.lower()

    def __check_relevancy_from_list(self, keywords: t.List[str], text: str, outcome: Relevance) -> bool:
        """Checks for a given list whether a keyword is present. Will set page_relevancy to the expected outcome.

        This method will go over all keywords in a list and checks whether the keyword appears in a string. If this is
        the case, the expected PageRelevancy is set and true is returned to indicate the word was found.

        Parameters
        --------
        keywords : list of str
            The list of keywords that are to be looked for
        text : str
            The text to find the keywords in
        outcome : PageRelevancy
            If a word is found, this should be the new PageRelevancy

        Returns
        ---------
        bool
            Whether a keyword from the list is found in the text

        """
        for kw in keywords:
            if self.__check_for_word(kw, text):
                self.__page_relevancy = outcome
                return True
        return False

    def __return_relevancy_from_list(self, keywords: t.List[str], text: str, outcome: Relevance) -> Relevance:
        """Checks for a given list whether a keyword is present. Will return page_relevancy with the expected outcome.
        if a keyword is present, otherwise returns unknown.

        This method will go over all keywords in a list and checks whether the keyword appears in a string. If this is
        the case, the expected PageRelevancy is returned to indicate that the word was found. If this is not the case,
        Relevance.UNKNOWN is returned.

        Parameters
        --------
        keywords : list of str
            The list of keywords that are to be looked for.
        text : str
            The text to find the keywords in.
        outcome : PageRelevancy
            If a word is found, this should be the returned Relevance.

        Returns
        ---------
        Relevance
            Returns the expected Relevance (`outcome`) is a keyword was found in the string or Relevance.UNKNOWN if not.

        """
        for kw in keywords:
            if self.__check_for_word(kw, text):
                return outcome
        return Relevance.UNKNOWN

    @property
    def page_relevancy(self) -> t.Union[Relevance, None]:
        """Get the page relevancy of the last parsed page.

        Returns
        ------
        Relevance
            How relevant the last parsed page is according to the link follow policy and the keywords present on the
            page.

        Raises
        ------
        ValueError
            If the attribute is not an instance of Relevance.
        """
        if self.__page_relevancy is None:
            return self.__page_relevancy
        elif not isinstance(self.__page_relevancy, Relevance):
            raise ValueError("The page relevancy is not an instance of Relevance")
        else:
            return self.__page_relevancy

    @page_relevancy.setter
    def page_relevancy(self, relevancy: Relevance):
        """Set the page relevancy of the last parsed page. Only used for testing

        Parameters
        ------
        relevancy : Relevance
            How relevant the last parsed page is according to the link follow policy and the keywords present on the
            page.
        """
        self.__page_relevancy = relevancy

    @property
    def threads_relevancy(self) -> t.Union[t.List[Relevance], None]:
        """Get the threads relevancy of the last parsed page.

        Returns
        ------
        list of Relevance
            How relevant the threads on the last parsed page are according to the link follow policy and the keywords
            present in the titles of the threads.

        Raises
        ------
        ValueError
            If the attribute is not an instance of list or an element of the list is not an instance of Relevance.
        """
        if self.__threads_relevancy is None:
            return self.__threads_relevancy
        elif not isinstance(self.__threads_relevancy, list):
            raise ValueError("The threads relevancy is not an instance of list")
        elif not all(isinstance(elm, Relevance) for elm in self.__threads_relevancy):
            raise ValueError("An element of threads relevancy is not an instance of Relevance")
        else:
            return self.__threads_relevancy

    @property
    def relevant_kw(self):
        if self.__relevant_kws is None:
            return self.__relevant_kws
        elif not isinstance(self.__relevant_kws, list):
            raise ValueError("The list of relevant keywords is not a list")
        elif not all(isinstance(elm, str) for elm in self.__relevant_kws):
            raise ValueError("An element of relevant_kws is not a string")
        else:
            return self.__relevant_kws

    @relevant_kw.setter
    def relevant_kw(self, kws):
        """Set the list of relevant keywords.

        Parameters
        ---------
        kws: list of str
            List of relevant keywords to set. Overwrites the current list of relevant keywords.
        """
        self.__relevant_kws = kws

    @property
    def blacklisted_kw(self):
        if self.__blacklisted_kws is None:
            return self.__blacklisted_kws
            # raise ValueError("There is no list of blacklisted keywords")
        elif not isinstance(self.__blacklisted_kws, list):
            raise ValueError("The list of blacklisted keywords is not a list")
        elif not all(isinstance(elm, str) for elm in self.__blacklisted_kws):
            raise ValueError("An element of blacklisted_kws is not a string")
        else:
            return self.__blacklisted_kws

    @blacklisted_kw.setter
    def blacklisted_kw(self, kws):
        """Set the list of blacklisted keywords.

        Parameters
        ---------
        kws: list of str
            List of blacklisted keywords to set. Overwrites the current list of blacklisted keywords.
        """
        self.__blacklisted_kws = kws

    @property
    def link_policy(self):
        if self.__link_policy is None:
            return self.__link_policy
        elif not isinstance(self.__link_policy, LinkFollowPolicy):
            raise ValueError("The link follow policy is not a LinkFollowPolicy")
        else:
            return self.__link_policy

    @link_policy.setter
    def link_policy(self, policy):
        """Set the link follow policy.

        Parameters
        ---------
        policy
            The link follow policy to set. Overwrites the current link follow policy.
        """
        self.__link_policy = policy
