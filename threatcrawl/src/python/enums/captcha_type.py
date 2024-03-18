"""Class to house the enum for the CAPTCHA type"""
from enum import Enum


class CaptchaType(Enum):
    """Class to house the enum for the CAPTCHA type.

    CAPTCHAs come in a wide variety and need to be indicated in order for the crawler to decide whether it can try to
    solve the CAPTCHA itself or ask the user.

    Notes
    -----
    All the different CAPTCHA types can be found in [1]_.

    References
    ----------
    [1] Rosie, "11 most popular types of captcha." [Online]. Available at: https://passwordprotectwp.com/types-captcha/


    SIMPLE_MATH_PROBLEM
        CAPTCHA of the Simple Math Problem type.
    WORD_PROBLEM
        CAPTCHA of the Word Problem type.
    TIME_BASED
        Time based CAPTCHA type.
    HONEYPOT
        CAPTCHA of the Honeypot type.
    PICTURE_IDENTIFICATION
        CAPTCHA of the Picture Identification type.
    RECAPTCHA
        CAPTCHA of the ReCAPTCHA type.
    NOCAPTCHA_RECAPTCHA
        CAPTCHA of the NoCAPTCHA ReCAPTCHA type.
    INVISIBLE_RECAPTCHA
        CAPTCHA of the Invisible ReCAPTCHA type.
    SWEET_CAPTCHA
        CAPTCHA of the Sweet CAPTCHA type.
    BIOMETRICS
        Not really a CAPTCHA but a type of bot testing nonetheless.
    HCAPTCHA
        CloudFlare CAPTCHA.
    CUSTOM_SECOND_FACTOR
        Not really a CAPTCHA, requires to provide two chars of a secret word.
    """
    SIMPLE_MATH_PROBLEM = 1
    WORD_PROBLEM = 2
    TIME_BASED = 3
    HONEYPOT = 4
    PICTURE_IDENTIFICATION = 5
    RECAPTCHA = 6
    NOCAPTCHA_RECAPTCHA = 7
    INVISIBLE_RECAPTCHA = 8
    SWEET_CAPTCHA = 9
    BIOMETRICS = 10
    HCAPTCHA = 11
    CUSTOM_SECOND_FACTOR = 12
    DREAD = 13
    DDOS_GUARD = 14