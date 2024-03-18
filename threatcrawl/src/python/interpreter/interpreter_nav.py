"""Class that locates the navigational elements on a web page."""
from trainer.resource_identifier import ResourceIdentifier
from enums import StructuralElement, NavigationalElement, DataElement, InputElement, PageType
from .interpreter_utils import verify_struct
from utils import Logger
import typing as t


class InterpreterNav:
    """Class that locates the navigational elements on a web page.

    This class locates navigational elements on a web page. Think about the next page button, the previous page button,
    the home page button and more.

    Parameters
    ----------
    structure : t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]]
        The platform structure of the platform to which all the web pages belong that need to be parsed.

    Attributes
    ---------
    __structure : t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]] pairs
        The platform structure of the platform to which all the web pages belong that need to be parsed. May only be a
        non-empty dictionary.
    __home_button : ResourceIdentifier
        Class that gets the location of the button to return home.
    __next_page_button : ResourceIdentifier
        Class that gets the location of the button to go to the next page of the thread/section.
    __prev_page_button : ResourceIdentifier
        Class that gets the location of the button to go to the previous page of the thread/section.
    __goto_login_button : ResourceIdentifier:
        Class that gets the location of the button to go to the login page.
    __login_button : ResourceIdentifier
        Class that gets the location of the button to submit login information on the page.
    __login_username : ResourceIdentifier
        Class that gets the location of the field to fill in the username to log in.
    __login_password : ResourceIdentifier
        Class that gets the location of the field to fill in the password to log in.
    __first_thread_page_button : ResourceIdentifier
        Class that gets the location of the first page button of a thread.
    is_badly_formatted : bool
        Whether everything could be identified or not. True if everything could not be identified, false if not.

    Raises
    ------
    ValueError
        If `structure` is not a dictionary of <StructuralElement, ResourceIdentifier> pairs.
    """

    def __init__(self, structure: t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]]):
        verify_struct(structure)

        self.__structure = structure
        self.__home_button = None
        self.__next_page_button = None
        self.__prev_page_button = None
        self.__goto_login_button = None
        self.__login_button = None
        self.__login_username = None
        self.__login_password = None
        self.__first_thread_page_button = None
        self.is_badly_formatted = None

    def parse_page(self, page_type: PageType) -> bool:
        """Parse the supplied web page according to the known platform structure to identify the navigational elements.

        All the attributes that can be set according to the platform structure will be set when this function is called.
        If one of the elements should be present but could not be located, the `is_badly_formatted` attribute is set
        to False, which is otherwise set to True.

        Parameters
        ---------
        page_type : PageType
            The type of page that is being parsed.

        Returns
        ------
        bool
            True if parsing the page is completed, False if the parsing did not complete. Note that completing parsing
            is different from extracting all the relevant data. A page can be parsed completely without all the
            information being extracted (either because it doesn't exist or because this page is badly formatted).
        """
        # Reset everything to None
        self.__next_page_button = None
        self.__prev_page_button = None
        self.__home_button = None
        self.__login_button = None
        self.__goto_login_button = None
        self.__login_username = None
        self.__login_password = None
        self.__first_thread_page_button = None

        # Find buttons
        old = True
        errors = False
        for key, value in self.__structure[page_type].items():
            # Skip non navigation stuff
            if not isinstance(key, NavigationalElement) and not isinstance(key, InputElement):
                if isinstance(key, DataElement):
                    if not (key == DataElement.SectionTitle or key == DataElement.SubsectionTitle):
                        continue
                else:
                    continue

            # Check if something is missing. If so then the page is badly formatted and not everything can be
            # reliably accessed :(
            # TODO: This is something that must be redesigned. Doesn't work as it should. For example, first page in a
            #  thread does not contain any previous page button, and this would mark the page as badly formatted.
            #  Furthermore, the logic of having a tolerance of 3 errors every 2 hours (completely arbitrary),
            #  implemented in interpreter.py, self.__determine_badly_formatted(parsed_data), is broken. It doesn't
            #  reset this count in a rolling fashion.
            return_value = value
            # result = value.get_elements(page)
            # if not result:
            #     self.is_badly_formatted = True
            #     old = False
            #     return_value = None

            if isinstance(key, NavigationalElement):
                if key == NavigationalElement.NextPageButton:
                    self.__next_page_button = return_value
                elif key == NavigationalElement.PreviousPageButton:
                    self.__prev_page_button = return_value
                elif key == NavigationalElement.HomeButton:
                    self.__home_button = return_value
                elif key == NavigationalElement.LoginButton:
                    self.__goto_login_button = return_value
                elif key == NavigationalElement.FirstThreadPageButton:
                    self.__first_thread_page_button = return_value
                else:
                    Logger.log("interpreter", "Found " + str(key) + " which is not yet implemented!")
                    errors = True
            elif isinstance(key, InputElement):
                # Only need UsernameInput, PasswordInput and SubmitLoginButton to log in
                if key == InputElement.UsernameInput or key == InputElement.PasswordInput or \
                        key == InputElement.SubmitLoginButton:
                    if key == InputElement.UsernameInput:
                        self.__login_username = return_value
                    elif key == InputElement.PasswordInput:
                        self.__login_password = return_value
                    elif key == InputElement.SubmitLoginButton:
                        self.__login_button = return_value
                    else:
                        Logger.log("interpreter", "Found " + str(key) + " which is not yet implemented!")
                        errors = True

        if old:
            self.is_badly_formatted = False

        return not errors

    @property
    def home_button(self) -> t.Union[ResourceIdentifier, None]:
        """Gets the location of the home button on the last parsed page as stored in the `__home_button` attribute.

        Returns
        -------
        ResourceIdentifier
            Class which contains the location of the home button on the last parsed page. None if no home button
            should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If the contents of `__home_button` are not None or an instance of a ResourceIdentifier.
        """
        if self.__home_button is None:
            return self.__home_button
        elif not isinstance(self.__home_button, ResourceIdentifier):
            raise ValueError("The home button location is not an instance of a ResourceIdentifier")
        else:
            return self.__home_button

    @property
    def next_page_button(self) -> t.Union[ResourceIdentifier, None]:
        """Gets the location of the next page button on the last parsed page as stored in the `__next_page_button`
        attribute.

        Returns
        -------
        ResourceIdentifier
            Class which contains the location of the next page button on the last parsed page. None if no next page
            button should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If the contents of `__next_page_button` are not None or an instance of a ResourceIdentifier.
        """
        if self.__next_page_button is None:
            return self.__next_page_button
        elif not isinstance(self.__next_page_button, ResourceIdentifier):
            raise ValueError("The next page button location is not an instance of a ResourceIdentifier")
        else:
            return self.__next_page_button

    @property
    def prev_page_button(self) -> t.Union[ResourceIdentifier, None]:
        """Gets the location of the previous page button on the last parsed page as stored in the `__prev_page_button`
        attribute.

        Returns
        -------
        ResourceIdentifier
            Class which contains the location of the previous page button on the last parsed page. None if no
            previous page button should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If the contents of `__prev_page_button` are not None or an instance of a ResourceIdentifier.
        """
        if self.__prev_page_button is None:
            return self.__prev_page_button
        elif not isinstance(self.__prev_page_button, ResourceIdentifier):
            raise ValueError("The previous page button location is not an instance of a ResourceIdentifier")
        else:
            return self.__prev_page_button

    @property
    def login_button(self) -> t.Union[ResourceIdentifier, None]:
        """Gets the location of the login button on the last parsed page as stored in the `__login_button` attribute.

        Returns
        -------
        ResourceIdentifier
            Class which contains the location of the login button on the last parsed page. None if no login
            button should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If the contents of `__login_button` are not None or an instance of a ResourceIdentifier.
        """
        if self.__login_button is None:
            return self.__login_button
        elif not isinstance(self.__login_button, ResourceIdentifier):
            raise ValueError("The login button location is not an instance of a ResourceIdentifier")
        else:
            return self.__login_button

    @property
    def goto_login_button(self) -> t.Union[ResourceIdentifier, None]:
        """Gets the location of the goto login button on the last parsed page as stored in the `__goto_login_button`
        attribute.

        Returns
        -------
        ResourceIdentifier
            Class which contains the location of the goto login button on the last parsed page. None if no goto login
            button should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If the contents of `__goto_login_button` are not None or an instance of a ResourceIdentifier.
        """
        if self.__goto_login_button is None:
            return self.__goto_login_button
        elif not isinstance(self.__goto_login_button, ResourceIdentifier):
            raise ValueError("The goto login button location is not an instance of a ResourceIdentifier")
        else:
            return self.__goto_login_button

    @property
    def first_thread_page_button(self):
        """Gets the location of the first thread page button on the last parsed page as stored in the
        `__first_thread_page_button`attribute.

        Returns
        -------
        ResourceIdentifier
            Class which contains the location of the first thread page button on the last parsed page. None if no first
            thread page button should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If the contents of `__first_thread_page_button` are not None or an instance of a ResourceIdentifier.
        """
        if self.__first_thread_page_button is None:
            return self.__first_thread_page_button
        elif not isinstance(self.__first_thread_page_button, ResourceIdentifier):
            raise ValueError("The first thread page button location is not an instance of a ResourceIdentifier")
        else:
            return self.__first_thread_page_button

    @property
    def login_username(self) -> t.Union[ResourceIdentifier, None]:
        """Gets the location of the login username text field on the last parsed page as stored in the
        `__login_username` attribute.

        Returns
        -------
        ResourceIdentifier
            Class which contains the location of the login username text field on the last parsed page. None if no
            username text field should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If the contents of `__login_username` are not None or an instance of a ResourceIdentifier.
        """
        if self.__login_username is None:
            return self.__login_username
        elif not isinstance(self.__login_username, ResourceIdentifier):
            raise ValueError("The username text field location is not an instance of a ResourceIdentifier")
        else:
            return self.__login_username

    @property
    def login_password(self) -> t.Union[ResourceIdentifier, None]:
        """Gets the location of the login password text field on the last parsed page as stored in the
        `__login_password` attribute.

        Returns
        -------
        ResourceIdentifier
            Class which contains the location of the login password text field on the last parsed page. None if no
            password text field should be on the page or if it could not be found.

        Raises
        ------
        ValueError
            If the contents of `__login_password` are not None or an instance of a ResourceIdentifier.
        """
        if self.__login_password is None:
            return self.__login_password
        elif not isinstance(self.__login_password, ResourceIdentifier):
            raise ValueError("The password text field location is not an instance of a ResourceIdentifier")
        else:
            return self.__login_password

    @property
    def structure(self) -> t.Union[t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]], None]:
        """Get the structure that InterpreterData uses.

        Returns
        ------
        t.Union[t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]], None]
            The structure used by InterpreterData, None if improperly initialised."""
        return self.__structure

    @structure.setter
    def structure(self, struct: t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]]):
        """Set the structure that InterpreterData uses.

        Parameters
        ------
        struct : dict[PageType, dict[StructuralElement, ResourceIdentifier]]
            The structure to be used by InterpreterData."""
        verify_struct(struct)
        self.__structure = struct
