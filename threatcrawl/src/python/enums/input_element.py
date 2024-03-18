"""File containing the DataElement enum."""
from enums.structural_element import StructuralElement


class InputElement(StructuralElement):
    """Class containing the types of input-filed elements on a web page that are of interest.

    UsernameInput
        The input field which allows the user to enter their username or email.
    PasswordInput
        The input field which allows the user to enter their password.
    SearchInput
        The input field which allows the user to search the forum.
    SubmitLoginButton
        The button used to submit a log-in.
    """
    UsernameInput = 1
    PasswordInput = 2
    SearchInput = 3
    SubmitLoginButton = 4
