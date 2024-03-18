"""File containing the NavigationalElement enum."""
from enums.structural_element import StructuralElement


class NavigationalElement(StructuralElement):
    """Class containing the types of navigational elements on a web page that are of interest.

    HomeButton
        A button that can be used to return to the front page.
    NextPageButton
        A button that can be used to go to the next page of a section, subsection or thread.
    PreviousPageButton
        A button that can be used to go to the previous page of a section, subsection or thread.
    LoginButton
        A button that can be used to go to the log-in page.
    FirstThreadPageButton
        A button that can be used to move to the first page of a thread.
    """
    HomeButton = 1
    NextPageButton = 2
    PreviousPageButton = 3
    LoginButton = 4
    FirstThreadPageButton = 5
