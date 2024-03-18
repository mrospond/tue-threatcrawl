"""Class that detects CAPTCHAs on web pages"""
from trainer.resource_identifier import ResourceIdentifier
from enums import StructuralElement, CaptchaType, PageType
from .honeypot_detector import detect_honeypot
from .interpreter_utils import verify_struct
import typing as t


class InterpreterCAPTCHA:
    """Class that detects CAPTCHAs on web pages.

    This class detects whether a CAPTCHA is on the page and where the CAPTCHA is located on the page, if present. The
    different types of CAPTCHA can also be distinguished, though not perfectly. The interpreter can detect reCAPTCHAs
    easily, as well as basic Honeypot implementations. Various implementations of the Word Problem CAPTCHA can also be
    found. Picture Identification CAPTCHAs are also detected.

    Simple Math CAPTCHAs cannot be distinguished. However, they are similar to Word Problem CAPTCHAs. Since we do not
    intend to solve the CAPTCHAs, but pass them to the user, there is no way to distinguish between the two. They are
    detected, since they are similar to the Word Problem CAPTCHA.
    Time Based CAPTCHAs are not detected. However, since the system does not instantly fill out forms, this CAPTCHA will
    not detect the system in the first place, so this is a non-issue.
    Sweet CAPTCHAs and Biometrics are rarely used and due to time constraints and complexity, it is not feasible to
    implement them.
    Picture Identification CAPTCHAs are also not detected, due to lack of information on them and time constraints.
    If a CAPTCHA that is not listed above appears on a page, the CAPTCHA will not be detected.

    Parameters
    ---------
    structure : dict<StructuralElement, ResourceIdentifier>
        The platform structure of the platform to which all the web pages belong that need to be parsed.

    Attributes
    ---------
    __structure : dict of <StructuralElement, ResourceIdentifier> pairs
        The platform structure of the platform to which all the web pages belong that need to be parsed.
    captcha_on_page : bool
        Whether a CAPTCHA is on the web page or not.
    captcha_full_page : bool
        Whether the displayed webpage is a CAPTCHA page.
    __captcha_type : CaptchaType
        Which type of CAPTCHA has been encountered on the web page. None if no CAPTCHA is on the page.

    Raises
    ------
    ValueError
        If `structure` is not a dictionary of <StructuralElement, ResourceIdentifier> pairs.
    """

    def __init__(self, structure):
        verify_struct(structure)

        self.__structure = structure
        self.captcha_on_page = False
        self.captcha_full_page = False
        self.__captcha_type = None

    def parse_page(self, page: str):
        """Parse the supplied web page to check for CAPTCHAs

        During parsing, all the attributes are set (if their preconditions are met). Returns True when finished, returns
        False if it could not finish.

        Parameters
        ---------
        page : str
            The web page to parse.

        Returns
        -------
        bool
            True if parsing the page is completed, False if the parsing did not complete.
        """
        # Reset values so they are never left over from previous pages.
        self.__captcha_type = None
        self.captcha_on_page = False
        self.captcha_full_page = False

        # A CAPTCHA is on page if using Google's reCAPTCHA script
        if "recaptcha" in page.lower():
            if "grecaptcha.enterprise.execute" in page.lower() or (("v2" in page.lower() or "v3" in page.lower()) and
                                                                   "invisible" in page.lower()):
                self.captcha_on_page = True
                self.__captcha_type = CaptchaType.INVISIBLE_RECAPTCHA
            elif "<script src=\"https://www.google.com/recaptcha/enterprise.js\" async defer></script>" in page.lower()\
                    or "grecaptcha.enterprise.render" in page.lower() or "grecaptcha.render" in page.lower():
                self.captcha_on_page = True
                self.__captcha_type = CaptchaType.NOCAPTCHA_RECAPTCHA
            elif "I'm not a robot" in page.lower() and "Privacy" in page and "Terms" in page:
                self.captcha_on_page = True
                self.__captcha_type = CaptchaType.RECAPTCHA

        # If page has an image php with a hash value and the input field has the same value, this is a Word Problem
        if "<img" in page:
            # Find all image tags
            split_image = page.split("<img")
            for tag in split_image[1:]:
                # Split such that we only have the tag
                captcha_line = tag.split(">")[0]
                # If it is a php image, it is most likely a CAPTCHA
                if "captcha.php" in captcha_line.casefold() or \
                        "captcha.png" in captcha_line.casefold() or "captcha.gif" in captcha_line.casefold() or \
                        "captcha.jpg" in captcha_line.casefold():
                    self.captcha_on_page = True
                    self.__captcha_type = CaptchaType.WORD_PROBLEM

        # If an input field is hidden from view, this is a Honeypot CAPTCHA
        if "<input" in page:
            hidden_inputs = detect_honeypot(page)

            if hidden_inputs:
                self.captcha_on_page = True
                self.__captcha_type = CaptchaType.HONEYPOT

        if "Why do I have to complete a CAPTCHA?" in page or \
                "needs to review the security of your connection before proceeding" in page or \
                "Checking if the site connection is secure" in page:
            # This is a cloudflare CAPTCHA
            self.captcha_on_page = True
            self.__captcha_type = CaptchaType.HCAPTCHA
            self.captcha_full_page = True

        if "Расчетное время ожидания составляет" in page or "Докажи, что ты не бот и не чайка." in page:
            # This is a waiting page from Dread
            self.captcha_on_page = True
            self.__captcha_type = CaptchaType.DREAD
            self.captcha_full_page = True

        if "Вашего кодового слова форму ниже" in page:
            self.captcha_on_page = True
            self.__captcha_type = CaptchaType.CUSTOM_SECOND_FACTOR
            self.captcha_full_page = True

        if "Using this page, we will be able to determine that you are not the robot." in page or \
            "DDoS protection by DDoS-GUARD" in page:
            self.captcha_on_page = True
            self.__captcha_type = CaptchaType.DDOS_GUARD
            self.captcha_full_page = True


    @property
    def captcha_type(self) -> t.Union[CaptchaType, None]:
        """Gets the CAPTCHA type on the last parsed web page.

        Returns
        -------
        CaptchaType
            Which type of CAPTCHA has been encountered on the web page. None if no CAPTCHA is on the page.
        """
        if self.__captcha_type is None:
            return self.__captcha_type
        elif not isinstance(self.__captcha_type, CaptchaType):
            raise ValueError("The CAPTCHA type is not a CaptchaType")
        else:
            return self.__captcha_type

    @property
    def structure(self) -> t.Union[t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]], None]:
        """Get the structure that InterpreterData uses.

        Returns
        ------
        dict<PageType, dict<StructuralElement, ResourceIdentifier>> | None
            The structure used by InterpreterData, None if improperly initialised."""
        return self.__structure

    @structure.setter
    def structure(self, struct: t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]]):
        """Set the structure that InterpreterData uses.

        Parameters
        ------
        struct : dict<PageType, dict<StructuralElement, ResourceIdentifier>>
            The structure to be used by InterpreterData."""
        verify_struct(struct)
        self.__structure = struct
