"""Class that houses the enum for the link follow policy"""
from enum import Enum


class LinkFollowPolicy(Enum):
    """Class that houses the enum for the link follow policy.

    The link follow policy dictates what to do with encountered links which link to the same platform. Links that link
    to another platform do not fall under this link follow policy.

    FOLLOW_ALL
        Follow all encountered links that link to the same platform.
    FOLLOW_RELEVANT
        Follow only links that link to the same platform that have a relevant keyword in plain text in them or have a
        relevant keyword in the first post of a thread (if the link links to a thread).
    """
    FOLLOW_ALL = 1
    FOLLOW_RELEVANT = 2
