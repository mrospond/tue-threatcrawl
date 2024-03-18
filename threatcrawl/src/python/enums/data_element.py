"""File containing the DataElement enum."""
from enums.structural_element import StructuralElement


class DataElement(StructuralElement):
    """Class containing the types of data-carrying elements on a web page that are of interest.

    AuthorUsername
        The username of an author.
    AuthorNrOfPosts
        The number of posts an author has posted on the platform.
    AuthorPopularity
        The popularity of an author.
    AuthorRegistrationDate
        The date at which an author created their profile.
    AuthorEmail
        The email address of an author.
    ThreadTitle
        The title of a thread. We assume this can also be clicked to go to the corresponding thread.
    ThreadSection
        The section to which a thread belongs.
    ThreadAge
        The age of a thread.
    SectionTitle
        The title of a section. We assume this can also be clicked to go to the corresponding section.
    SubsectionTitle
        The title of a subsection. We assume this can also be clicked to go to the corresponding subsection.
    PostDate
        The date at which a post was posted.
    PostContent
        The content of a post.
    """
    # ---- AUTHOR ----
    AuthorUsername = 1
    AuthorNrOfPosts = 2
    AuthorPopularity = 3
    AuthorRegistrationDate = 4
    AuthorEmail = 5
    # ---- THREAD ----
    ThreadTitle = 6
    ThreadSection = 7
    ThreadAge = 8
    # ---- SECTION ----
    SectionTitle = 9
    # ---- SUBSECTION ----
    SubsectionTitle = 10
    # ---- POST ----
    PostDate = 11
    PostContent = 12
