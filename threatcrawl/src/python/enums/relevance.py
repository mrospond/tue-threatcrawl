from enum import Enum


class Relevance(Enum):
    """Class to house the enum to indicate thread relevancy.

    This class contains the different relevancy indicators for a thread.

    BLACKLISTED
        Thread contains a blacklisted keyword and shall not be crawled further nor recrawled in the future.
    IRRELEVANT
        Thread does not contain blacklisted keywords nor relevant keywords and can therefore be ignored.
    RELEVANT
        Thread contains a relevant keyword and shall be crawled completely and possibly recrawled in the future.
    UNKNOWN
        Could not be determined what relevancy the thread has. Most likely due to it not having been crawled before.
        Might also indicate a badly formatted page.
    """
    BLACKLISTED = 'blacklisted'
    RELEVANT = 'relevant'
    IRRELEVANT = 'irrelevant'
    UNKNOWN = 'unknown'
