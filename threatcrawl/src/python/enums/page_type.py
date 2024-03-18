"""File containing the PageType class."""
from enum import Enum


class PageType(Enum):
    """Class containing the different types of pages we are interested in.

    FrontPage
        The front page of a platform. This page usually contains links to many other pages on the platform, and
        is usually the first page that a user encounters when visiting a platform for the first time.
    LoginPage
        A page on which the user can log-in.
    SectionPage
        A page containing links to `ThreadPage`s sharing a common topic, or `SubsectionPage`s.
    SubsectionPage
        A page containing links to `ThreadPage`s sharing a common topic.
    ThreadPage
        A page containing a thread (a sequence of posts).
    """
    FrontPage = 1
    LoginPage = 2
    SectionPage = 3
    SubsectionPage = 4
    ThreadPage = 5
