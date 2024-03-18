"""Captcha Solver class for the Crawler module"""
import threading

from utils import Logger
from enums import CaptchaType


class CaptchaSolver:
    """The captcha_solver class solves a supported Captcha type when encountered during crawling.

    Attributes
    ---------
    solved : Threading.Condition
        lock to communicate the crawler that a CAPTCHA has been encountered and the crawler execution has to stop.

    """
    def __init__(self, solved: threading.Condition):
        self.__solved_condition = solved

    def solve_captcha(self, captcha_type):
        """This function suspends the execution of the crawler. The solved condition is taken and the CLI will print
        a message asking to solve the CAPTCHA; once this interaction occurred, the lock is released.

        Parameters
        ----------
        captcha_type : CaptchaType
            The type of the Captcha encountered
        """

        if captcha_type != CaptchaType.HONEYPOT:
            Logger.log("interpreter", "Captcha detected of type: {}. Please solve the Captcha visible in the Tor "
                                      "Browser. Type 'solved' in the terminal to continue once the CAPTCHA is solved "
                                      "and then press enter twice."
                                      .format(captcha_type))
            with self.__solved_condition:
                self.__solved_condition.wait()
