"""File that contains methods that counts the amount of words there are on a page"""

from trainer.resource_identifier import ResourceIdentifier
from enums import PageType
from typing import Optional, List


def count_words(page_type: PageType, posts_content: Optional[List[str]], link_list: Optional[ResourceIdentifier],
                page: str) -> int:
    """Count the amount of words as instructed by the given InterpreterData.

    The words on a thread page are counted. If the post does not exist, or there is no post content, or the page is
    not a thread page, no words are counted and an error value is passed. A different error value is passed if the
    page is not a thread page and there are no more threads to process.

    Parameters
    ---------
    page_type : PageType
        The type of page that was last parsed.
    posts_content : Optional[List[str]]
        List of the contents of the posts in the thread on the last parsed page. Has the same order as
        `__posts_dates`.
    link_list : Optional[ResourceIdentifier]
        ResourceIdentifier that locates the titles of threads, names of sections or names of subsections that are
        recognised to be on the page. Only set if `__page_type` is not set to ThreadPage.
    page : str
        HTML of the page to which `thread_list` belongs.

    Returns
    ---------
    count : int
        The amount of words on the page. Negative in case of errors.
    """
    count = 0

    if page_type == PageType.ThreadPage:
        if posts_content is not None:
            for post in posts_content:
                # If we are on a thread page and there is post content, count the words in every post.
                # Due to the verify_posts_content method, all elements in posts_content are guaranteed not to be None
                count = count + len(post.split())
        else:
            # If we are on a thread page and posts_content is set to none, then we cannot determine the amount of
            # readable words on the page and set a non-sensible value.
            count = -1
    else:
        if link_list is not None and isinstance(link_list, ResourceIdentifier) and page is not None and \
                isinstance(page, str):
            # Retrieve HTML elements from ResourceIdentifier and strip tags.
            links = link_list.get_elements(page)
            for link in links:
                count += len(get_text_content(link).split())
        else:
            # Not on a ThreadPage and no links to read, or has no page to read from. Difficult to read words then...
            # Setting it to a non-sensible value. Note that missing data is not necessarily the case.
            count = -2
    return count


def verify_posts_content(page_type: PageType, posts_content: List[str]) -> Optional[List[str]]:
    """Verifies the posts_content.

    Only works for thread pages. On non-thread pages, return the current value of `posts_content`. On thread pages,
    it verifies that all posts are not None. If one of them is none, `posts_content` is set to None, since not all
    data could be retrieved. If all posts are not None, the `posts_content` is returned.

    Parameters
    ---------
    page_type : PageType
        The type of page that was last parsed.
    posts_content : t.List[str]
        List of the contents of the posts in the thread on the last parsed page.

    Returns
    ---------
    posts_content : t.Optional[t.List[str]]
        List of the contents of the posts in the thread on the last parsed page.
    """

    if page_type == PageType.ThreadPage and posts_content is not None:
        return posts_content


def interpret_count(count: int):
    """Interprets the word count and returns whether all data is complete.

    Depending on the given `count`, the result is interpreted. A count of -1 indicates that the data is incomplete.
    A count of -2 indicates that the current page is not a thread page and that there are no more threads to read.
    A non-negative count indicates that the number of words in the post has been counted correctly.

    Parameters
    ---------
    count : int
        The number of words that was counted in the post

    Returns
    ---------
    is_data_complete : bool
        Whether all the relevant information (determined by the value of the parent interpreter's `__page_type`
        attribute) could be extracted from the page. True if all information could be extracted, False if not.
        False indicates a badly formatted page or an incorrect platform structure.
    """

    return count != -1 and count != -2


def get_text_content(html: str):
    """Function that returns the content between two tags.

    Parameters
    ----------
    html : str
        The snippet of HTML containing the tag.

    Returns
    -------
    str
        The content between two tags.
    """

    return html.split('>')[1].split('<')[0]
