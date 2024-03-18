"""Class that houses the enum to indicate thread status"""
from enum import Enum


class ThreadStatus(Enum):
    """Class that houses the enum to indicate thread status.

    The crawler needs to know the status of the thread to make an adequate decision to decide whether to (re)crawl a
    thread or whether it can be skipped.


    UNKNOWN
        When the thread is not in the database or the ThreadStatus could not be determined.
    PARSED
        When the thread is in the database, has been parsed completely in the past and has not been updated since the
        last time it was parsed.
    UPDATED
        When the thread is in the database, has been parsed completely in the past and has been updated since the last
        time it was parsed.
    """
    UNKNOWN = 1
    PARSED = 2
    UPDATED = 3
